#!/usr/bin/env python3
"""
Test script to verify parameter fixes:
1. Parameter controls disabled on startup when auto modes enabled
2. Database parameter updates working correctly
"""

import sys
import os
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Add parent directory to path for imports to work when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_startup_control_states():
    """Test that parameter controls are properly disabled on startup"""
    try:
        from DesktopApp.widgets.device_settings_widget.device_settings_widgets import CameraSettingsWidget
        
        app = QApplication(sys.argv)
        
        print("Testing startup control states...")
        
        # Create widget (this should initialize with auto modes enabled)
        widget = CameraSettingsWidget()
        
        # Check initial states (should be auto modes enabled by default)
        ae_checked = widget.chk_ae.isChecked()
        awb_checked = widget.chk_awb.isChecked()
        
        print(f"Startup - AE checked: {ae_checked}")
        print(f"Startup - AWB checked: {awb_checked}")
        print(f"Startup - ExposureTime enabled: {widget.exp_time.isEnabled()}")
        print(f"Startup - Gain enabled: {widget.gain.isEnabled()}")
        print(f"Startup - ExposureValue enabled: {widget.exp_value.isEnabled()}")
        print(f"Startup - RedGain enabled: {widget.red_gain.isEnabled()}")
        print(f"Startup - BlueGain enabled: {widget.blue_gain.isEnabled()}")
        
        # Verify correct initial states
        if ae_checked and awb_checked:
            # Auto modes enabled, manual controls should be disabled
            manual_controls_disabled = (
                not widget.exp_time.isEnabled() and
                not widget.gain.isEnabled() and
                widget.exp_value.isEnabled() and
                not widget.red_gain.isEnabled() and
                not widget.blue_gain.isEnabled()
            )
            
            if manual_controls_disabled:
                print("SUCCESS: Startup control states are correct")
                result = True
            else:
                print("ERROR: Manual controls should be disabled when auto modes enabled")
                result = False
        else:
            print("ERROR: Auto modes should be enabled by default")
            result = False
        
        widget.close()
        return result
        
    except Exception as e:
        print(f"ERROR: Startup control test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_parameter_updates():
    """Test that database parameter updates work correctly"""
    try:
        from DesktopApp.widgets.device_settings_widget.device_settings_widgets import DeviceSettingsWidget
        
        app = QApplication(sys.argv)
        
        print("Testing database parameter updates...")
        
        # Create device settings widget (this contains the camera widget)
        device_widget = DeviceSettingsWidget()
        camera_widget = device_widget.camera_tab
        
        # Connect signal to track updates
        signal_received = False
        
        def on_settings_updated():
            nonlocal signal_received
            signal_received = True
            print("Settings updated signal received!")
        
        device_widget.settings_updated.connect(on_settings_updated)
        
        # Modify some settings
        original_exposure = camera_widget.exp_time.value()
        new_exposure = 25000
        camera_widget.exp_time.setValue(new_exposure)
        
        original_ae = camera_widget.chk_ae.isChecked()
        camera_widget.chk_ae.setChecked(False)  # Disable auto exposure
        
        print(f"Before update - ExposureTime: {original_exposure}, AE: {original_ae}")
        print(f"After change - ExposureTime: {camera_widget.exp_time.value()}, AE: {camera_widget.chk_ae.isChecked()}")
        
        # Apply settings (this should trigger database update)
        print("Applying settings...")
        camera_widget.apply_settings()
        
        # Wait for async operations to complete
        app.processEvents()
        time.sleep(2)  # Wait for database operations
        app.processEvents()
        
        # Check if signal was received
        print(f"Signal received: {signal_received}")
        
        # Verify database was actually updated
        try:
            db_path = os.path.join('RaspberryPi', 'services')
            sys.path.insert(0, db_path)
            
            from database_service import db_service
            settings = db_service.get_camera_settings()
            
            print(f"Database - ExposureTime: {settings.get('ExposureTime')}")
            print(f"Database - AeEnable: {settings.get('AeEnable')}")
            
            # Check if values match what we set
            exposure_updated = settings.get('ExposureTime') == new_exposure
            ae_updated = settings.get('AeEnable') == False
            
            if exposure_updated and ae_updated:
                print("SUCCESS: Database parameter updates work correctly")
                result = True
            else:
                print(f"ERROR: Database not updated correctly - Exposure: {exposure_updated}, AE: {ae_updated}")
                result = False
                
        except Exception as e:
            print(f"ERROR: Database verification failed: {e}")
            result = False
        
        device_widget.close()
        return result and signal_received
        
    except Exception as e:
        print(f"ERROR: Database update test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_control_toggle_behavior():
    """Test that toggling controls properly enables/disables related parameters"""
    try:
        from DesktopApp.widgets.device_settings_widget.device_settings_widgets import CameraSettingsWidget
        
        app = QApplication(sys.argv)
        
        print("Testing control toggle behavior...")
        
        # Create widget
        widget = CameraSettingsWidget()
        
        # Test toggling auto exposure
        print("Testing auto exposure toggle...")
        
        # Start with AE enabled
        widget.chk_ae.setChecked(True)
        app.processEvents()
        
        ae_enabled_manual_disabled = (
            not widget.exp_time.isEnabled() and
            not widget.gain.isEnabled() and
            widget.exp_value.isEnabled()
        )
        
        print(f"AE enabled - Manual disabled: {ae_enabled_manual_disabled}")
        
        # Disable AE
        widget.chk_ae.setChecked(False)
        app.processEvents()
        
        ae_disabled_manual_enabled = (
            widget.exp_time.isEnabled() and
            widget.gain.isEnabled() and
            not widget.exp_value.isEnabled()
        )
        
        print(f"AE disabled - Manual enabled: {ae_disabled_manual_enabled}")
        
        # Test toggling auto white balance
        print("Testing auto white balance toggle...")
        
        # Start with AWB enabled
        widget.chk_awb.setChecked(True)
        app.processEvents()
        
        awb_enabled_gains_disabled = (
            not widget.red_gain.isEnabled() and
            not widget.blue_gain.isEnabled()
        )
        
        print(f"AWB enabled - Gains disabled: {awb_enabled_gains_disabled}")
        
        # Disable AWB
        widget.chk_awb.setChecked(False)
        app.processEvents()
        
        awb_disabled_gains_enabled = (
            widget.red_gain.isEnabled() and
            widget.blue_gain.isEnabled()
        )
        
        print(f"AWB disabled - Gains enabled: {awb_disabled_gains_enabled}")
        
        widget.close()
        
        # Verify all toggle behaviors work
        all_correct = (
            ae_enabled_manual_disabled and
            ae_disabled_manual_enabled and
            awb_enabled_gains_disabled and
            awb_disabled_gains_enabled
        )
        
        if all_correct:
            print("SUCCESS: Control toggle behavior works correctly")
            return True
        else:
            print("ERROR: Control toggle behavior has issues")
            return False
            
    except Exception as e:
        print(f"ERROR: Toggle behavior test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("Testing Parameter Fixes")
    print("=" * 30)
    
    tests = [
        ("Startup Control States", test_startup_control_states),
        ("Database Parameter Updates", test_database_parameter_updates),
        ("Control Toggle Behavior", test_control_toggle_behavior),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 25)
        
        try:
            success = test_func()
            results.append((test_name, success))
            
        except Exception as e:
            print(f"ERROR: {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 30)
    print("PARAMETER FIXES TEST SUMMARY:")
    print("=" * 30)
    
    passed = 0
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("All parameter fixes are working correctly!")
        return True
    else:
        print("Some parameter fixes need attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
