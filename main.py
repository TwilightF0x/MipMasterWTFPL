from PySide6.QtWidgets import QApplication, QListWidgetItem, QMainWindow, QVBoxLayout, QWidget, QLabel, QHBoxLayout
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QTimer

from PIL import Image
import os
import sys

from controllers.main_controller import MainController
from logic.image_utils import apply_channel_preview, load_image_from_file, normalize_pil_image, pil_to_pixmap
from models.options import OptionsMapper, RenderOptions
from models.project_state import ProjectState
from services.export_service import ExportService
from services.mip_service import MipService
from views import control_panel, menu, panels

try:
    from eastereggs.easter_logic import AchievementToast
except:
    pass

class MipmapGenerator(QMainWindow):

    def center_on_screen(self, window_w=None, window_h=None):
        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            return

        available_rect = screen.availableGeometry()
        width = self.width() if window_w is None else window_w
        height = self.height() if window_h is None else window_h

        pos_x = available_rect.x() + max(0, (available_rect.width() - width) // 2)
        pos_y = available_rect.y() + max(0, (available_rect.height() - height) // 2)
        self.move(pos_x, pos_y)

    def set_screen_resolution(self):
        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            return

        available_rect = screen.availableGeometry()
        base_w = 1280
        base_h = 800
        safe_margin_w = 32
        safe_margin_h = 32

        max_w = max(320, available_rect.width() - safe_margin_w)
        max_h = max(320, available_rect.height() - safe_margin_h)
        final_w = min(base_w, max_w)
        final_h = min(base_h, max_h)

        self.setMinimumSize(final_w, final_h)
        self.setMaximumSize(final_w, final_h)
        self.resize(final_w, final_h)
        self.center_on_screen(final_w, final_h)
    
    def show_drop_overlay(self):
        if self.drop_overlay:
            self.drop_overlay.setGeometry(self.rect())
            self.drop_overlay.raise_()
            self.drop_overlay.show()

    def hide_drop_overlay(self):
        if self.drop_overlay:
            self.drop_overlay.hide()

    def handle_mip_context_menu(self, action, index):
            if action == "copy":
                self.mip_slider_buffer = self.get_mip_options(index)
                self.status_timer(f"Settings copied from mip {index}", "#1E90FF", 3)
            
            elif action == "paste":
                if self.mip_slider_buffer is None:
                    self.status_timer("No copied settings to paste", "#B8860B", 3)
                    return

                for key, val in self.mip_slider_buffer.items():
                    key_mip = f"{index}_{key}"
                    print(f"Setting {key_mip} to {val}")
                    self.self_mip_changes[key_mip] = val
                    
                self.mips[index] = None
                self.show_selected_mip(index)
                self.status_timer(f"Pasted settings to mip {index}", "#107C10", 3)

    def setup_menu_bar(self):
        menu.setup_menu_bar(self)

    def show_about_dialog(self):
        menu.show_about_dialog(self)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MipMaster")
        self.set_screen_resolution()
        self.setup_menu_bar()

        self.state = ProjectState()
        self.mips = self.state.mips
        self.assembler_lib_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "assembler/MipAssembler.dll")
        self.compressor_exe = os.path.join(os.path.dirname(os.path.realpath(__file__)), "oodle_convert/bin/otexdds.exe")
        self.nv_compressor_exe = os.path.join(os.path.dirname(os.path.realpath(__file__)), "nvcompress/nvcompress.exe")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)), "icons/icon.ico")))

        self.current_visible_mip = self.state.current_visible_mip
        self.image_path = self.state.image_path
        self.uv_weight_map = self.state.uv_weight_map
        self.sup_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".tga", ".dds", ".gif", ".webp", ".psd", ".tif", ".tiff", ".mipj")
        self.self_mip_changes = self.state.self_mip_changes

        self.original_mips = self.state.original_mips
        self.mip_slider_buffer = self.state.mip_slider_buffer
        self.loading_project = self.state.loading_project
        self.save_path = self.state.save_path
        self.save_project_name = self.state.save_project_name
        self.show_r = self.state.show_r
        self.show_g = self.state.show_g
        self.show_b = self.state.show_b
        self.show_a = self.state.show_a
        self.preview_background_mode = self.state.preview_background_mode

        self.is_3d_mode = False
        self.max_mip_level = 0
        self.mip_service = MipService()
        self.export_service = ExportService(self.assembler_lib_path, self.compressor_exe, self.nv_compressor_exe)
        self.controller = MainController(self, self.export_service)

        main_widget = QWidget()
        central_layout = QVBoxLayout(main_widget)
        self.main_layout = QHBoxLayout()
        central_layout.addLayout(self.main_layout)
        
        self.setup_control_panel()
        
        self.setup_image_widget()
        
        self.drop_overlay = QLabel("Drop file to load", self)
        self.drop_overlay.setStyleSheet("""
            background-color: rgba(255, 92, 119, 180);
            color: white;
            font-size: 24px;
            padding: 20px;
            border: 2px dashed white;
            border-radius: 10px;
        """)
        self.drop_overlay.setAlignment(Qt.AlignCenter)
        self.drop_overlay.hide()


        self.setup_mip_preview_panel()
        
        self.setCentralWidget(main_widget)
        self.setAcceptDrops(True)

        status_bar = QHBoxLayout()
        status_bar.setContentsMargins(5, 0, 5, 5)
        status_bar.addWidget(self.status_label)
        central_layout.addLayout(status_bar)

    def save_project_call(self):
        self.controller.save_project_call()

    def open_project_call(self, file = None):
        self.controller.open_project_call(file)
  
    def setup_control_panel(self):
        panels.setup_control_panel(self)
    
    def setup_image_widget(self):
        panels.setup_image_widget(self)
        self.image_widget.channel_toggled.connect(self.on_channel_preview_toggle)
        self.image_widget.background_mode_changed.connect(self.on_preview_background_mode_changed)
        self.image_widget.set_overlay_channel_state(*self.get_channel_preview_flags())
        self.image_widget.set_background_mode(self.preview_background_mode)

    def setup_mip_preview_panel(self):
        panels.setup_mip_preview_panel(self)
    
    def setup_load_buttons(self, layout):
        control_panel.setup_load_buttons(self, layout)
    
    def setup_mipmap_settings(self, layout):
        control_panel.setup_mipmap_settings(self, layout)
    
    def clamp_sliders(self):
        control_panel.clamp_sliders(self)

    def update_label(self):
        control_panel.update_label(self)

    def setup_brightness_sliders(self, layout):        
        control_panel.setup_brightness_sliders(self, layout)
    
    def enable_strict_size(self):
        if self.strict_size.isChecked():
            self.strict_size_input_y.setVisible(True)
            self.strict_size_input_x.setVisible(True)
            self.checkbox_makeArray.setVisible(False)
            self.clean_up.setVisible(False)
            self.mip_slider.setVisible(False)
            self.extension_format.setVisible(True)
            self.bc_format.setVisible(False)

        else:
            self.strict_size_input_y.setVisible(False)
            self.strict_size_input_x.setVisible(False)
            self.checkbox_makeArray.setVisible(True)
            self.clean_up.setVisible(True)
            self.mip_slider.setVisible(True)
            self.extension_format.setVisible(False)
            self.bc_format.setVisible(True)
            self.extension_format.setCurrentIndex(0)
        
        self.update_preview()

    def on_slider_change(self, slider_name):
        idx = self.current_visible_mip
        key = f"{idx}_{slider_name}"
        value = getattr(self, slider_name).value()
        self.self_mip_changes[key] = value
        self.mips[idx] = None
        self.show_selected_mip(idx)

    def get_channel_preview_flags(self):
        return self.show_r, self.show_g, self.show_b, self.show_a

    def on_channel_preview_toggle(self, channel_name, checked):
        setattr(self, f"show_{channel_name}", checked)
        setattr(self.state, f"show_{channel_name}", checked)

        if not any(self.get_channel_preview_flags()):
            setattr(self, f"show_{channel_name}", True)
            setattr(self.state, f"show_{channel_name}", True)
            self.image_widget.set_overlay_channel_state(*self.get_channel_preview_flags())

        self.refresh_channel_preview()

    def on_preview_background_mode_changed(self, mode):
        self.preview_background_mode = mode
        self.state.preview_background_mode = mode
        self.image_widget.set_background_mode(mode)

    def refresh_channel_preview(self):
        has_mip_preview = self.original_mips and 0 <= self.current_visible_mip < len(self.mips)

        if has_mip_preview:
            self.preview_mip_levels(self.original_mips)
            self.show_selected_mip(self.current_visible_mip)
            return

        if hasattr(self, "original_pil_image"):
            self.display_image(self.original_pil_image, preserve_view=True)

    def setup_channel_sliders(self, layout):
        control_panel.setup_channel_sliders(self, layout)

    def setup_sharpness_slider(self, layout):
        control_panel.setup_sharpness_slider(self, layout)

    def update_current_mip(self):
        self.mips[self.current_visible_mip] = None
        self.update_preview()

    def setup_action_buttons(self, layout):
        control_panel.setup_action_buttons(self, layout)

    def open_export_path(self):
        control_panel.open_export_path(self)

    def output_checker(self):
        control_panel.output_checker(self)

    def open_folder_dialog(self):
        control_panel.open_folder_dialog(self)

    def status_timer(self, text: str, background: str = "#1E1E1E", countdown: int = 5):
        self.status_counter = countdown
        self.status_text = text
        self.status_background = background
        self.status_color = "white"

        self._update_status_label()

        self.status_timer_obj = QTimer()
        self.status_timer_obj.timeout.connect(self._status_timer_tick)
        self.status_timer_obj.start(1000)

    def _update_status_label(self):
        self.status_label.setText(f"{self.status_text} ({self.status_counter})")
        self.status_label.setStyleSheet(
            f"background-color: {self.status_background}; color: {self.status_color}; padding: 1px;"
        )

    def _status_timer_tick(self):
        self.status_counter -= 1
        if self.status_counter <= 0:
            self.status_timer_obj.stop()
            self.status_label.setText("Status: Ready")
            self.status_label.setStyleSheet("background-color: #1E90FF; color: white; padding: 1px;")
        else:
            self._update_status_label()

    def update_status(self, text: str, background:str = "1E1E1E", color: str = "white"):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"""
                                        QLabel {{
                                        background-color: {background}; 
                                        color: white;
                                        font-weight: bold;
                                        padding: 1px;
                                        border-radius: 1px;
                                        margin-top: 10px;
                                                }}
                                    """)
    
    def get_status_style(self, bg_color, padding="10px", margin_top="0"):
        return control_panel.get_status_style(bg_color, padding=padding, margin_top=margin_top)

    def get_button_style(self, bg_color, hover_color, padding="10px", margin_top="0"):
        return control_panel.get_button_style(bg_color, hover_color, padding=padding, margin_top=margin_top)
    
    def get_mip_options(self, index):
        get = self.self_mip_changes.get
        return {
            "brightness_slider_r": get(f"{index}_brightness_slider_r", 0),
            "brightness_slider_g": get(f"{index}_brightness_slider_g", 0),
            "brightness_slider_b": get(f"{index}_brightness_slider_b", 0),
            "brightness_slider_a": get(f"{index}_brightness_slider_a", 0),
            "sharpness_slider":    get(f"{index}_sharpness_slider", 100),
            "unsharp_mask_slider": get(f"{index}_unsharp_mask_slider", 0),
        }

    def restore_sliders_for_mip(self, index):
        get = self.self_mip_changes.get
        self.brightness_slider_r.setValue(get(f"{index}_brightness_slider_r", 0))
        self.brightness_slider_g.setValue(get(f"{index}_brightness_slider_g", 0))
        self.brightness_slider_b.setValue(get(f"{index}_brightness_slider_b", 0))
        self.brightness_slider_a.setValue(get(f"{index}_brightness_slider_a", 0))
        self.sharpness_slider.setValue(get(f"{index}_sharpness_slider", 100))
        getattr(self, "unsharp_mask_slider").setValue(get(f"{index}_unsharp_mask_slider", 0))

    def get_current_mip_options(self, index):
        return {
            "brightness_slider_r": self.self_mip_changes.get(f"{index}_brightness_slider_r", 0),
            "brightness_slider_g": self.self_mip_changes.get(f"{index}_brightness_slider_g", 0),
            "brightness_slider_b": self.self_mip_changes.get(f"{index}_brightness_slider_b", 0),
            "brightness_slider_a": self.self_mip_changes.get(f"{index}_brightness_slider_a", 0),
            "sharpness_slider": self.self_mip_changes.get(f"{index}_sharpness_slider", 100),
            "unsharp_mask_slider": self.self_mip_changes.get(f"{index}_unsharp_mask_slider", 0),

        }

    def show_selected_mip(self, item_or_index):
        
        if isinstance(item_or_index, QListWidgetItem):
            index = self.mip_preview.row(item_or_index)
        else:
            index = item_or_index

        previous_mip_index = self.current_visible_mip
        mip_changed = index != previous_mip_index
        self.current_visible_mip = index
        self.mip_preview.setCurrentRow(index)
        if index < 0 or index >= len(self.original_mips):
            return

        if self.mips[index] is None:
            base = self.original_mips[index]
            options = self.get_mip_options(index)
            processed = self.mip_service.process_single_mip(base, options)
            self.mips[index] = processed

        preview_image = apply_channel_preview(self.mips[index], *self.get_channel_preview_flags())
        self.image_widget.set_image(
            preview_image,
            preserve_view=not mip_changed,
            preserve_relative_zoom=mip_changed,
        )
        self.restore_sliders_for_mip(index)
        
    def get_max_mip_level(self, image):
        width, height = image.size
        mip_levels = 0

        while width >= 1 or height >= 1:
            width = width // 2
            height = height // 2
            mip_levels += 1

        self.max_mip_level = mip_levels - 1
        self.mip_slider.setMaximum(mip_levels)
        self.mip_slider.setValue(mip_levels)

        self.min_slider.setMaximum(mip_levels)
        self.max_slider.setMaximum(mip_levels)
        self.max_slider.setValue(mip_levels)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile() and url.fileName().endswith(self.sup_extensions):
                    event.acceptProposedAction()
                    self.show_drop_overlay()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        event.accept()

    def dragLeaveEvent(self, event):
        self.hide_drop_overlay()

    def dropEvent(self, event):
        self.hide_drop_overlay()
        for url in event.mimeData().urls():
            if url.isLocalFile():

                if url.fileName().endswith(".mipj"):
                    file_path = [url.toLocalFile()]
                    file_path[0] = file_path[0].upper()
                    self.open_project_call(file_path)
                    break

                self.load_image_from_path(url.toLocalFile())
                break
        event.acceptProposedAction()

    def update_title(self):
        print(self.save_path)
        opened_project = self.save_path if self.save_path != None else "Default Starter"
        opened_project = opened_project + "/" + self.save_project_name if self.save_project_name else opened_project

        self.setWindowTitle(f'MipMaster - Current Image: "{self.output_filename.text()}" Current Project: "{opened_project}"')

    def load_image_from_path(self, file_path: str):
        self.controller.load_image_from_path(file_path)

    def load_image(self):
        self.controller.load_image()

    def load_uv(self):
        self.controller.load_uv()
    
    def display_image(self, path, preserve_view=False):
        try:
            if isinstance(path, str):
                if os.path.exists(path):
                    pil_image = load_image_from_file(path)
                    self.original_pil_image = pil_image
                else:
                    self.status_timer(f"File not found: {path}", "#8B0000")
                    return

            elif isinstance(path, Image.Image):
                pil_image = normalize_pil_image(path)
                self.original_pil_image = pil_image
            else:
                self.status_timer("Invalid image format (expected path or PIL.Image)", "#8B0000")
                return

            preview_image = apply_channel_preview(pil_image, *self.get_channel_preview_flags())
            pixmap = pil_to_pixmap(preview_image)
            scaled = pixmap.scaled(
                self.image_widget.width() - 20,
                self.image_widget.height() - 20,
                Qt.AspectRatioMode.KeepAspectRatio,
            )

            self.image_widget.set_image(scaled, preserve_view=preserve_view)

        except Exception as e:
            self.status_timer(f"Error: {str(e)}", "#8B0000")
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        has_mips = bool(self.original_mips) and 0 <= self.current_visible_mip < len(self.original_mips)
        if has_mips:
            self.show_selected_mip(self.current_visible_mip)
        elif self.image_path:
            self.display_image(self.image_path, preserve_view=True)
        
    def preview_mip_levels(self, mip_list):
        self.mip_preview.clear()

        for i, mip in enumerate(mip_list):
            width, height = mip.size
            thumb = mip.resize((80, 80), resample=Image.LANCZOS)
            preview_thumb = apply_channel_preview(thumb, *self.get_channel_preview_flags())
            pixmap = pil_to_pixmap(preview_thumb)
            item = QListWidgetItem(f"Mip {i} - {width}x{height}")
            item.setIcon(QIcon(pixmap))
            self.mip_preview.addItem(item)
    
    def generate_mipmaps(self):
        self.controller.generate_mipmaps()

    def collect_current_options(self):
        return OptionsMapper.from_window(self).to_dict()
    
    def __default_slider_params(self):
        return RenderOptions.default_slider_params()
    
    def refresh_current_mip(self):
        idx = self.current_visible_mip
        self.mips[idx] = None
        self.show_selected_mip(idx)

    def regenerate_original_mips(self):
        self.controller.regenerate_original_mips()

    def update_preview(self):
        try:
            self.controller.update_preview()
        except Exception as e:
            if self.strict_size_input_x.text() == "0" and self.strict_size_input_y.text() == "0":
                self.toaster = AchievementToast("Achievement Unlocked: \nTry to disintegrate the image!", r"C:\Users\Bingus\Downloads\peep.jpg")
                self.toaster.show()
            elif self.strict_size_input_x.text() == "9999" and self.strict_size_input_y.text() == "9999":
                self.toaster = AchievementToast("Achievement Unlocked: \nTry to destroy your PC!", r"C:\Users\Bingus\Downloads\peep.jpg")

            self.status_timer(f"Error updating preview: {e}", "#8B0000")

    def apply_effects(self, pil_image):
        processed_img = self.mip_service.process_single_mip(pil_image, self.collect_current_options())
        return pil_to_pixmap(processed_img)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MipmapGenerator()
    window.show()
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if file_path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tga", ".dds", ".gif", ".webp", ".psd", ".tif", ".tiff")):
            try:
                window.load_image_from_path(file_path)
            except Exception as e:
                print(f"Failed to load image: {e}")

        if file_path.lower().endswith(".mipj"):
            if os.path.exists(file_path):
                file_path = [file_path]
                file_path[0] = file_path[0].upper()
            try:
                window.open_project_call(file_path)
            except Exception as e:
                print(f"Failed to open MIPJ file: {e}")

    sys.exit(app.exec())