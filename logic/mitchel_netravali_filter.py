import numpy as np
from PIL import Image

from numba import njit, prange

##--base mitchel--##
@njit
def mitchell_kernel(x, B=1/3, C=1/3):
    result = np.zeros_like(x)
    for i in range(len(x)):
        abs_x = abs(x[i])
        if abs_x < 1:
            result[i] = ((12 - 9*B - 6*C)*(abs_x**3) +
                         (-18 + 12*B + 6*C)*(abs_x**2) +
                         (6 - 2*B)) / 6
        elif abs_x < 2:
            result[i] = ((-B - 6*C)*(abs_x**3) +
                         (6*B + 30*C)*(abs_x**2) +
                         (-12*B - 48*C)*abs_x +
                         (8*B + 24*C)) / 6
        else:
            result[i] = 0.0
    return result

def mitchell_resample(pil_img, new_size, B=1/3, C=1/3):

    img = np.array(pil_img.convert("RGB"), dtype=np.float32) / 255.0
    scale_x = new_size[0] / img.shape[1]
    scale_y = new_size[1] / img.shape[0]

    radius = 2

    def resize_axis(data, axis, scale):
        in_len = data.shape[axis]
        out_len = int(np.floor(in_len * scale))
        coords = (np.arange(out_len) + 0.5) / scale - 0.5

        result = np.zeros_like(np.swapaxes(data, 0, axis)[:out_len])
        kernel_range = np.arange(-radius + 1, radius + 1)

        for i, coord in enumerate(coords):
            center = int(np.floor(coord))
            weights = mitchell_kernel(coord - (center + kernel_range), B, C)
            weights /= np.sum(weights)

            samples = []
            for offset in kernel_range:
                idx = np.clip(center + offset, 0, in_len - 1)
                samples.append(np.take(data, idx, axis=axis))
            samples = np.stack(samples, axis=0)

            result[i] = np.tensordot(weights, samples, axes=([0], [0]))

        return np.swapaxes(result, 0, axis)

    resized = resize_axis(img, axis=1, scale=scale_x)
    resized = resize_axis(resized, axis=0, scale=scale_y)
    return Image.fromarray(np.clip(resized * 255, 0, 255).astype(np.uint8))

@njit
def mitchell_netravali(x, B=1/3, C=1/3):
    x = abs(x)
    if x < 1:
        return ((12 - 9*B - 6*C)*(x**3) + (-18 + 12*B + 6*C)*(x**2) + (6 - 2*B)) / 6
    elif x < 2:
        return ((-B - 6*C)*(x**3) + (6*B + 30*C)*(x**2) + (-12*B - 48*C)*x + (8*B + 24*C)) / 6
    return 0

@njit(parallel=True)
def resize_mitchell_core(img_arr, weight_mask, out_h, out_w, scale_y, scale_x):
    in_h, in_w, channels = img_arr.shape
    output = np.zeros((out_h, out_w, channels), dtype=np.float32)

    for y_out in prange(out_h):
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
                    if weight_mask[yj, xi] < 0.05:
                        continue

                    if 0 <= xi < in_w and 0 <= yj < in_h:

                        dx = x_in - xi
                        dy = y_in - yj
                        wx = mitchell_netravali(dx)
                        wy = mitchell_netravali(dy)
                        w = wx * wy * weight_mask[yj, xi]

                        for c in range(channels):
                            accum[c] += img_arr[yj, xi, c] * w
                        total_weight += w

            if total_weight > 0:
                for c in range(channels):
                    output[y_out, x_out, c] = accum[c] / total_weight

    return output

def resize_mitchell_with_mask(img: Image.Image, out_size: tuple, weight_mask: np.ndarray):
    img_arr = np.array(img).astype(np.float32)
    if img_arr.ndim == 2:
        img_arr = img_arr[..., np.newaxis]

    in_h, in_w = img_arr.shape[:2]
    out_w, out_h = out_size
    scale_x = in_w / out_w
    scale_y = in_h / out_h

    resized = resize_mitchell_core(img_arr, weight_mask.astype(np.float32), out_h, out_w, scale_y, scale_x)
    resized = np.clip(resized, 0, 255).astype(np.uint8)
    return Image.fromarray(resized.squeeze() if resized.shape[2] == 1 else resized)
