from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QApplication
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation


class AchievementToast(QWidget):
    def __init__(self, message: str, icon_path: str = None, duration_ms=8000, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.SubWindow | Qt.FramelessWindowHint)
        # self.setAttribute(Qt.WA_TranslucentBackground)

        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim.setDuration(500)

        self.init_ui(message, icon_path)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.fade_out)
        self.timer.setSingleShot(True)
        self.timer.start(duration_ms)

        self.fade_in()

    def init_ui(self, message, icon_path):
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        if icon_path:
            pixmap = QPixmap(icon_path).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label = QLabel()
            icon_label.setPixmap(pixmap)
            layout.addWidget(icon_label)

        message_label = QLabel(message)
        message_label.setStyleSheet("color: white; font-weight: bold;")
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(message_label)

        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(40, 40, 40, 240);
                border-radius: 8px;
            }
        """)
        self.adjustSize()

    def move_to_corner(self):
        if self.parent():
            parent_geom = self.parent().geometry()
            x = parent_geom.x() + parent_geom.width() - self.width() - 20
            y = parent_geom.y() + parent_geom.height() - self.height() - 20
            self.move(x, y)
        else:
            screen = QApplication.primaryScreen().availableGeometry()
            self.move(screen.width() - self.width() - 20,
                    screen.height() - self.height() - 20)

    def fade_in(self):
        self.setWindowOpacity(0.0)
        self.show()
        self.move_to_corner()
        self.opacity_anim.stop()
        self.opacity_anim.setStartValue(0.0)
        self.opacity_anim.setEndValue(1.0)
        self.opacity_anim.start()

    def fade_out(self):
        self.opacity_anim.stop()
        self.opacity_anim.setStartValue(1.0)
        self.opacity_anim.setEndValue(0.0)
        self.opacity_anim.finished.connect(self.close)
        self.opacity_anim.start()
