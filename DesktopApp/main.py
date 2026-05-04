"""
Multimodal Imaging Platform - Desktop Application
Main entry point for the desktop application.

This application provides a GUI for controlling spectrometer and camera devices,
with support for multiple languages and configurable settings.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication

# Add parent directory to path for imports to work when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from DesktopApp.threads.main_window_thread import MainWindow


def main():
    """Initialize and run the desktop application."""
    # Create Qt application instance
    app = QApplication(sys.argv)
    
    # Create and show main window
    win = MainWindow()
    win.show()
    
    # Start the application event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()