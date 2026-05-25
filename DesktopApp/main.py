#!/usr/bin/env python3
"""
Desktop Application Entry Point
Main entry point for the Multimodal Imaging Platform desktop application.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.main_window import MainWindow


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start application event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
