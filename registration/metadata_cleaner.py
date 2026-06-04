import io, subprocess, tempfile, zipfile, magic, logging
from django.core.files.base import ContentFile
from PIL import Image
import pikepdf

logger = logging.getLogger(__name__)

def get_mime_type(file):
    """Detect mime type of uploaded file."""
    file.seek(0)
    mime = magic.from_buffer(file.read(2048), mime=True)
    file.seek(0)
    return mime

def clean_image(file):
    """Strip EXIF from image safely."""
    try:
        image = Image.open(file)
        data = list(image.getdata())
        cleaned = Image.new(image.mode, image.size)
        cleaned.putdata(data)
        buffer = io.BytesIO()
        cleaned.save(buffer, format=image.format)
        return ContentFile(buffer.getvalue())
    except Exception as e:
        logger.warning(f"Image cleaning failed: {e}")
        file.seek(0)
        return ContentFile(file.read())

def clean_pdf(file):
    """Remove metadata from PDF."""
    try:
        buffer = io.BytesIO()
        with pikepdf.open(file) as pdf:
            clean = pikepdf.Pdf.new()
            for page in pdf.pages:
                clean.pages.append(page)
            clean.save(buffer)
        return ContentFile(buffer.getvalue())
    except Exception as e:
        logger.warning(f"PDF cleaning failed: {e}")
        file.seek(0)
        return ContentFile(file.read())

def clean_office(file):
    """Remove metadata from DOCX/XLSX/PPTX."""
    try:
        memfile = io.BytesIO()
        with zipfile.ZipFile(file, 'r') as zin, zipfile.ZipFile(memfile, 'w') as zout:
            for item in zin.infolist():
                if not item.filename.startswith('docProps/'):
                    zout.writestr(item, zin.read(item.filename))
        memfile.seek(0)
        return ContentFile(memfile.read())
    except Exception as e:
        logger.warning(f"Office file cleaning failed: {e}")
        file.seek(0)
        return ContentFile(file.read())

def clean_media(file):
    """Remove metadata from video/audio files."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp_in, tempfile.NamedTemporaryFile(suffix=".mp4") as tmp_out:
            tmp_in.write(file.read())
            tmp_in.flush()
            subprocess.run(
                ["ffmpeg", "-y", "-i", tmp_in.name, "-map_metadata", "-1", "-c", "copy", tmp_out.name],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            tmp_out.seek(0)
            return ContentFile(tmp_out.read())
    except Exception as e:
        logger.warning(f"Media cleaning failed: {e}")
        file.seek(0)
        return ContentFile(file.read())

def sanitize_file(file):
    """Main universal entrypoint for cleaning uploaded files."""
    mime = get_mime_type(file)

    if mime.startswith("image/"):
        return clean_image(file)
    elif mime == "application/pdf":
        return clean_pdf(file)
    elif mime in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ]:
        return clean_office(file)
    elif mime.startswith("video/") or mime.startswith("audio/"):
        return clean_media(file)
    else:
        # Fallback: use exiftool to wipe all metadata
        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(file.read())
                tmp.flush()
                subprocess.run(["exiftool", "-all=", "-overwrite_original", tmp.name],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                tmp.seek(0)
                return ContentFile(tmp.read())
        except Exception as e:
            logger.warning(f"Generic metadata strip failed: {e}")
            file.seek(0)
            return ContentFile(file.read())
