import os
from typing import Optional, Tuple

from io_logic.io_methods import open_file, save_file


class ProjectService:
    @staticmethod
    def build_save_payload(window, mip_options_getter) -> Tuple[Optional[str], Optional[str], Optional[dict]]:
        folder = window.save_path if window.save_path else None
        if not folder:
            return None, "Save path is not set.", None

        if not os.path.exists(folder):
            return None, "Save path is not valid.", None

        name = window.output_filename.text().strip()
        if not name:
            return None, "Filename cannot be empty.", None

        if not window.original_mips or not window.original_mips[0]:
            return None, "No base image to save.", None

        content = {}
        for i in range(window.max_mip_level):
            mip_options = mip_options_getter(i)
            if not isinstance(mip_options, dict):
                return None, f"Invalid data for MIP level {i}.", None
            content[str(i)] = mip_options

        content.update(
            {
                "max_mip_level": window.max_mip_level,
                "output_filename": name,
                "output_path": folder,
                "slice_min": window.min_slider.value(),
                "slice_max": window.max_slider.value(),
                "strict_size": window.strict_size.isChecked(),
                "filter_type": window.bc_format.currentIndex(),
                "a_filter_type": window.a_filter_type.currentIndex(),
                "mip_level": window.mip_slider.value(),
                "save_path": window.save_path,
                "save_project_name": name,
            }
        )

        if content["strict_size"]:
            try:
                content["size_y"] = int(window.strict_size_input_y.text())
                content["size_x"] = int(window.strict_size_input_x.text())
            except ValueError:
                return None, "Invalid size values.", None

        return folder, None, content

    @staticmethod
    def save_project(name: str, folder: str, base_image, content: dict) -> None:
        save_file(name, folder, base_image, content)

    @staticmethod
    def open_project(path: str):
        return open_file(path)
