from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QListView, QScrollArea, QVBoxLayout, QWidget

from views.mip_preview_list import HoverSelectableMipList
from views.zoomable_image_view import ZoomableImageView


def setup_control_panel(window):
    scroll_content = QWidget()
    scroll_content.setMaximumWidth(460)
    scroll_content.setMinimumWidth(300)

    control_layout = QVBoxLayout(scroll_content)
    control_layout.setContentsMargins(5, 5, 5, 5)

    window.setup_load_buttons(control_layout)
    window.setup_mipmap_settings(control_layout)
    window.setup_brightness_sliders(control_layout)
    window.setup_sharpness_slider(control_layout)
    window.setup_action_buttons(control_layout)
    control_layout.addStretch()

    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setWidget(scroll_content)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll_area.setStyleSheet(
        """
        QScrollArea {
            border: none;
            background: transparent;
        }
        QScrollBar:vertical {
            width: 10px;
            background: #2D2D30;
        }
        QScrollBar::handle:vertical {
            background: #3F3F46;
            min-height: 20px;
            border-radius: 5px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        """
    )

    window.main_layout.addWidget(scroll_area, 1)


def setup_image_widget(window):
    window.image_widget = ZoomableImageView()
    window.main_layout.addWidget(window.image_widget)
    window.image_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
    window.image_widget.setStyleSheet(
        """
        QLabel {
            background-color: #2D2D30;
            border: 2px dashed #3F3F46;
            border-radius: 5px;
        }
        """
    )
    window.image_widget.setMinimumSize(400, 400)
    window.main_layout.addWidget(window.image_widget, 2)


def setup_mip_preview_panel(window):
    right_panel = QWidget()
    right_layout = QVBoxLayout(right_panel)
    right_layout.setContentsMargins(5, 5, 5, 5)

    window.mip_preview = HoverSelectableMipList()
    window.mip_preview.on_hover_select = window.show_selected_mip
    window.mip_preview.setFlow(QListView.Flow.TopToBottom)
    window.mip_preview.setMovement(QListView.Movement.Static)
    window.mip_preview.setResizeMode(QListView.ResizeMode.Fixed)
    window.mip_preview.setViewMode(QListView.ViewMode.ListMode)
    window.mip_preview.setIconSize(QSize(80, 80))
    window.mip_preview.setFixedWidth(250)
    window.mip_preview.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
    window.mip_preview.context_menu_callback = window.handle_mip_context_menu
    window.mip_preview.setStyleSheet(
        """
        QListWidget {
            background-color: #2D2D30;
            border: 1px solid #3F3F46;
            border-radius: 3px;
            padding: 5px;
        }
        QListWidget::item {
            padding: 5px;
            border-bottom: 1px solid #3F3F46;
        }
        QListWidget::item:hover {
            background-color: #3E3E40;
        }
        """
    )
    window.mip_preview.itemClicked.connect(window.show_selected_mip)
    right_layout.addWidget(window.mip_preview)
    window.main_layout.addWidget(right_panel, 0)
