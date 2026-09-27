#!/usr/bin/env python3
"""
Desktop Application Entry Point
Main entry point for the Multimodal Imaging Platform desktop application.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QDialog

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def _show_connection_dialog(app: QApplication) -> bool:
    """
    Show the device-discovery dialog **before** heavy imports.

    Returns True if a device was selected (or the user chose to use the
    saved IP), False if the dialog was closed/cancelled.
    """
    # These lightweight imports do NOT trigger api_config-dependent modules
    from config import interface_config
    from config.api_config import get_saved_ip, reconfigure
    from config.theme_manager import ThemeManager
    from models.interface_text import Interface_text
    from ui.widgets.connection_dialog import ConnectionDialog

    # Apply theme so the dialog matches the app look
    theme_mgr = ThemeManager(interface_config)
    theme_mgr.apply_current_theme()

    default_language = interface_config.get('language.default', 'English')
    interface_text = Interface_text(default_language)

    saved_ip = get_saved_ip()

    dialog = ConnectionDialog(
        interface_text=interface_text,
        saved_ip=saved_ip,
        api_port=8000,
    )
    result = dialog.exec_()

    if result == QDialog.Accepted and dialog.selected_ip:
        reconfigure(dialog.selected_ip, api_port=str(dialog.selected_port))
        return True

    # User cancelled — fall through with whatever is already configured
    return saved_ip is not None


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)

    # Step 1: Show connection dialog (lightweight — no heavy module imports yet)
    if not _show_connection_dialog(app):
        # No device selected and no saved IP — exit gracefully
        sys.exit(0)

    # Step 2: Now import MainWindow (triggers api_config-dependent modules
    # which will read the already-reconfigured module-level URLs)
    from ui.main_window import MainWindow

    # Create and show main window
    # (MainWindow.__init__ shows the window immediately with a startup overlay,
    #  then defers heavy tab construction to the next event-loop tick)
    window = MainWindow()

    # Start application event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
