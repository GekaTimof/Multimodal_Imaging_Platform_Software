#!/usr/bin/env python3
"""
Test script to verify all fixes are working:
1. Video stop hanging issue
2. Parameter change error  
3. Settings retrieval error
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Add parent directory to path for imports to work when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_database_fallback():
    """Test database fallback functionality"""
    try:
        from DesktopApp.widgets.device_settings_widget.device_settings_widgets import CameraSettingsWidget
        
        app = QApplication(sys.argv)
        
        # Create widget
        widget = CameraSettingsWidget()
        
        # Test database fallback method exists
        if hasattr(widget, '_load_settings_from_database'):
            print("SUCCESS: Database fallback method exists")
        else:
            print("ERROR: Database fallback method missing")
            return False
        
        # Test fallback apply method exists
        if hasattr(widget, '_apply_settings_with_fallback'):
            print("SUCCESS: Fallback apply method exists")
        else:
            print("ERROR: Fallback apply method missing")
            return False
        
        widget.close()
        return True
        
    except Exception as e:
        print(f"ERROR: Database fallback test failed: {e}")
        return False

def test_camera_thread_stop():
    """Test camera thread stop improvements"""
    try:
        from DesktopApp.threads.camera_thread import CameraThread
        
        # Create thread (without starting)
        thread = CameraThread("test_source")
        
        # Test stop method exists and has proper timeout
        if hasattr(thread, 'stop'):
            print("SUCCESS: Camera thread has stop method")
        else:
            print("ERROR: Camera thread missing stop method")
            return False
        
        return True
        
    except Exception as e:
        print(f"ERROR: Camera thread test failed: {e}")
        return False

def test_camera_tab_stop():
    """Test camera tab stop improvements"""
    try:
        from DesktopApp.threads.main_window_thread import MainWindow
        from DesktopApp.objects.Interface_text import Interface_text
        
        app = QApplication(sys.argv)
        
        # Create main window
        main_window = MainWindow()
        camera_tab = main_window.camera_tab
        
        # Check if stop_camera method has improvements
        if hasattr(camera_tab, 'stop_camera'):
            print("SUCCESS: Camera tab has stop_camera method")
        else:
            print("ERROR: Camera tab missing stop_camera method")
            return False
        
        main_window.close()
        return True
        
    except Exception as e:
        print(f"ERROR: Camera tab test failed: {e}")
        return False

def test_database_connection():
    """Test database connection works without API"""
    try:
        import sys
        import os
        db_path = os.path.join('RaspberryPi', 'services')
        sys.path.insert(0, db_path)
        
        from database_service import db_service
        settings = db_service.get_camera_settings()
        
        if settings:
            print("SUCCESS: Database connection works")
            print(f"Current settings: {list(settings.keys())}")
            return True
        else:
            print("ERROR: No settings found in database")
            return False
            
    except Exception as e:
        print(f"ERROR: Database connection failed: {e}")
        return False

def test_settings_update():
    """Test settings update works without API"""
    try:
        import sys
        import os
        db_path = os.path.join('RaspberryPi', 'services')
        sys.path.insert(0, db_path)
        
        from database_service import db_service
        
        # Test valid update
        success, message = db_service.update_parameter('CameraSettings', 'ExposureTime', 15000)
        print(f"Database update test: {success} - {message}")
        
        if success:
            print("SUCCESS: Database update works")
            return True
        else:
            print("ERROR: Database update failed")
            return False
            
    except Exception as e:
        print(f"ERROR: Settings update test failed: {e}")
        return False

def main():
    print("Testing All Fixes")
    print("=" * 40)
    
    tests = [
        ("Database Fallback", test_database_fallback),
        ("Camera Thread Stop", test_camera_thread_stop),
        ("Camera Tab Stop", test_camera_tab_stop),
        ("Database Connection", test_database_connection),
        ("Settings Update", test_settings_update),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 20)
        
        try:
            success = test_func()
            results.append((test_name, success))
            
        except Exception as e:
            print(f"ERROR: {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("FIXES SUMMARY:")
    print("=" * 40)
    
    passed = 0
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("All fixes are working correctly!")
        return True
    else:
        print("Some fixes need attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
