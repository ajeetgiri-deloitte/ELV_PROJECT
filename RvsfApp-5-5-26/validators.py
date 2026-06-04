# validators.py
import os
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_pdf_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext != '.pdf':
        raise ValidationError(_('Unsupported file extension – only .pdf allowed.'))

def validate_file_size(value):
    limit = 2 * 1024 * 1024  # 2 MB
    if value.size > limit:
        raise ValidationError(_('File too large – must be under 2 MB.'))
