#!/usr/bin/env python3
"""
Test script to verify DesktopApp can start properly
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Add parent directory to path for imports to work when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test all critical imports"""
    try:
        from DesktopApp.threads.main_window_thread import MainWindow
        print("SUCCESS: MainWindow import works")
        return True
    except Exception as e:
        print(f"ERROR: MainWindow import failed: {e}")
        return False

def test_widget_imports():
    """Test widget imports"""
    try:
        from DesktopApp.widgets.device_settings_widget.device_settings_widgets import DeviceSettingsWidget
        print("SUCCESS: DeviceSettingsWidget import works")
        return True
    except Exception as e:
        print(f"ERROR: DeviceSettingsWidget import failed: {e}")
        return False

def test_app_creation():
    """Test QApplication creation and MainWindow instantiation"""
    try:
        app = QApplication(sys.argv)
        
        from DesktopApp.threads.main_window_thread import MainWindow
        win = MainWindow()
        
        print("SUCCESS: QApplication and MainWindow created")
        
        # Schedule app to quit after 2 seconds to test startup
        QTimer.singleShot(2000, app.quit)
        
        # Run the event loop
        app.exec_()
        
        print("SUCCESS: Application ran and closed cleanly")
        return True
        
    except Exception as e:
        print(f"ERROR: Application creation failed: {e}")
        return False

def main():
    print("Testing DesktopApp startup...")
    print("=" * 50)
    
    # Test 1: Basic imports
    print("1. Testing imports...")
    if not test_imports():
        return False
    
    if not test_widget_imports():
        return False
    
    # Test 2: Application creation
    print("\n2. Testing application creation...")
    if not test_app_creation():
        return False
    
    print("\nAll tests passed! DesktopApp should start correctly.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
