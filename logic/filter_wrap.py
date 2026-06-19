from PIL import Image, ImageFilter
import numpy as np
from numba import njit, prange
import cv2


def exact_a_filter(pil_img: Image.Image, filter_func, *args, **kwargs) -> Image.Image:

    arr = np.array(pil_img)

    if arr.ndim == 3 and arr.shape[2] == 4:
        rgb = Image.fromarray(arr[..., :3], mode="RGB")
        alpha = arr[..., 3]

        filtered_rgb_img = filter_func(rgb, *args, **kwargs)
        if type(filtered_rgb_img) == str:
            return filtered_rgb_img
        filtered_rgb = np.array(filtered_rgb_img)

        if filtered_rgb.shape[:2] != alpha.shape[:2]:
            alpha_img = Image.fromarray(alpha, mode="L")
            alpha_resized = cv2.resize(np.array(alpha_img).astype(np.float32) / 255.0,
                                       filtered_rgb_img.size,  # (W, H)
                                       interpolation=cv2.INTER_CUBIC)
            alpha_resized = np.clip(alpha_resized * 255.0, 0, 255).astype(np.uint8)
        else:
            alpha_resized = alpha

        rgba = np.dstack((filtered_rgb, alpha_resized))
        return Image.fromarray(rgba, mode="RGBA")


def soft_a_filter(pil_alpha: Image.Image, size: tuple) -> np.ndarray:
    arr = np.array(pil_alpha).astype(np.float32) / 255.0
    resized = cv2.resize(arr, size, interpolation=cv2.INTER_AREA)
    return (resized * 255.0).astype(np.uint8)

def safe_filter(options_set, pil_img: Image.Image, filter_func, *args, **kwargs) -> Image.Image:
    """
    Безопасная обёртка для фильтров, чтобы правильно обрабатывать RGBA и RGB изображения.
    filter_func — функция, которая принимает и возвращает PIL.Image.Image (работающая с RGB).
    """
    options_set = options_set.get("alpha_filter_type")
    arr = np.array(pil_img)
    if arr.ndim == 3 and arr.shape[2] == 4:
        if options_set == "Exact":
            return(exact_a_filter(pil_img, filter_func, *args, **kwargs))
            
        rgb = Image.fromarray(arr[..., :3])
        alpha = Image.fromarray(arr[..., 3])

        filtered_rgb = filter_func(rgb, *args, **kwargs)

        filtered_arr = np.array(filtered_rgb)
        alpha_arr = np.array(alpha)

        if filtered_arr.shape[:2] != alpha_arr.shape[:2]:
            alpha_arr = soft_a_filter(alpha, filtered_rgb.size)

        rgba = np.dstack((filtered_arr, alpha_arr))
        return Image.fromarray(rgba, mode="RGBA")

    else:
        return filter_func(pil_img, *args, **kwargs)


def smart_downscale_normal(pil_image, new_size):
        resized = pil_image.resize(new_size, resample=Image.LANCZOS)
        sharpened = resized.filter(ImageFilter.UnsharpMask(radius=1, percent=100, threshold=0))
        return sharpened


@njit(parallel=True)
def normalize_soft_numba(xyz, original_z, mix_factor):
    h, w, _ = xyz.shape
    output = np.zeros_like(xyz)
    
    for y in prange(h):
        for x in range(w):
            vec = xyz[y, x]
            norm = np.linalg.norm(vec)
            if norm == 0:
                norm = 1.0
            vec = vec / norm

            orig_z = original_z[y, x]
            mixed_z = mix_factor * vec[2] + (1.0 - mix_factor) * orig_z

            final_vec = np.array([vec[0], vec[1], mixed_z])
            final_norm = np.linalg.norm(final_vec)
            if final_norm == 0:
                final_norm = 1.0
            final_vec /= final_norm
            output[y, x] = final_vec
    return output

def normalize_normal_map_soft(pil_image, mix_factor=0.5):
    """Мягкая нормализация нормалей с сохранением Z-компоненты"""
    arr = np.array(pil_image).astype(np.float32)

    if arr.shape[2] < 3:
        raise ValueError("Normal map must have at least 3 channels")

    rgb = arr[..., :3] / 255.0 * 2.0 - 1.0
    z_original = arr[..., 2] / 255.0 * 2.0 - 1.0

    normalized = normalize_soft_numba(rgb, z_original, mix_factor)

    result_rgb = ((normalized + 1.0) * 0.5 * 255.0).clip(0, 255).astype(np.uint8)

    if arr.shape[2] == 4:
        alpha = arr[..., 3:4].astype(np.uint8)
        final = np.concatenate((result_rgb, alpha), axis=2)
        return Image.fromarray(final, "RGBA")
    return Image.fromarray(result_rgb, "RGB")


def boost_z_channel(pil_image, factor=1.2):
    arr = np.array(pil_image).astype(np.float32)
    arr[..., 2] = np.clip((arr[..., 2] - 128) * factor + 128, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), pil_image.mode)


def smart_downscale(pil_image, new_size):
    resized = pil_image.resize(new_size, resample=Image.LANCZOS)
    sharpened = resized.filter(ImageFilter.UnsharpMask(radius=1, percent=100, threshold=0))
    return sharpened

def linear_dodge_channel(channel, intensity):
    """Смешивает канал с белым цветом (Linear Dodge/Add)."""
    white = Image.new("L", channel.size, 255)

    if intensity <= 0:
        return channel
    if intensity >= 1:
        return Image.new("L", channel.size, 255)

    ch_np = np.array(channel).astype(np.float32)

    result_np = ch_np + (255 - ch_np) * intensity
    result_np = np.clip(result_np, 0, 255).astype(np.uint8)

    result = Image.fromarray(result_np, mode="L")
    return result