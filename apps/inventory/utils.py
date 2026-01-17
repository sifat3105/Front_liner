import io
import barcode
import qrcode
from barcode.writer import ImageWriter
from django.core.files.base import ContentFile


def generate_barcode(sku):
    buffer = io.BytesIO()
    code128 = barcode.get("code128", sku, writer=ImageWriter())
    code128.write(buffer)
    return ContentFile(buffer.getvalue(), name=f"{sku}.png")


def generate_qr(sku):
    buffer = io.BytesIO()
    img = qrcode.make(sku)
    img.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name=f"{sku}.png")