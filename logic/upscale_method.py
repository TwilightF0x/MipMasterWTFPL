from PIL import Image

from .filter_wrap import smart_downscale


def upscale(pil_image: Image.Image, new_size, alpha=0.5) -> Image.Image:
    return smart_downscale(pil_image, new_size)
