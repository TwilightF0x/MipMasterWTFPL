from dataclasses import dataclass


@dataclass
class RenderOptions:
    strict_size: bool
    strict_size_y: int
    strict_size_x: int
    alpha_filter_type: str
    brightness_slider_r: int
    brightness_slider_g: int
    brightness_slider_b: int
    brightness_slider_a: int
    sharpness_slider: int
    unsharp_mask_slider: int
    mip_entry: int
    filter_type: str
    checkbox_uv_method: bool

    def to_dict(self) -> dict:
        return {
            "strict_size": self.strict_size,
            "strict_size_y": self.strict_size_y,
            "strict_size_x": self.strict_size_x,
            "alpha_filter_type": self.alpha_filter_type,
            "brightness_slider_r": self.brightness_slider_r,
            "brightness_slider_g": self.brightness_slider_g,
            "brightness_slider_b": self.brightness_slider_b,
            "brightness_slider_a": self.brightness_slider_a,
            "sharpness_slider": self.sharpness_slider,
            "unsharp_mask_slider": self.unsharp_mask_slider,
            "mip_entry": self.mip_entry,
            "filter_type": self.filter_type,
            "checkbox_uv_method": self.checkbox_uv_method,
        }

    @staticmethod
    def default_slider_params() -> dict:
        return {
            "brightness_slider_r": 0,
            "brightness_slider_g": 0,
            "brightness_slider_b": 0,
            "brightness_slider_a": 0,
            "sharpness_slider": 100,
            "unsharp_mask_slider": 0,
        }


class OptionsMapper:
    @staticmethod
    def from_window(window) -> RenderOptions:
        strict_size_enabled = window.strict_size.isChecked()
        return RenderOptions(
            strict_size=strict_size_enabled,
            strict_size_y=int(window.strict_size_input_y.text()) if strict_size_enabled else 0,
            strict_size_x=int(window.strict_size_input_x.text()) if strict_size_enabled else 0,
            alpha_filter_type=window.a_filter_type.currentText(),
            brightness_slider_r=window.brightness_slider_r.value(),
            brightness_slider_g=window.brightness_slider_g.value(),
            brightness_slider_b=window.brightness_slider_b.value(),
            brightness_slider_a=window.brightness_slider_a.value(),
            sharpness_slider=window.sharpness_slider.value(),
            unsharp_mask_slider=window.unsharp_mask_slider.value(),
            mip_entry=window.mip_slider.value(),
            filter_type=window.filter_combo.currentText(),
            checkbox_uv_method=window.checkbox_uv_method.isChecked(),
        )
