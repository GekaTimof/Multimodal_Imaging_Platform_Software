#!/usr/bin/env python3
"""
Desktop Application Entry Point
Main entry point for the Multimodal Imaging Platform desktop application.
"""

import sys
import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication

os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def main():
    """Main application entry point."""
    from config import interface_config
    from ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setFont(QFont(
        interface_config.get('ui_scaling.font_family', 'DejaVu Sans'),
        interface_config.get('ui_scaling.font_point_size', 11)
    ))
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start application event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
