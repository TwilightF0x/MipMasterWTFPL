import numpy as np
from PIL import Image
import cv2

def create_uv_weight_map(mask_image, target_size, max_distance=10):
    if mask_image.mode != "L":
        mask_image = mask_image.convert("L")
    
    mask_resized = mask_image.resize(target_size)
    mask_array = np.array(mask_resized)

    inverted = 255 - mask_array

    dist = cv2.distanceTransform(inverted, cv2.DIST_L2, 5)

    clipped = np.clip(dist, 0, max_distance)
    norm_dist = clipped / max_distance
    weight_map = 1.0 - norm_dist
    
    return weight_map



def overlay_mask_on_image(image: Image.Image, mask: np.ndarray, alpha=0.5) -> Image.Image:
    mask_img = Image.fromarray((mask * 255).astype(np.uint8)).resize(image.size)
    red_overlay = Image.new("RGBA", image.size, (255, 0, 0, 0))
    red_overlay.putalpha(mask_img.point(lambda p: int(p * alpha)))
    
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    
    combined = Image.alpha_composite(image, red_overlay)
    return combined
