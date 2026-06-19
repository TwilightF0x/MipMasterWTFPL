from PySide6.QtCore import QPointF, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
)


class ZoomableImageView(QGraphicsView):
    channel_toggled = Signal(str, bool)
    background_mode_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self._background_mode = "solid"
        self.setBackgroundBrush(self._generate_solid_color())

        self.image_item = QGraphicsPixmapItem()
        self.scene().addItem(self.image_item)
        self._min_scale = 1e-6
        self._max_scale = 1e6
        self._setup_overlay_controls()
        self._position_overlay_controls()

    def _setup_overlay_controls(self):
        self.overlay_controls = QFrame(self.viewport())
        self.overlay_controls.setObjectName("previewOverlay")
        self.overlay_controls.setStyleSheet(
            """
            #previewOverlay {
                background-color: rgba(30, 30, 30, 185);
                border: 1px solid rgba(80, 80, 80, 180);
                border-radius: 6px;
            }
            #previewOverlay QLabel, #previewOverlay QCheckBox, #previewOverlay QComboBox {
                color: #e8e8e8;
                font-size: 10px;
            }
            #previewOverlay QComboBox {
                padding: 1px 4px;
                min-height: 18px;
            }
            """
        )

        layout = QHBoxLayout(self.overlay_controls)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)

        self.channel_preview_r = QCheckBox("R")
        self.channel_preview_g = QCheckBox("G")
        self.channel_preview_b = QCheckBox("B")
        self.channel_preview_a = QCheckBox("A")

        self.channel_preview_r.setChecked(True)
        self.channel_preview_g.setChecked(True)
        self.channel_preview_b.setChecked(True)
        self.channel_preview_a.setChecked(True)

        self.channel_preview_r.toggled.connect(lambda checked: self.channel_toggled.emit("r", checked))
        self.channel_preview_g.toggled.connect(lambda checked: self.channel_toggled.emit("g", checked))
        self.channel_preview_b.toggled.connect(lambda checked: self.channel_toggled.emit("b", checked))
        self.channel_preview_a.toggled.connect(lambda checked: self.channel_toggled.emit("a", checked))

        self.background_mode_combo = QComboBox()
        self.background_mode_combo.addItem("Solid", "solid")
        self.background_mode_combo.addItem("Checker", "checkerboard")
        self.background_mode_combo.currentIndexChanged.connect(self._emit_background_mode)

        layout.addWidget(QLabel("RGBA"))
        layout.addWidget(self.channel_preview_r)
        layout.addWidget(self.channel_preview_g)
        layout.addWidget(self.channel_preview_b)
        layout.addWidget(self.channel_preview_a)
        layout.addWidget(QLabel("BG"))
        layout.addWidget(self.background_mode_combo)

        self.overlay_controls.adjustSize()
        self.overlay_controls.show()

    def _emit_background_mode(self):
        mode = self.background_mode_combo.currentData()
        self.background_mode_changed.emit(mode)

    def _position_overlay_controls(self):
        if not hasattr(self, "overlay_controls"):
            return
        margin = 8
        self.overlay_controls.adjustSize()
        ow = self.overlay_controls.width()
        self.overlay_controls.move(max(margin, self.viewport().width() - ow - margin), margin)
        self.overlay_controls.raise_()

    def _schedule_overlay_reposition(self):
        self._position_overlay_controls()
        QTimer.singleShot(0, self._position_overlay_controls)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._schedule_overlay_reposition()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.fitInView(self.image_item, Qt.KeepAspectRatio)
            event.accept()
        elif event.button() == Qt.RightButton:
            self.resetTransform()
            event.accept()

    def _fit_scale_for_size(self, width, height):
        viewport_rect = self.viewport().rect()
        view_w = max(1, viewport_rect.width())
        view_h = max(1, viewport_rect.height())
        img_w = max(1, width)
        img_h = max(1, height)
        return min(view_w / img_w, view_h / img_h)

    def _clamp_scale(self, value):
        return max(self._min_scale, min(self._max_scale, value))

    def set_image(self, img, preserve_view=False, preserve_relative_zoom=False):
        had_image = not self.image_item.pixmap().isNull()
        previous_pixmap = self.image_item.pixmap()
        previous_center = self.mapToScene(self.viewport().rect().center()) if had_image else None
        previous_scale = self.transform().m11() if had_image else 1.0

        if isinstance(img, QPixmap):
            pixmap = img
        else:
            qimage = self._pil2qimage(img)
            pixmap = QPixmap.fromImage(qimage)

        self.image_item.setPixmap(pixmap)
        self.setSceneRect(pixmap.rect())

        if preserve_relative_zoom and had_image and previous_center is not None:
            old_w = max(1, previous_pixmap.width())
            old_h = max(1, previous_pixmap.height())
            new_w = max(1, pixmap.width())
            new_h = max(1, pixmap.height())

            old_fit_scale = self._fit_scale_for_size(old_w, old_h)
            relative_zoom = previous_scale / max(old_fit_scale, 1e-9)

            # Keep center in normalized scene coordinates without hard clamping to avoid drift.
            nx = previous_center.x() / old_w
            ny = previous_center.y() / old_h
            new_center = QPointF(nx * new_w, ny * new_h)

            new_fit_scale = self._fit_scale_for_size(new_w, new_h)
            target_scale = max(new_fit_scale * relative_zoom, self._min_scale)

            self.resetTransform()
            self.scale(target_scale, target_scale)
            self.centerOn(new_center)
            self._schedule_overlay_reposition()
            return

        if preserve_view and had_image and previous_center is not None:
            self.centerOn(previous_center)
            self._schedule_overlay_reposition()
            return

        self.fitInView(self.image_item, Qt.KeepAspectRatio)
        self._schedule_overlay_reposition()

    def set_overlay_channel_state(self, show_r, show_g, show_b, show_a):
        state_map = [
            (self.channel_preview_r, show_r),
            (self.channel_preview_g, show_g),
            (self.channel_preview_b, show_b),
            (self.channel_preview_a, show_a),
        ]
        for checkbox, value in state_map:
            checkbox.blockSignals(True)
            checkbox.setChecked(value)
            checkbox.blockSignals(False)

    def set_background_mode(self, mode):
        self._background_mode = mode
        if mode == "checkerboard":
            self.setBackgroundBrush(self._generate_checkerboard())
        else:
            self.setBackgroundBrush(self._generate_solid_color())

        index = self.background_mode_combo.findData(mode)
        if index >= 0 and self.background_mode_combo.currentIndex() != index:
            self.background_mode_combo.blockSignals(True)
            self.background_mode_combo.setCurrentIndex(index)
            self.background_mode_combo.blockSignals(False)

    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 0.8
        factor = zoom_in_factor if event.angleDelta().y() > 0 else zoom_out_factor
        target = self._clamp_scale(self.transform().m11() * factor)
        step = target / max(self.transform().m11(), 1e-9)
        self.scale(step, step)
        self._schedule_overlay_reposition()

    def scrollContentsBy(self, dx, dy):
        super().scrollContentsBy(dx, dy)
        self._position_overlay_controls()

    def _pil2qimage(self, pil_image):
        rgba = pil_image.convert("RGBA").tobytes("raw", "RGBA")
        return QImage(rgba, pil_image.width, pil_image.height, QImage.Format_RGBA8888)

    def _generate_checkerboard(self, size=16):
        img = QImage(size * 2, size * 2, QImage.Format_RGB32)
        painter = QPainter(img)
        painter.fillRect(0, 0, size * 2, size * 2, QColor(70, 70, 70))
        painter.fillRect(0, 0, size, size, QColor(50, 50, 50))
        painter.fillRect(size, size, size, size, QColor(50, 50, 50))
        painter.end()
        return QBrush(QPixmap.fromImage(img))

    def _generate_solid_color(self, color = QColor(50, 50, 50)):
        img = QImage(1, 1, QImage.Format_RGB32)
        painter = QPainter(img)
        painter.fillRect(0, 0, 1, 1, color)
        painter.end()
        return QBrush(QPixmap.fromImage(img))