import os

from PIL import Image
from PySide6.QtWidgets import QFileDialog

from logic.image_utils import apply_channel_preview, pil_to_pixmap
from logic.uv_mask_support import create_uv_weight_map, overlay_mask_on_image
from models.options import OptionsMapper
from services.mip_service import MipService
from services.project_service import ProjectService


class MainController:
    def __init__(self, window, export_service):
        self.window = window
        self.project_service = ProjectService()
        self.mip_service = MipService()
        self.export_service = export_service

    def collect_options(self):
        return OptionsMapper.from_window(self.window)

    def save_project_call(self):
        if not self.window.save_path:
            selected = QFileDialog.getExistingDirectory(self.window, "Select save path")
            if selected:
                self.window.save_path = selected

        folder, error, content = self.project_service.build_save_payload(self.window, self.window.get_mip_options)
        if error:
            self.window.status_timer(error, "#8B0000", 5)
            return
        if folder is None or content is None:
            self.window.status_timer("Save payload is incomplete.", "#8B0000", 5)
            return

        name = self.window.output_filename.text().strip()
        self.project_service.save_project(name, folder, self.window.original_mips[0], content)
        self.window.save_project_name = name
        self.window.save_path = folder
        self.window.status_timer("Project saved successfully!", "#4CAF50", 5)
        self.window.update_title()

    def open_project_call(self, file=None):
        if not file:
            file = QFileDialog.getOpenFileName(
                self.window, "Select project file", "", "MIPJ Files (*.mipj);;All Files (*)"
            )
        if not file or not file[0]:
            return

        pulled = self.project_service.open_project(file[0])
        if not pulled[0] or not pulled[1]:
            self.window.status_timer("File damaged, can't open.", "#8B0000", 5)
            return

        self.window.display_image(pulled[0])
        self.window.get_max_mip_level(self.window.original_pil_image)
        self.window.self_mip_changes.clear()

        settings = pulled[1]
        self.window.bc_format.setCurrentIndex(int(settings["filter_type"]))
        self.window.a_filter_type.setCurrentIndex(int(settings["a_filter_type"]))
        self.window.max_mip_level = settings["max_mip_level"]
        self.window.output_filename.setText(settings["output_filename"])
        self.window.output_path.setText(settings["output_path"])
        self.window.min_slider.setValue(settings["slice_min"])
        self.window.max_slider.setValue(settings["slice_max"])
        self.window.mip_slider.setValue(int(settings["mip_level"]))
        self.window.save_path = settings.get("save_path")
        self.window.save_project_name = settings.get("save_project_name")

        strict_size = settings.get("strict_size", False)
        if isinstance(strict_size, str):
            strict_size = strict_size.lower() == "true"
        self.window.strict_size.setChecked(strict_size)
        if strict_size and "size_y" in settings and "size_x" in settings:
            self.window.strict_size_input_y.setText(str(settings["size_y"]))
            self.window.strict_size_input_x.setText(str(settings["size_x"]))

        for i in range(self.window.max_mip_level):
            self.window.mips[i] = None
            mip_key = str(i)
            if mip_key in settings:
                mip_data = settings[mip_key]
                for param_name, param_value in mip_data.items():
                    key_mip = f"{mip_key}_{param_name}"
                    self.window.self_mip_changes[key_mip] = param_value

        self.window.show_selected_mip(0)
        self.window.loading_project = True
        self.window.preview_mip_levels(self.window.original_mips)
        self.window.show_selected_mip(0)
        self.window.loading_project = False
        self.window.update_title()

    def load_image_from_path(self, file_path: str):
        if not file_path or not os.path.exists(file_path):
            self.window.status_timer("Error: File not found", "#8B0000", 5)
            return

        self.window.output_path.setText(os.path.dirname(os.path.abspath(file_path)))
        self.window.output_filename.setText(os.path.splitext(os.path.basename(file_path))[0])
        self.window.image_path = file_path
        self.window.display_image(self.window.image_path)
        self.window.update_title()
        self.window.status_timer("File loaded", "#107C10", 5)
        self.window.get_max_mip_level(self.window.original_pil_image)
        self.regenerate_original_mips()
        self.window.preview_mip_levels(self.window.original_mips)

    def load_image(self):
        filename, _ = QFileDialog.getOpenFileName(
            self.window,
            "Open Texture",
            "",
            "Images (*.png *.jpg *.jpeg *.tga *.bmp *.gif *.psd *.webp *.tif *.tiff)",
        )
        if not filename:
            return

        self.window.image_path = filename
        self.window.display_image(filename)
        self.window.status_timer("File loaded", "#107C10", 5)
        self.window.get_max_mip_level(self.window.original_pil_image)
        self.update_preview()
        self.window.preview_mip_levels(self.window.original_mips)

    def load_uv(self):
        filename, _ = QFileDialog.getOpenFileName(
            self.window,
            "Open Texture",
            "",
            "Images (*.png *.jpg *.jpeg *.tga *.bmp)",
        )
        if not filename:
            return

        uv_mask = Image.open(filename).convert("L")
        self.window.uv_weight_map = create_uv_weight_map(uv_mask, self.window.original_pil_image.size)

        preview_img = overlay_mask_on_image(self.window.original_pil_image.copy(), self.window.uv_weight_map)
        preview_img = apply_channel_preview(preview_img, *self.window.get_channel_preview_flags())
        pixmap = pil_to_pixmap(preview_img)
        self.window.image_widget.set_image(pixmap)

    def regenerate_original_mips(self):
        options = self.collect_options()
        original_mips, mips = self.mip_service.regenerate_original_mips(
            self.window.original_pil_image, options, self.window.uv_weight_map
        )
        self.window.original_mips = original_mips
        self.window.mips = mips

    def update_preview(self):
        if self.window.current_visible_mip > self.window.mip_slider.value():
            self.window.current_visible_mip = self.window.mip_slider.value()
            self.window.refresh_current_mip()

        if self.window.loading_project:
            return

        self.window.max_slider.setMaximum(self.window.mip_slider.value() - 1)
        self.window.min_slider.setMaximum(self.window.max_slider.maximum())
        if self.window.max_slider.value() > self.window.mip_slider.value():
            self.window.max_slider.setValue(self.window.mip_slider.value() - 1)

        self.regenerate_original_mips()
        self.window.preview_mip_levels(self.window.original_mips)
        self.window.show_selected_mip(self.window.current_visible_mip)

    def generate_mipmaps(self):
        if not hasattr(self.window, "original_pil_image"):
            self.window.status_timer("Warning: No image loaded!", "#B8860B")
            return

        folder_path = self.window.output_path.text().strip()
        if not folder_path:
            self.window.status_timer("Export path is not set!", "#8B0000")
            return

        output_name = self.window.output_filename.text().strip() or "Default_name_output"

        try:
            self.export_service.export_mips(
                folder_path=folder_path,
                output_filename=output_name,
                extension=self.window.extension_format.currentText(),
                strict_size=self.window.strict_size.isChecked(),
                min_mip=self.window.min_slider.value(),
                max_mip=self.window.max_slider.value(),
                original_mips=self.window.original_mips,
                mips=self.window.mips,
                mip_options_getter=self.window.get_mip_options,
                apply_effects_fn=self.mip_service.process_single_mip,
                make_array=self.window.checkbox_makeArray.isChecked(),
                bc_format=self.window.bc_format.currentText(),
                cleanup=self.window.clean_up.isChecked(),
            )
            self.window.status_timer("Export completed.", "#107C10", 5)
        except Exception as exc:
            self.window.status_timer(f"Export failed: {exc}", "#8B0000", 10)
