#!/usr/bin/env python3
"""
Final comprehensive test for all parameter fixes
"""

import sys
import os
import time
from PyQt5.QtWidgets import QApplication

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_startup_controls():
    """Test startup control states"""
    from DesktopApp.widgets.device_settings_widget.device_settings_widgets import CameraSettingsWidget
    
    app = QApplication([])
    
    widget = CameraSettingsWidget()
    
    # Auto modes should be enabled by default
    ae_checked = widget.chk_ae.isChecked()
    awb_checked = widget.chk_awb.isChecked()
    
    # Manual controls should be disabled when auto modes enabled
    manual_disabled = (
        not widget.exp_time.isEnabled() and
        not widget.gain.isEnabled() and
        widget.exp_value.isEnabled() and
        not widget.red_gain.isEnabled() and
        not widget.blue_gain.isEnabled()
    )
    
    widget.close()
    
    return ae_checked and awb_checked and manual_disabled

def test_database_updates():
    """Test database parameter updates"""
    from DesktopApp.widgets.device_settings_widget.device_settings_widgets import DeviceSettingsWidget
    
    app = QApplication([])
    
    device_widget = DeviceSettingsWidget()
    camera_widget = device_widget.camera_tab
    
    # Track signal
    signal_received = False
    def on_signal():
        nonlocal signal_received
        signal_received = True
    
    device_widget.settings_updated.connect(on_signal)
    
    # Change settings
    camera_widget.exp_time.setValue(50000)
    camera_widget.chk_ae.setChecked(False)
    
    # Apply settings
    camera_widget.apply_settings()
    
    # Process events
    for _ in range(20):
        app.processEvents()
        time.sleep(0.1)
    
    # Check database
    db_path = os.path.join('RaspberryPi', 'services')
    sys.path.insert(0, db_path)
    from database_service import db_service
    settings = db_service.get_camera_settings()
    
    device_widget.close()
    
    return (signal_received and 
            settings.get('ExposureTime') == 50000 and
            settings.get('AeEnable') == False)

def test_toggle_behavior():
    """Test control toggle behavior"""
    from DesktopApp.widgets.device_settings_widget.device_settings_widgets import CameraSettingsWidget
    
    app = QApplication([])
    
    widget = CameraSettingsWidget()
    
    # Test AE toggle
    widget.chk_ae.setChecked(True)
    app.processEvents()
    ae_enabled_correct = (
        not widget.exp_time.isEnabled() and
        not widget.gain.isEnabled() and
        widget.exp_value.isEnabled()
    )
    
    widget.chk_ae.setChecked(False)
    app.processEvents()
    ae_disabled_correct = (
        widget.exp_time.isEnabled() and
        widget.gain.isEnabled() and
        not widget.exp_value.isEnabled()
    )
    
    # Test AWB toggle
    widget.chk_awb.setChecked(True)
    app.processEvents()
    awb_enabled_correct = (
        not widget.red_gain.isEnabled() and
        not widget.blue_gain.isEnabled()
    )
    
    widget.chk_awb.setChecked(False)
    app.processEvents()
    awb_disabled_correct = (
        widget.red_gain.isEnabled() and
        widget.blue_gain.isEnabled()
    )
    
    widget.close()
    
    return (ae_enabled_correct and ae_disabled_correct and 
            awb_enabled_correct and awb_disabled_correct)

def main():
    print("Final Parameter Fixes Test")
    print("=" * 30)
    
    tests = [
        ("Startup Controls", test_startup_controls),
        ("Database Updates", test_database_updates),
        ("Toggle Behavior", test_toggle_behavior),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{name}:")
        print("-" * 20)
        
        try:
            success = test_func()
            results.append((name, success))
            print(f"{'PASS' if success else 'FAIL'}")
        except Exception as e:
            print(f"ERROR: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 30)
    print("FINAL RESULTS:")
    print("=" * 30)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        print(f"{name}: {'PASS' if success else 'FAIL'}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL PARAMETER FIXES WORKING CORRECTLY!")
        return True
    else:
        print("❌ Some fixes still need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
