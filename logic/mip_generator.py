from .image_utils import normalize_pil_image
from .filter_wrap import linear_dodge_channel, smart_downscale_normal, normalize_normal_map_soft, smart_downscale, boost_z_channel, safe_filter
from .mitchel_netravali_filter import resize_mitchell_with_mask, mitchell_resample
from .kaiser_filter import kaiser_downscale
from .combo_mitchel_filter import resize_mitchell_adaptive
from .upscale_method import upscale
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


def _compensate_luma(reference, sharpened, strength=0.5):
        mode = sharpened.mode
        has_alpha = "A" in sharpened.getbands()

        reference_luma = np.asarray(reference.convert("L"), dtype=np.float32)
        sharpened_luma = np.asarray(sharpened.convert("L"), dtype=np.float32)
        luma_delta = (reference_luma - sharpened_luma) * strength

        rgb = np.asarray(sharpened.convert("RGB"), dtype=np.float32)
        rgb = np.clip(rgb + luma_delta[..., None], 0, 255).astype(np.uint8)

        result = Image.fromarray(rgb, "RGB")
        if has_alpha:
            result.putalpha(sharpened.getchannel("A"))

        return result if result.mode == mode else result.convert(mode)


def apply_effects_pil(pil_image, options_set):
        img = normalize_pil_image(pil_image)
     
        brightness_r = (options_set.get("brightness_slider_r") / 100.0)
        brightness_g = (options_set.get("brightness_slider_g") / 100.0)
        brightness_b = (options_set.get("brightness_slider_b") / 100.0)
        brightness_a = (options_set.get("brightness_slider_a") / 100.0)
        sharpness    = (options_set.get("sharpness_slider") / 100.0)
        unsharp_mask = options_set.get("unsharp_mask_slider", 0)

        if img.mode == "RGB":
            r,g,b = img.split()
            r = linear_dodge_channel(r, brightness_r)
            g = linear_dodge_channel(g, brightness_g)
            b = linear_dodge_channel(b, brightness_b)

            img = Image.merge("RGB", (r,g,b))

        elif img.mode == "RGBA":
            r,g,b,a = img.split()
            r = linear_dodge_channel(r, brightness_r)
            g = linear_dodge_channel(g, brightness_g)
            b = linear_dodge_channel(b, brightness_b)
            a = linear_dodge_channel(a, brightness_a)

            img = Image.merge("RGBA", (r,g,b,a))
        
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(sharpness)

        if unsharp_mask > 0:
            luma_reference = img
            img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=unsharp_mask, threshold=3))
            img = _compensate_luma(luma_reference, img)
        
        return img


def regenerate_mips(original_pil_image, options_set, weight_mask):
        global mips
        
        processed_image = apply_effects_pil(original_pil_image, options_set)
        
        try:
            __is_strict_size = options_set.get("strict_size")
            if __is_strict_size:
                 mip_count = 2
            else:
                mip_count = int(options_set.get("mip_entry"))

            if mip_count < 1:
                raise ValueError
        except ValueError:
            raise ValueError


        mips = [processed_image]
        for i in range(1, mip_count):
            w, h = mips[-1].size
            if options_set.get("strict_size") == True:
                 new_size = (options_set.get("strict_size_y"), options_set.get("strict_size_x"))
                 if new_size[0] > original_pil_image.width  or new_size[1] > original_pil_image.height:
                    mip = safe_filter(options_set, mips[-1], upscale, new_size)
                 
            else:
                new_size = (max(1, w // 2), max(1, h // 2))

            if options_set.get("filter_type") == "ComboBox (Only Normal Map)":
                mip = safe_filter(options_set, mips[-1], smart_downscale_normal, new_size)
                mip = safe_filter(options_set, mip, normalize_normal_map_soft, mix_factor=0.5)
                # mip = safe_filter(options_set, mip, boost_z_channel, factor=1.2)

            elif options_set.get("filter_type") == "Combo Mitchel-Netravali":
                    mip = safe_filter(options_set, mips[-1], resize_mitchell_adaptive, new_size)

            elif options_set.get("filter_type") == "Mitchel-Netravali":
                if weight_mask is not None and options_set.get("checkbox_uv_method") == True:
                    mip = safe_filter(options_set, mips[-1], resize_mitchell_with_mask, new_size, weight_mask)
                else:
                    mip = safe_filter(options_set, mips[-1], mitchell_resample, new_size)

            elif options_set.get("filter_type") == "Kaiser":
                mip = safe_filter(options_set, mips[-1], kaiser_downscale, new_size)

            elif options_set.get("filter_type") == "Default texture":
                mip = safe_filter(options_set, mips[-1], smart_downscale, new_size)

            else:
                return f"Unsupported filter type: {options_set.get('filter_type')}"

            if type(mip) == str:
                error = mip
                return(error)
            
            mips.append(mip)
        
        return(mips)

