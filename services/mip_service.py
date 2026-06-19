from logic.mip_generator import apply_effects_pil, regenerate_mips

from models.options import RenderOptions


class MipService:
    @staticmethod
    def regenerate_original_mips(original_pil_image, options: RenderOptions, uv_weight_map):
        options_dict = options.to_dict()
        options_dict.update(RenderOptions.default_slider_params())
        original_mips = regenerate_mips(original_pil_image, options_dict, uv_weight_map)
        mips = [None] * len(original_mips)
        return original_mips, mips

    @staticmethod
    def process_single_mip(base_mip, mip_options: dict):
        return apply_effects_pil(base_mip, mip_options)
