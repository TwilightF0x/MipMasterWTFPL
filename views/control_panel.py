import os

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QIntValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
)


def setup_load_buttons(window, layout):
    window.load_button = QPushButton("📁 Load Texture")
    window.load_button.setStyleSheet(get_button_style("#0078D7", "#106EBE"))
    window.load_button.clicked.connect(window.load_image)
    layout.addWidget(window.load_button)

    window.load_uv_button = QPushButton("📁 Load UV Mask")
    window.load_uv_button.setStyleSheet(get_button_style("#0078D7", "#106EBE"))
    window.load_uv_button.clicked.connect(window.load_uv)


def setup_mipmap_settings(window, layout):
    layout.addWidget(QLabel("\nMipmap Settings"))
    layout.addWidget(QLabel("Set filters:"))

    window.filter_combo = QComboBox()
    window.filter_combo.addItems(
        [
            "ComboBox (Only Normal Map)",
            "Mitchel-Netravali",
            "Combo Mitchel-Netravali",
            "Kaiser",
            "Default texture",
        ]
    )
    window.filter_combo.setCurrentIndex(2)
    layout.addWidget(window.filter_combo)

    layout.addWidget(QLabel("Set formats:"))
    window.bc_format = QComboBox()
    window.bc_format.addItems(["BC1", "BC2", "BC3", "BC6U", "BC7", "R8G8B8A8_UNORM", "R32G32B32A32_FLOAT"])
    window.bc_format.setCurrentIndex(4)
    layout.addWidget(window.bc_format)

    window.extension_format = QComboBox()
    window.extension_format.addItems([".tga", ".png", ".jpg", ".dds"])
    window.extension_format.setVisible(False)
    layout.addWidget(window.extension_format)

    layout.addWidget(QLabel("Set alpha filters:"))
    window.a_filter_type = QComboBox()
    window.a_filter_type.addItems(["Soft", "Exact"])
    window.a_filter_type.setCurrentIndex(1)
    layout.addWidget(window.a_filter_type)

    layout.addWidget(QLabel("\nMip Levels:"))
    window.mip_slider = QSlider(Qt.Orientation.Horizontal)
    window.mip_slider.setRange(1, window.max_mip_level)
    window.mip_slider.setValue(window.max_mip_level)
    window.mip_slider.setSingleStep(1)
    layout.addWidget(window.mip_slider)

    window.min_slider = QSlider(Qt.Horizontal)
    window.max_slider = QSlider(Qt.Horizontal)
    window.min_slider.setRange(0, 12)
    window.max_slider.setRange(0, 12)
    window.min_slider.setValue(0)
    window.max_slider.setValue(12)
    window.min_slider.setSingleStep(1)
    window.max_slider.setSingleStep(1)

    window.label = QLabel()
    layout.addWidget(window.min_slider)
    layout.addWidget(window.max_slider)
    layout.addWidget(window.label)

    update_label(window)

    window.filter_combo.currentIndexChanged.connect(window.update_preview)
    window.mip_slider.valueChanged.connect(window.update_preview)
    window.a_filter_type.currentIndexChanged.connect(window.update_preview)
    window.min_slider.valueChanged.connect(window.clamp_sliders)
    window.max_slider.valueChanged.connect(window.clamp_sliders)


def clamp_sliders(window):
    if window.min_slider.value() > window.max_slider.value():
        window.min_slider.setValue(window.max_slider.value())
    update_label(window)


def update_label(window):
    min_val = window.min_slider.value()
    max_val = window.max_slider.value()
    window.label.setText(f"|Slice mip range: {min_val} - {max_val}|")


def setup_brightness_sliders(window, layout):
    # TODO: Add back in later
    window.checkbox_uv_method = QCheckBox("Use UV mask method")
    window.checkbox_uv_method.setChecked(False)
    # layout.addWidget(window.checkbox_uv_method)

    window.checkbox_makeArray = QCheckBox("Convert mips into array")
    window.checkbox_makeArray.setChecked(True)
    layout.addWidget(window.checkbox_makeArray)

    window.clean_up = QCheckBox("Clean up after")
    window.clean_up.setChecked(True)
    layout.addWidget(window.clean_up)

    window.strict_size = QCheckBox("Enable STRICT SIZE")
    window.strict_size.setChecked(False)
    window.strict_size.stateChanged.connect(window.enable_strict_size)
    layout.addWidget(window.strict_size)

    window.strict_size_input_y = QLineEdit()
    window.strict_size_input_y.setPlaceholderText("Enter height")
    window.strict_size_input_y.setValidator(QIntValidator(0, 9999))
    window.strict_size_input_y.setText("128")
    window.strict_size_input_y.setVisible(False)
    window.strict_size_input_y.editingFinished.connect(window.update_preview)
    layout.addWidget(window.strict_size_input_y)

    window.strict_size_input_x = QLineEdit()
    window.strict_size_input_x.setPlaceholderText("Enter width")
    window.strict_size_input_x.setValidator(QIntValidator(0, 9999))
    window.strict_size_input_x.setText("128")
    window.strict_size_input_x.setVisible(False)
    window.strict_size_input_x.editingFinished.connect(window.update_preview)
    layout.addWidget(window.strict_size_input_x)

    setup_channel_sliders(window, layout)


def setup_channel_sliders(window, layout):
    window.label_r = QLabel("\nBrightness R:")
    window.brightness_slider_r = QSlider(Qt.Orientation.Horizontal)
    window.brightness_slider_r.setRange(0, 100)
    window.brightness_slider_r.setValue(0)
    window.brightness_slider_r.valueChanged.connect(lambda: window.on_slider_change("brightness_slider_r"))

    window.label_g = QLabel("\nBrightness G:")
    window.brightness_slider_g = QSlider(Qt.Orientation.Horizontal)
    window.brightness_slider_g.setRange(0, 100)
    window.brightness_slider_g.setValue(0)
    window.brightness_slider_g.valueChanged.connect(lambda: window.on_slider_change("brightness_slider_g"))

    window.label_b = QLabel("\nBrightness B:")
    window.brightness_slider_b = QSlider(Qt.Orientation.Horizontal)
    window.brightness_slider_b.setRange(0, 100)
    window.brightness_slider_b.setValue(0)
    window.brightness_slider_b.valueChanged.connect(lambda: window.on_slider_change("brightness_slider_b"))

    window.label_a = QLabel("\nBrightness A:")
    window.brightness_slider_a = QSlider(Qt.Orientation.Horizontal)
    window.brightness_slider_a.setRange(0, 100)
    window.brightness_slider_a.setValue(0)
    window.brightness_slider_a.valueChanged.connect(lambda: window.on_slider_change("brightness_slider_a"))

    for widget in [
        window.label_r,
        window.brightness_slider_r,
        window.label_g,
        window.brightness_slider_g,
        window.label_b,
        window.brightness_slider_b,
        window.label_a,
        window.brightness_slider_a,
    ]:
        layout.addWidget(widget)


def setup_sharpness_slider(window, layout):
    layout.addWidget(QLabel("Sharpness:"))
    window.sharpness_slider = QSlider(Qt.Orientation.Horizontal)
    window.sharpness_slider.setRange(0, 500)
    window.sharpness_slider.setValue(100)
    window.sharpness_slider.valueChanged.connect(lambda: window.on_slider_change("sharpness_slider"))
    layout.addWidget(window.sharpness_slider)

    layout.addWidget(QLabel("Unsharp Mask:"))
    window.unsharp_mask_slider = QSlider(Qt.Orientation.Horizontal)
    window.unsharp_mask_slider.setRange(0, 500)
    window.unsharp_mask_slider.setValue(0)
    window.unsharp_mask_slider.valueChanged.connect(lambda: window.on_slider_change("unsharp_mask_slider"))
    layout.addWidget(window.unsharp_mask_slider)


def setup_action_buttons(window, layout):
    window.output_filename = QLineEdit()
    window.output_filename.setPlaceholderText("Enter output filename...")
    layout.addWidget(window.output_filename)

    output_path_layout = QHBoxLayout()
    window.to_export_path = QPushButton("Open Path")
    window.to_export_path.setFixedWidth(60)
    window.browse_button = QPushButton("📂")
    window.browse_button.setFixedWidth(30)
    window.output_path = QLineEdit()
    window.output_path.setPlaceholderText("Enter output path...")
    window.output_path.editingFinished.connect(window.output_checker)
    output_path_layout.addWidget(window.output_path)
    output_path_layout.addWidget(window.browse_button)
    output_path_layout.addWidget(window.to_export_path)
    window.browse_button.clicked.connect(window.open_folder_dialog)
    window.to_export_path.clicked.connect(window.open_export_path)
    layout.addLayout(output_path_layout)

    window.generate_button = QPushButton("🔄 Generate Mipmaps")
    window.generate_button.setStyleSheet(get_button_style("#107C10", "#0E700E", padding="12px", margin_top="20px"))
    window.generate_button.clicked.connect(window.generate_mipmaps)
    layout.addWidget(window.generate_button)

    window.status_label = QLabel("Status: Ready")
    window.status_label.setAlignment(Qt.AlignCenter)
    window.status_label.setStyleSheet(get_status_style("#1E90FF", padding="1px", margin_top="0px"))
    layout.addWidget(window.status_label)


def open_export_path(window):
    folder = window.output_path.text()
    if folder and os.path.exists(folder):
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
    else:
        window.status_timer("Path is empty!", "#8B0000", 5)


def output_checker(window):
    if not os.path.exists(window.output_path.text()):
        window.output_path.setText("")
        window.status_timer("Current path is not valid. Check it out!", "#8B0000", 5)


def open_folder_dialog(window):
    try:
        folder = QFileDialog.getExistingDirectory(window, "Select output path")
        if folder and os.path.exists(folder):
            window.output_path.setText(folder)
    except Exception:
        window.status_timer("Current path is not valid. Check it out!", "#8B0000", 5)


def get_status_style(bg_color, padding="10px", margin_top="0"):
    return f"""
        QLabel {{
            background-color: {bg_color};
            color: white;
            font-weight: bold;
            padding: {padding};
            border-radius: 1px;
            margin-top: {margin_top};
        }}
        """


def get_button_style(bg_color, hover_color, padding="10px", margin_top="0"):
    return f"""
        QPushButton {{
            background-color: {bg_color};
            color: white;
            font-weight: bold;
            padding: {padding};
            border-radius: 5px;
            margin-top: {margin_top};
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
    """
