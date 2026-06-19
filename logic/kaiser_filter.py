import numpy as np
from PIL import Image
from scipy.signal.windows import kaiser
from scipy.signal import convolve2d
from scipy.ndimage import map_coordinates

def kaiser_downscale(pil_img, new_size, beta=14, max_ksize=25):
    img = np.array(pil_img.convert("RGB"), dtype=np.float32) / 255.0
    h, w = img.shape[:2]

    scale_x = w / new_size[0]
    scale_y = h / new_size[1]

    ksize = int(max(scale_x, scale_y) * 2 + 1)
    ksize = max(3, min(ksize, max_ksize))

    kaiser_win = kaiser(ksize, beta)
    kernel = np.outer(kaiser_win, kaiser_win)
    kernel /= kernel.sum()

    filtered = np.empty_like(img)
    for i in range(3):
        filtered[:, :, i] = convolve2d(img[:, :, i], kernel, mode='same', boundary='symm')

    y_coords = (np.arange(new_size[1]) + 0.5) * scale_y - 0.5
    x_coords = (np.arange(new_size[0]) + 0.5) * scale_x - 0.5

    X, Y = np.meshgrid(x_coords, y_coords)

    result = np.zeros((new_size[1], new_size[0], 3), dtype=np.float32)
    for c in range(3):
        result[:, :, c] = map_coordinates(filtered[:, :, c], [Y, X], order=1, mode='reflect')

    return Image.fromarray(np.clip(result * 255, 0, 255).astype(np.uint8), mode="RGB")
