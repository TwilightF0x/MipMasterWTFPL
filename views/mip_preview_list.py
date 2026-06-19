from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QListWidget, QMenu


class HoverSelectableMipList(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.mouse_pressed = False
        self._last_hover_row = -1
        self.on_hover_select = None
        self.context_menu_callback = None

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mouse_pressed = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mouse_pressed = False
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self.mouse_pressed and self.on_hover_select:
            item = self.itemAt(event.pos())
            if item:
                row = self.row(item)
                if row != self._last_hover_row:
                    self._last_hover_row = row
                    self.on_hover_select(item)
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._last_hover_row = -1
        super().leaveEvent(event)

    def show_context_menu(self, pos):
        item = self.itemAt(pos)
        if not item or not self.context_menu_callback:
            return

        index = self.row(item)
        menu = QMenu(self)
        copy_action = QAction("Copy Settings", self)
        paste_action = QAction("Paste Settings", self)

        copy_action.triggered.connect(lambda: self.context_menu_callback("copy", index))
        paste_action.triggered.connect(lambda: self.context_menu_callback("paste", index))

        menu.addAction(copy_action)
        menu.addAction(paste_action)
        menu.exec(self.viewport().mapToGlobal(pos))
