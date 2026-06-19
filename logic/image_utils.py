import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError
from PySide6.QtGui import QPixmap, QImage


def normalize_pil_image(img: Image.Image) -> Image.Image:
    """Привести PIL-изображение к 8-bit RGB/RGBA, загрузив пиксели в память."""
    img.load()
    if getattr(img, "n_frames", 1) > 1:
        img.seek(0)
    if img.mode in ("RGB", "RGBA"):
        return img.copy()
    if img.mode in ("L", "P", "LA", "PA"):
        return img.convert("RGBA")
    if img.mode == "CMYK":
        return img.convert("RGB")
    return img.convert("RGBA")


def _array_to_pil(arr: np.ndarray) -> Image.Image:
    arr = np.asarray(arr)
    if arr.dtype in (np.float32, np.float64):
        max_val = float(np.nanmax(arr)) if arr.size else 1.0
        arr = (arr * 255.0).clip(0, 255) if max_val <= 1.0 else arr.clip(0, 255)
        arr = arr.astype(np.uint8)
    elif arr.dtype == np.uint16:
        arr = (arr / 257).astype(np.uint8)
    elif arr.dtype != np.uint8:
        arr = arr.astype(np.uint8)

    if arr.ndim == 2:
        return Image.fromarray(arr, "L")
    if arr.ndim == 3:
        ch = arr.shape[2]
        if ch == 4:
            arr = cv2.cvtColor(arr, cv2.COLOR_BGRA2RGBA)
            return Image.fromarray(arr, "RGBA")
        if ch == 3:
            arr = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
            return Image.fromarray(arr, "RGB")
    raise ValueError(f"Unsupported array shape for image: {getattr(arr, 'shape', None)}")


def _load_tiff_fallback(path: str) -> Image.Image:
    arr = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if arr is None:
        raise ValueError(f"Could not read TIFF file: {path}")
    return _array_to_pil(arr)


def load_image_from_file(path: str) -> Image.Image:
    try:
        with Image.open(path) as f:
            return normalize_pil_image(f)
    except UnidentifiedImageError:
        if path.lower().endswith((".tif", ".tiff")):
            return normalize_pil_image(_load_tiff_fallback(path))
        raise


def pil_to_pixmap(pil_image):
    pil_image = pil_image.convert("RGBA")
    data = pil_image.tobytes("raw", "RGBA")
    qimage = QImage(
        data,
        pil_image.width,
        pil_image.height,
        QImage.Format.Format_RGBA8888,
    )
    if qimage.isNull():
        raise ValueError("Failed to create QImage from PIL image")
    return QPixmap.fromImage(qimage)


def apply_channel_preview(pil_image, show_r=True, show_g=True, show_b=True, show_a=True):
    """Return preview image with selected channels only."""
    src = pil_image.convert("RGBA")
    r, g, b, a = src.split()
    visible_rgb = [show_r, show_g, show_b]

    if visible_rgb.count(True) == 1:
        channel = r if show_r else g if show_g else b
        alpha = a if show_a else a.point(lambda _x: 0)
        return Image.merge("RGBA", (channel, channel, channel, alpha))

    if not show_r:
        r = r.point(lambda _x: 0)
    if not show_g:
        g = g.point(lambda _x: 0)
    if not show_b:
        b = b.point(lambda _x: 0)
    if not show_a:
        a = a.point(lambda _x: 0)

    return Image.merge("RGBA", (r, g, b, a))
