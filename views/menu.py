from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox


def setup_menu_bar(window):
    menubar = window.menuBar()

    file_menu = menubar.addMenu("&File")
    open_action = QAction("&Open...", window)
    open_action.setShortcut("Ctrl+O")
    open_action.triggered.connect(window.open_project_call)
    file_menu.addAction(open_action)

    save_action = QAction("&Save Project...", window)
    save_action.setShortcut("Ctrl+S")
    save_action.triggered.connect(window.save_project_call)
    file_menu.addAction(save_action)

    export_action = QAction("&Export...", window)
    export_action.setShortcut("Ctrl+E")
    export_action.triggered.connect(window.generate_mipmaps)
    file_menu.addAction(export_action)

    file_menu.addSeparator()
    exit_action = QAction("&Exit", window)
    exit_action.setShortcut("Ctrl+Q")
    exit_action.triggered.connect(window.close)
    file_menu.addAction(exit_action)

    edit_menu = menubar.addMenu("&Edit")
    copy_settings_action = QAction("&Copy Settings", window)
    copy_settings_action.triggered.connect(lambda: window.handle_mip_context_menu("copy", window.current_visible_mip))
    edit_menu.addAction(copy_settings_action)

    paste_settings_action = QAction("&Paste Settings", window)
    paste_settings_action.triggered.connect(lambda: window.handle_mip_context_menu("paste", window.current_visible_mip))
    edit_menu.addAction(paste_settings_action)

    help_menu = menubar.addMenu("&Help")
    about_action = QAction("&About", window)
    about_action.triggered.connect(lambda: show_about_dialog(window))
    help_menu.addAction(about_action)


def show_about_dialog(window):
    about_text = """
    <b>MipMaster</b><br><br>
    A tool for generating and editing mipmaps.<br><br>
    Version: 0.9<br>
    """
    QMessageBox.about(window, "About MipMaster", about_text)
