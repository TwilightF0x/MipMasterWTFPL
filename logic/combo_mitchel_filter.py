import numpy as np
from PIL import Image
import cv2
from numba import njit
from .mitchel_netravali_filter import mitchell_netravali


# === Фильтры ===
@njit
def box_filter(x):
    return 1.0 if abs(x) <= 0.5 else 0.0

@njit
def triangle_filter(x):
    x = abs(x)
    return max(1.0 - x, 0.0)

@njit
def adaptive_kernel(x, importance):
    if importance > 0.7:
        return mitchell_netravali(x)
    elif importance > 0.3:
        return triangle_filter(x)
    else:
        return box_filter(x)



def compute_importance_map(img: np.ndarray, use_color: bool = False) -> np.ndarray:
    if use_color:
        lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        gray = l.astype(np.float32)
    else:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32)

    gray = np.clip(gray, 1e-3, 255.0)

    ### 1. Log-Luminance Gradient
    log_gray = np.log(gray)
    sobel_x = cv2.Sobel(log_gray, cv2.CV_32F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(log_gray, cv2.CV_32F, 0, 1, ksize=3)
    log_grad = np.sqrt(sobel_x**2 + sobel_y**2)

    ### 2. Laplacian
    lap = cv2.Laplacian(gray, cv2.CV_32F, ksize=3)
    lap_mag = np.abs(lap)

    ### 3. Edge-Preserving Difference
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    epf = cv2.edgePreservingFilter(img_bgr, flags=1, sigma_s=64, sigma_r=0.2)
    epf = cv2.cvtColor(epf, cv2.COLOR_BGR2GRAY).astype(np.float32)
    epf_diff = np.abs(gray - epf)

    ### 4. Layers combination
    combined = (
        0.4 * log_grad +
        0.3 * lap_mag +
        0.3 * epf_diff
    )

    ### 5. Dynamic Range Normalization
    mean = np.mean(combined)
    std = np.std(combined)
    importance = (combined - mean) / (std + 1e-6)

    importance = np.clip(importance, 0, 1)
    importance = cv2.bilateralFilter(importance, d=5, sigmaColor=0.2, sigmaSpace=3)

    return importance


def linearize(img):
    return np.power(img / 255.0, 2.2)

def delinearize(img):
    img = np.maximum(img, 0.0)
    return np.clip(np.power(img, 1/2.2) * 255, 0, 255).astype(np.uint8)


@njit
def apply_adaptive_resample(img_arr, importance_map, out_w, out_h, scale_x, scale_y):
    in_h, in_w, channels = img_arr.shape
    output = np.zeros((out_h, out_w, channels), dtype=np.float32)
    
    for y_out in range(out_h):
        for x_out in range(out_w):
            x_in = (x_out + 0.5) * scale_x - 0.5
            y_in = (y_out + 0.5) * scale_y - 0.5

            x0 = int(np.floor(x_in - 2))
            y0 = int(np.floor(y_in - 2))

            accum = np.zeros(channels, dtype=np.float32)
            total_weight = 0.0

            for j in range(4):
                for i in range(4):
                    xi = x0 + i
                    yj = y0 + j
                    if 0 <= xi < in_w and 0 <= yj < in_h:
                        dx = x_in - xi
                        dy = y_in - yj
                        imp = importance_map[yj, xi]
                        wx = adaptive_kernel(dx, imp)
                        wy = adaptive_kernel(dy, imp)
                        w = wx * wy
                        for c in range(channels):
                            accum[c] += img_arr[yj, xi, c] * w
                        total_weight += w

            if total_weight > 0:
                for c in range(channels):
                    output[y_out, x_out, c] = accum[c] / total_weight

    return output

def resize_mitchell_adaptive(img: Image.Image, out_size: tuple) -> Image.Image:
    img_arr = np.array(img.convert("RGB"), dtype=np.float32)
    img_arr = linearize(img_arr)

    in_h, in_w = img_arr.shape[:2]
    out_w, out_h = out_size
    scale_x = in_w / out_w
    scale_y = in_h / out_h

    importance_map = compute_importance_map(img_arr)
    result = apply_adaptive_resample(img_arr, importance_map, out_w, out_h, scale_x, scale_y)

    result = delinearize(result)
    return Image.fromarray(result.astype(np.uint8))
