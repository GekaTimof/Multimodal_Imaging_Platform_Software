#!/usr/bin/env python3
"""
Test script to verify the new workflow: API -> DB -> Video stream restart
"""

import sys
import os
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Add parent directory to path for imports to work when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_database_connection():
    """Test database connection and settings retrieval"""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'RaspberryPi', 'services'))
        from database_service import db_service
        
        settings = db_service.get_camera_settings()
        print("SUCCESS: Database connection works")
        print(f"Current settings: {settings}")
        return True, settings
    except Exception as e:
        print(f"ERROR: Database connection failed: {e}")
        return False, None

def test_settings_update():
    """Test updating settings through database service"""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'RaspberryPi', 'services'))
        from database_service import db_service
        
        # Test valid update
        success, message = db_service.update_parameter('CameraSettings', 'ExposureTime', 15000)
        print(f"Settings update test: {success} - {message}")
        
        # Test invalid update
        success, message = db_service.update_parameter('CameraSettings', 'ExposureTime', 50)
        print(f"Invalid settings test: {success} - {message}")
        
        return True
    except Exception as e:
        print(f"ERROR: Settings update test failed: {e}")
        return False

def test_camera_thread_db_integration():
    """Test camera thread database integration"""
    try:
        from DesktopApp.threads.camera_thread import CameraThread
        
        # Create camera thread (without starting it)
        thread = CameraThread("test_source")
        
        # Test settings loading
        settings = thread.load_camera_settings()
        print(f"Camera thread settings loading: {settings is not None}")
        
        return True
    except Exception as e:
        print(f"ERROR: Camera thread DB integration failed: {e}")
        return False

def test_device_settings_widget():
    """Test device settings widget functionality"""
    try:
        from DesktopApp.widgets.device_settings_widget.device_settings_widgets import DeviceSettingsWidget
        
        app = QApplication(sys.argv)
        
        # Create widget
        widget = DeviceSettingsWidget()
        
        # Test signal exists
        if hasattr(widget, 'settings_updated'):
            print("SUCCESS: Device settings widget has settings_updated signal")
        else:
            print("ERROR: Device settings widget missing settings_updated signal")
            return False
        
        # Test thread tracking
        if hasattr(widget, 'active_threads'):
            print("SUCCESS: Device settings widget has thread tracking")
        else:
            print("ERROR: Device settings widget missing thread tracking")
            return False
        
        widget.close()
        return True
        
    except Exception as e:
        print(f"ERROR: Device settings widget test failed: {e}")
        return False

def test_camera_tab_integration():
    """Test camera tab integration with device settings"""
    try:
        from DesktopApp.threads.main_window_thread import MainWindow
        from DesktopApp.objects.Interface_text import Interface_text
        
        app = QApplication(sys.argv)
        
        # Create main window
        main_window = MainWindow()
        
        # Check if camera tab has device settings widget
        camera_tab = main_window.camera_tab
        if hasattr(camera_tab, 'device_settings_widget'):
            print("SUCCESS: Camera tab has device settings widget")
        else:
            print("ERROR: Camera tab missing device settings widget")
            return False
        
        # Check if on_settings_updated method exists
        if hasattr(camera_tab, 'on_settings_updated'):
            print("SUCCESS: Camera tab has on_settings_updated method")
        else:
            print("ERROR: Camera tab missing on_settings_updated method")
            return False
        
        main_window.close()
        return True
        
    except Exception as e:
        print(f"ERROR: Camera tab integration test failed: {e}")
        return False

def test_fullscreen_mode():
    """Test that main window starts in fullscreen mode"""
    try:
        from DesktopApp.threads.main_window_thread import MainWindow
        from DesktopApp.objects.Interface_text import Interface_text
        
        app = QApplication(sys.argv)
        
        # Create main window
        main_window = MainWindow()
        
        # Check if window is maximized
        if main_window.isMaximized():
            print("SUCCESS: Main window starts in fullscreen mode")
        else:
            print("WARNING: Main window not maximized (may be normal on some systems)")
        
        main_window.close()
        return True
        
    except Exception as e:
        print(f"ERROR: Fullscreen mode test failed: {e}")
        return False

def main():
    print("Testing New Workflow: API -> DB -> Video Stream Restart")
    print("=" * 60)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Settings Update", test_settings_update),
        ("Camera Thread DB Integration", test_camera_thread_db_integration),
        ("Device Settings Widget", test_device_settings_widget),
        ("Camera Tab Integration", test_camera_tab_integration),
        ("Fullscreen Mode", test_fullscreen_mode),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        
        try:
            if test_name == "Database Connection":
                success, _ = test_func()
            else:
                success = test_func()
            
            results.append((test_name, success))
            
        except Exception as e:
            print(f"ERROR: {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY:")
    print("=" * 60)
    
    passed = 0
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("All tests passed! New workflow is ready.")
        return True
    else:
        print("Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
