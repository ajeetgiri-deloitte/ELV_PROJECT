from PIL import Image
import piexif
from io import BytesIO
from django.core.files.base import ContentFile
from PyPDF2 import PdfReader, PdfWriter
from openpyxl import load_workbook

# ---------------- Images ----------------
def strip_exif(file):
    try:
        image = Image.open(file)
        if "exif" in image.info:
            data = list(image.getdata())
            clean_image = Image.new(image.mode, image.size)
            clean_image.putdata(data)
            output = BytesIO()
            clean_image.save(output, format=image.format)
            return ContentFile(output.getvalue(), name=file.name)
    except Exception:
        return file
    return file

# ---------------- PDF ----------------
def clean_pdf(file):
    try:
        reader = PdfReader(file)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.add_metadata({})  # remove all metadata
        output = BytesIO()
        writer.write(output)
        return ContentFile(output.getvalue(), name=file.name)
    except Exception:
        return file

# ---------------- Excel ----------------
def clean_excel(file):
    try:
        wb = load_workbook(file)
        wb.properties = wb.properties.__class__()  # reset metadata
        output = BytesIO()
        wb.save(output)
        return ContentFile(output.getvalue(), name=file.name)
    except Exception:
        return file

# ---------------- General Cleaner ----------------
def sanitize_file(file):
    if file.name.lower().endswith(('.jpg', '.jpeg', '.png')):
        return strip_exif(file)
    elif file.name.lower().endswith('.pdf'):
        return clean_pdf(file)
    elif file.name.lower().endswith(('.xlsx', '.xls')):
        return clean_excel(file)
    return file
