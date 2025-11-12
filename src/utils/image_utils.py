import io
import os
import base64
from typing import Optional, Tuple

from PIL import Image


def compress_image_to_jpeg(
    image_path: str,
    max_side_px: int = 512,
    target_kb: int = 200,
) -> bytes:
    """Load an image, downscale to fit within max_side_px, and JPEG-compress.

    Returns JPEG bytes. Best-effort to keep size under target_kb while
    preserving reasonable quality.
    """
    image = Image.open(image_path).convert("RGB")

    # Resize keeping aspect ratio
    width, height = image.size
    scale = min(1.0, float(max_side_px) / float(max(width, height)))
    if scale < 1.0:
        new_size = (int(width * scale), int(height * scale))
        image = image.resize(new_size, Image.Resampling.LANCZOS)

    # Binary search quality to fit under target_kb
    low, high = 40, 90
    best = None
    while low <= high:
        mid = (low + high) // 2
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=mid, optimize=True)
        data = buf.getvalue()
        kb = len(data) // 1024
        if kb <= target_kb:
            best = data
            low = mid + 1
        else:
            high = mid - 1

    if best is None:
        # Fallback with moderate quality
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=70, optimize=True)
        best = buf.getvalue()

    return best


def image_bytes_to_base64(data: bytes) -> str:
    """Encode image bytes to base64 string (utf-8)."""
    return base64.b64encode(data).decode("utf-8")


def base64_to_image_bytes(b64: str) -> bytes:
    """Decode base64 string to raw bytes."""
    return base64.b64decode(b64.encode("utf-8"))


def is_base64_string(value: str) -> bool:
    if not value or not isinstance(value, str):
        return False
    try:
        base64.b64decode(value.encode("utf-8"))
        return True
    except Exception:
        return False


def base64_to_tk_photo(b64: str):
    """Return a Tk-compatible PhotoImage from base64 image string.

    Imported lazily to avoid tkinter dependency here.
    """
    from PIL import ImageTk  # local import
    data = base64_to_image_bytes(b64)
    img = Image.open(io.BytesIO(data))
    return ImageTk.PhotoImage(img)









