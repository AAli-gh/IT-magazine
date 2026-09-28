"""Cover thumbnails and upload optimization with Pillow."""

import io
import logging
import os

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

COVER_WIDTHS = (480, 960, 1440)
MAX_UPLOAD_WIDTH = 1920
WEBP_QUALITY = 80


def _open(field):
    field.open("rb")
    field.seek(0)
    image = Image.open(field)
    image = ImageOps.exif_transpose(image)  # honour camera rotation, drops EXIF on save
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA" if "transparency" in image.info else "RGB")
    return image


def build_cover_variants(field):
    """Create WebP variants of a cover image; returns ``{width: url}``."""
    try:
        image = _open(field)
    except Exception:  # corrupt or unsupported file: keep the original only
        logger.exception("Could not open cover %s", field.name)
        return {}
    base = os.path.splitext(os.path.basename(field.name))[0]
    variants = {}
    for width in COVER_WIDTHS:
        if image.width < width and variants:
            break
        target = min(width, image.width)
        height = round(image.height * target / image.width)
        resized = image.resize((target, height), Image.LANCZOS)
        buffer = io.BytesIO()
        resized.save(buffer, "WEBP", quality=WEBP_QUALITY, method=4)
        path = f"covers/variants/{base}-{target}.webp"
        if default_storage.exists(path):
            default_storage.delete(path)
        saved = default_storage.save(path, ContentFile(buffer.getvalue()))
        variants[str(target)] = default_storage.url(saved)
    return variants


def optimize_upload(field):
    """Downscale very large uploads and strip metadata before first save."""
    try:
        image = _open(field)
    except Exception:
        return
    if image.width <= MAX_UPLOAD_WIDTH:
        return
    height = round(image.height * MAX_UPLOAD_WIDTH / image.width)
    image = image.resize((MAX_UPLOAD_WIDTH, height), Image.LANCZOS)
    buffer = io.BytesIO()
    fmt = "PNG" if image.mode == "RGBA" else "JPEG"
    image.save(buffer, fmt, quality=85, optimize=True)
    name = os.path.splitext(os.path.basename(field.name))[0] + (".png" if fmt == "PNG" else ".jpg")
    field.save(name, ContentFile(buffer.getvalue()), save=False)
