import os
import re
import uuid
import magic
import unicodedata
import urllib.parse
from django.core.exceptions import ValidationError

# -------------------------
# Configuration
# -------------------------
ALLOWED_EXTS = {'.pdf'}
ALLOWED_MIMES = {
    'application/pdf',
    'application/x-pdf',
}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
FILENAME_MAX_LENGTH = 255

# Suspicious tokens that indicate embedded/active PDF content
PDF_SUSPICIOUS_TOKENS = [
    b'/JavaScript',
    b'/JS(',       
    b'/OpenAction',
    b'/AA<<',
    b'/RichMedia'
]

# Allowed filename characters (strict ASCII)
FILENAME_REGEX = re.compile(r'^[A-Za-z0-9._-]+$')

# Detect patterns that indicate traversal or hidden extensions
TRAILING_EXT_SLASH_PATTERN = re.compile(r'\.[A-Za-z0-9]{1,6}[\\/]', flags=re.IGNORECASE)
DOUBLE_EXT_PATTERN = re.compile(r'\.[A-Za-z0-9]{1,6}\.[A-Za-z0-9]{1,6}$', flags=re.IGNORECASE)

# Detect encoded slashes like "%2f" or "%5c"
ENCODED_SLASH_PATTERNS = re.compile(r'%2f|%5c', flags=re.IGNORECASE)


# -------------------------
# Helper Functions
# -------------------------
def _has_control_chars(s: str) -> bool:
    """Detects control characters (C0/C1)."""
    return any(ord(ch) < 32 or (127 <= ord(ch) < 160) for ch in s)


def _decode_all(raw: str) -> str:
    """Repeatedly decode percent-encodings like %252f → %2f → /"""
    prev = None
    cur = raw
    try:
        for _ in range(3):
            prev = cur
            cur = urllib.parse.unquote_plus(cur)
            if cur == prev:
                break
    except Exception:
        cur = raw
    return cur


def _normalize_and_sanitize_filename(raw_name: str) -> str:
    """Normalize Unicode, reject encoded slashes/nulls, and return basename."""
    if raw_name is None:
        return ''

    decoded = _decode_all(raw_name)

    # Reject null bytes
    if '\x00' in decoded or '%00' in decoded.lower():
        raise ValidationError("Invalid filename (null byte detected).")

    # Reject literal or encoded slashes/backslashes
    if '/' in decoded or '\\' in decoded:
        raise ValidationError("Invalid filename (contains path separators).")
    if ENCODED_SLASH_PATTERNS.search(raw_name) or ENCODED_SLASH_PATTERNS.search(decoded):
        raise ValidationError("Invalid filename encoding (encoded slashes/backslashes detected).")

    normalized = unicodedata.normalize('NFKC', decoded).strip()

    if normalized.endswith(('/', '\\')):
        raise ValidationError("Invalid filename ending with a slash or backslash.")

    basename = os.path.basename(normalized)
    basename = re.sub(r'\s+', ' ', basename).strip()

    if not basename:
        raise ValidationError("Invalid filename (empty after normalization).")

    return basename


def _read_head_and_tail(file_obj, head=8192, tail=8192) -> bytes:
    """
    Read first and last chunks of file to detect spoofing/malicious payloads.
    Many bypass payloads hide in tail of PDFs.
    """
    file_obj.seek(0, os.SEEK_END)
    size = file_obj.tell()
    file_obj.seek(0)

    data = file_obj.read(head)
    if size > tail:
        # Read last part for hidden payload detection
        file_obj.seek(-tail, os.SEEK_END)
        data += file_obj.read(tail)
    file_obj.seek(0)
    return data


# -------------------------
# Main Validation Function
# -------------------------
def validate_uploaded_file(file):
    """
    Securely validate uploaded files to prevent:
    - Path traversal or encoded path bypasses
    - Double extensions or suspicious extensions
    - Hidden files, control chars, overly long names
    - MIME spoofing
    - Embedded JS/attachments in PDFs
    - Partial-content bypass (checks both start and end)
    """
    raw_filename = getattr(file, 'name', '') or ''

    # 🔒 Filenames cannot contain slashes or encoded path separators
    if '/' in raw_filename or '\\' in raw_filename:
        raise ValidationError("Invalid filename (contains path separators).")
    if ENCODED_SLASH_PATTERNS.search(raw_filename):
        raise ValidationError("Invalid filename encoding (encoded slashes/backslashes detected).")
    if raw_filename.endswith(('/', '\\')):
        raise ValidationError("Invalid filename ending with a slash or backslash.")

    # Normalize + sanitize
    filename = _normalize_and_sanitize_filename(raw_filename)

    # Basic validations
    if not filename:
        raise ValidationError("Empty or invalid filename.")
    if filename.startswith('.'):
        raise ValidationError("Hidden files are not allowed.")
    if _has_control_chars(filename):
        raise ValidationError("Filename contains control characters.")
    if filename.endswith('.'):
        raise ValidationError("Filename cannot end with a dot.")
    if len(filename) > FILENAME_MAX_LENGTH:
        raise ValidationError(f"Filename too long (max {FILENAME_MAX_LENGTH} characters).")

    # Pattern-based rejections
    if TRAILING_EXT_SLASH_PATTERN.search(filename):
        raise ValidationError("Suspicious filename pattern detected (extension followed by slash/backslash).")
    if DOUBLE_EXT_PATTERN.search(filename):
        raise ValidationError("Double extension detected in filename.")
    if filename.count('.') != 1:
        raise ValidationError("Filename must contain exactly one extension (single dot).")

    # Extension check
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    if ext not in ALLOWED_EXTS:
        raise ValidationError(f"Unsupported file extension '{ext}'.")

    # Strict character policy
    if not FILENAME_REGEX.match(filename):
        raise ValidationError("Filename contains invalid characters. Use only letters, numbers, dot, underscore, and hyphen.")

    # File size validation
    try:
        size = getattr(file, 'size', None)
        if size is None:
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
    except Exception:
        raise ValidationError("Unable to determine file size.")

    if size == 0:
        raise ValidationError("File is empty.")
    if size > MAX_FILE_SIZE:
        raise ValidationError(f"File too large (max {MAX_FILE_SIZE} bytes).")

    # MIME detection from both head & tail (prevents body spoofing)
    try:
        chunk = _read_head_and_tail(file)
        mime = magic.from_buffer(chunk, mime=True)
    except Exception as e:
        raise ValidationError(f"Unable to verify file type: {str(e)}")

    if mime not in ALLOWED_MIMES:
        raise ValidationError(f"Invalid file type: {mime}")
    
    # Extra deep inspection to block disguised scripts or executables
    dangerous_signatures = [
        b'<?php', b'<?=',
        b'<%@', b'runat="server"', b'asp.net',
        b'<script', b'<html', b'<body', b'<iframe',
        b'<!doctype', b'<jsp:', b'<?=', b'#!/',
        b'class ', b'using system', b'@page',
    ]

    if any(sig in chunk.lower() for sig in dangerous_signatures):
        raise ValidationError("File contains embedded code or script tags — only clean PDFs are allowed.")

    # PDF header check
    lower_data = chunk.lower()
    if not lower_data.lstrip().startswith(b'%pdf'):
        raise ValidationError("File content does not start with a valid PDF header.")

    # 🔍 Deep content-body inspection (both header and tail)
    # This prevents bypass via partial payloads or appended scripts
    # Reads entire file in manageable chunks up to limit
    file.seek(0)
    read_bytes = 0
    while True:
        part = file.read(8192)
        if not part:
            break
        read_bytes += len(part)
        lower_part = part.lower()
        for token in PDF_SUSPICIOUS_TOKENS:
            if token.lower() in lower_part:
                raise ValidationError("PDF contains suspicious embedded content (JavaScript or attachments).")
        if read_bytes > MAX_FILE_SIZE:
            break
    file.seek(0)

    return file


# -------------------------
# Secure Filename Generator
# -------------------------
def secure_filename(filename: str) -> str:
    """Generate a UUID-prefixed secure filename with .pdf enforced."""
    filename = _normalize_and_sanitize_filename(filename)
    if not filename:
        raise ValueError("Invalid filename for securing.")

    base = os.path.basename(filename)
    name, ext = os.path.splitext(base)
    ext = ext.lower()
    if ext not in ALLOWED_EXTS:
        ext = '.pdf'

    safe_base = re.sub(r'[^A-Za-z0-9._-]', '_', name)
    uid = uuid.uuid4().hex
    return f"{uid}_{safe_base}{ext}"


# -------------------------
# Upload Wrappers
# -------------------------
def validate_uploaded_file_force_pdf(file):
    """Force validation specifically for PDFs."""
    return validate_uploaded_file(file)


def secure_save_pdf(file, upload_dir):
    """Save a validated PDF with a unique, sanitized name."""
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)

    safe_name = secure_filename(file.name)
    full_path = os.path.join(upload_dir, safe_name)

    # Write safely
    with open(full_path, 'wb+') as dest:
        for chunk in file.chunks():
            dest.write(chunk)

    os.chmod(full_path, 0o644)
    return safe_name
