#!/usr/bin/env python3
"""
Debug database update issue
"""

import sys
import os
import time

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_direct_database_update():
    """Test database update directly"""
    try:
        # Test database service directly
        db_path = os.path.join('RaspberryPi', 'services')
        sys.path.insert(0, db_path)
        
        from database_service import db_service
        
        print("Testing direct database update...")
        
        # Update a parameter
        success, message = db_service.update_parameter('CameraSettings', 'ExposureTime', '35000')
        print(f"Direct update result: {success} - {message}")
        
        # Check result
        settings = db_service.get_camera_settings()
        print(f"Database after update: {settings.get('ExposureTime')}")
        
        return success
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_widget_database_update():
    """Test database update through widget"""
    try:
        from PyQt5.QtWidgets import QApplication
        from DesktopApp.widgets.device_settings_widget.device_settings_widgets import DeviceSettingsWidget
        
        app = QApplication([])
        
        print("Testing widget database update...")
        
        # Create widget
        device_widget = DeviceSettingsWidget()
        camera_widget = device_widget.camera_tab
        
        # Connect to signal
        signal_received = False
        def on_signal():
            nonlocal signal_received
            signal_received = True
            print("Signal received!")
        
        device_widget.settings_updated.connect(on_signal)
        
        # Change setting
        camera_widget.exp_time.setValue(40000)
        print(f"Set ExposureTime to: {camera_widget.exp_time.value()}")
        
        # Apply settings
        print("Applying settings...")
        camera_widget.apply_settings()
        
        # Process events
        for i in range(20):
            app.processEvents()
            time.sleep(0.1)
        
        print(f"Signal received: {signal_received}")
        
        # Check database
        settings = None
        try:
            from database_service import db_service
            settings = db_service.get_camera_settings()
            print(f"Database ExposureTime: {settings.get('ExposureTime')}")
        except Exception as e:
            print(f"Error checking database: {e}")
        
        device_widget.close()
        
        return signal_received and (settings and settings.get('ExposureTime') == 40000)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Debug Database Update")
    print("=" * 25)
    
    print("\n1. Direct database test:")
    direct_ok = test_direct_database_update()
    
    print("\n2. Widget database test:")
    widget_ok = test_widget_database_update()
    
    print(f"\nResults: Direct={direct_ok}, Widget={widget_ok}")
    
    if direct_ok and not widget_ok:
        print("ISSUE: Widget database update not working")
    elif direct_ok and widget_ok:
        print("SUCCESS: Both direct and widget updates work")
    else:
        print("ISSUE: Even direct database update not working")
