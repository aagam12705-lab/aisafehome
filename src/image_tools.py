"""Safe, consistent image preparation for upload and recheck flows."""

import io
from typing import Any

from PIL import Image, ImageOps

from src.constants import MAX_FILE_SIZE_MB


def validate_uploaded_photo(uploaded_file: Any) -> tuple[bool, str]:
    if uploaded_file is None:
        return False, "No file uploaded."
    if uploaded_file.size / (1024 * 1024) > MAX_FILE_SIZE_MB:
        return False, f"File is too large. Maximum size is {MAX_FILE_SIZE_MB} MB."
    return True, ""


def load_oriented_image(uploaded_file: Any) -> Image.Image:
    """Open a camera image after applying its EXIF orientation."""
    uploaded_file.seek(0)
    image = ImageOps.exif_transpose(Image.open(uploaded_file))
    image.load()
    return image.copy()


def oriented_image_file(image: Image.Image) -> io.BytesIO:
    """Use the same upright JPEG pixels for preview and AI analysis."""
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=95)
    buffer.seek(0)
    buffer.name = "upright_room_photo.jpg"
    buffer.type = "image/jpeg"
    return buffer
