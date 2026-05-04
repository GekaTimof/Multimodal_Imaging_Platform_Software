#!/usr/bin/env python3
"""
Test script to verify UI fixes:
1. Start button becomes visible after camera stop
2. Parameter controls are properly disabled when auto modes are enabled
"""

import sys
import os
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Add parent directory to path for imports to work when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_start_stop_button_states():
    """Test that start/stop buttons toggle correctly"""
    try:
        from DesktopApp.threads.main_window_thread import MainWindow
        from DesktopApp.objects.Interface_text import Interface_text
        
        app = QApplication(sys.argv)
        
        print("Testing start/stop button states...")
        
        # Create main window
        main_window = MainWindow()
        camera_tab = main_window.camera_tab
        
        # Check initial button states
        print(f"Initial - Start enabled: {camera_tab.start_button.isEnabled()}")
        print(f"Initial - Stop enabled: {camera_tab.stop_button.isEnabled()}")
        
        # Start camera
        camera_tab.start_camera()
        app.processEvents()
        time.sleep(0.5)
        
        print(f"After start - Start enabled: {camera_tab.start_button.isEnabled()}")
        print(f"After start - Stop enabled: {camera_tab.stop_button.isEnabled()}")
        
        # Stop camera
        camera_tab.stop_camera()
        app.processEvents()
        time.sleep(0.5)
        
        print(f"After stop - Start enabled: {camera_tab.start_button.isEnabled()}")
        print(f"After stop - Stop enabled: {camera_tab.stop_button.isEnabled()}")
        
        # Verify correct states
        start_enabled_after_stop = camera_tab.start_button.isEnabled()
        stop_disabled_after_stop = not camera_tab.stop_button.isEnabled()
        
        main_window.close()
        
        if start_enabled_after_stop and stop_disabled_after_stop:
            print("SUCCESS: Start/stop button states work correctly")
            return True
        else:
            print("ERROR: Button states not correct")
            return False
            
    except Exception as e:
        print(f"ERROR: Button state test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_parameter_control_states():
    """Test that parameter controls are properly disabled when auto modes are enabled"""
    try:
        from DesktopApp.widgets.device_settings_widget.device_settings_widgets import CameraSettingsWidget
        
        app = QApplication(sys.argv)
        
        print("Testing parameter control states...")
        
        # Create widget
        widget = CameraSettingsWidget()
        
        # Test initial states (auto modes should be enabled by default)
        print(f"Initial AE checked: {widget.chk_ae.isChecked()}")
        print(f"Initial AWB checked: {widget.chk_awb.isChecked()}")
        print(f"Initial ExposureTime enabled: {widget.exp_time.isEnabled()}")
        print(f"Initial Gain enabled: {widget.gain.isEnabled()}")
        print(f"Initial ExposureValue enabled: {widget.exp_value.isEnabled()}")
        print(f"Initial RedGain enabled: {widget.red_gain.isEnabled()}")
        print(f"Initial BlueGain enabled: {widget.blue_gain.isEnabled()}")
        
        # Test with auto exposure enabled
        widget.chk_ae.setChecked(True)
        widget.chk_awb.setChecked(True)
        widget._update_control_states()
        
        ae_enabled_manual_disabled = not widget.exp_time.isEnabled()
        ae_enabled_gain_disabled = not widget.gain.isEnabled()
        ae_enabled_ev_enabled = widget.exp_value.isEnabled()
        
        print(f"AE enabled - ExposureTime enabled: {widget.exp_time.isEnabled()}")
        print(f"AE enabled - Gain enabled: {widget.gain.isEnabled()}")
        print(f"AE enabled - ExposureValue enabled: {widget.exp_value.isEnabled()}")
        
        # Test with auto exposure disabled
        widget.chk_ae.setChecked(False)
        widget._update_control_states()
        
        ae_disabled_manual_enabled = widget.exp_time.isEnabled()
        ae_disabled_gain_enabled = widget.gain.isEnabled()
        ae_disabled_ev_disabled = not widget.exp_value.isEnabled()
        
        print(f"AE disabled - ExposureTime enabled: {widget.exp_time.isEnabled()}")
        print(f"AE disabled - Gain enabled: {widget.gain.isEnabled()}")
        print(f"AE disabled - ExposureValue enabled: {widget.exp_value.isEnabled()}")
        
        # Test with auto white balance disabled
        widget.chk_awb.setChecked(False)
        widget._update_control_states()
        
        awb_disabled_red_enabled = widget.red_gain.isEnabled()
        awb_disabled_blue_enabled = widget.blue_gain.isEnabled()
        
        print(f"AWB disabled - RedGain enabled: {widget.red_gain.isEnabled()}")
        print(f"AWB disabled - BlueGain enabled: {widget.blue_gain.isEnabled()}")
        
        # Test with auto white balance enabled
        widget.chk_awb.setChecked(True)
        widget._update_control_states()
        
        awb_enabled_red_disabled = not widget.red_gain.isEnabled()
        awb_enabled_blue_disabled = not widget.blue_gain.isEnabled()
        
        print(f"AWB enabled - RedGain enabled: {widget.red_gain.isEnabled()}")
        print(f"AWB enabled - BlueGain enabled: {widget.blue_gain.isEnabled()}")
        
        widget.close()
        
        # Verify all states are correct
        checks = [
            ae_enabled_manual_disabled,
            ae_enabled_gain_disabled,
            ae_enabled_ev_enabled,
            ae_disabled_manual_enabled,
            ae_disabled_gain_enabled,
            ae_disabled_ev_disabled,
            awb_disabled_red_enabled,
            awb_disabled_blue_enabled,
            awb_enabled_red_disabled,
            awb_enabled_blue_disabled
        ]
        
        all_correct = all(checks)
        
        if all_correct:
            print("SUCCESS: Parameter control states work correctly")
            return True
        else:
            print(f"ERROR: Some control states incorrect: {checks}")
            return False
            
    except Exception as e:
        print(f"ERROR: Parameter control test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_settings_load_and_controls():
    """Test that loading settings properly updates control states"""
    try:
        from DesktopApp.widgets.device_settings_widget.device_settings_widgets import CameraSettingsWidget
        
        app = QApplication(sys.argv)
        
        print("Testing settings load and control states...")
        
        # Create widget
        widget = CameraSettingsWidget()
        
        # Simulate loading settings from database
        test_settings = {
            'AeEnable': False,  # Auto exposure disabled
            'AwbEnable': True,  # Auto white balance enabled
            'ExposureTime': 15000,
            'AnalogueGain': 2.0,
            'ExposureValue': 1.5,
            'RedGain': 1.2,
            'BlueGain': 1.1
        }
        
        # Update UI from settings
        widget._update_ui_from_settings(test_settings)
        
        # Check that controls are updated correctly
        ae_checked = widget.chk_ae.isChecked()
        awb_checked = widget.chk_awb.isChecked()
        exp_time_value = widget.exp_time.value()
        gain_value = widget.gain.value()
        
        # Check control states after settings load
        exp_time_enabled = widget.exp_time.isEnabled()
        gain_enabled = widget.gain.isEnabled()
        red_gain_enabled = widget.red_gain.isEnabled()
        blue_gain_enabled = widget.blue_gain.isEnabled()
        
        print(f"After settings load - AE checked: {ae_checked}")
        print(f"After settings load - AWB checked: {awb_checked}")
        print(f"After settings load - ExposureTime enabled: {exp_time_enabled}")
        print(f"After settings load - Gain enabled: {gain_enabled}")
        print(f"After settings load - RedGain enabled: {red_gain_enabled}")
        print(f"After settings load - BlueGain enabled: {blue_gain_enabled}")
        
        # Verify correct values and states
        values_correct = (
            not ae_checked and  # AE should be False
            awb_checked and     # AWB should be True
            exp_time_value == 15000 and
            gain_value == 2.0
        )
        
        states_correct = (
            exp_time_enabled and  # Manual controls enabled when AE disabled
            gain_enabled and
            not red_gain_enabled and  # Manual gains disabled when AWB enabled
            not blue_gain_enabled
        )
        
        widget.close()
        
        if values_correct and states_correct:
            print("SUCCESS: Settings load and control states work correctly")
            return True
        else:
            print(f"ERROR: Values correct: {values_correct}, States correct: {states_correct}")
            return False
            
    except Exception as e:
        print(f"ERROR: Settings load test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("Testing UI Fixes")
    print("=" * 30)
    
    tests = [
        ("Start/Stop Button States", test_start_stop_button_states),
        ("Parameter Control States", test_parameter_control_states),
        ("Settings Load and Controls", test_settings_load_and_controls),
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
    print("UI FIXES TEST SUMMARY:")
    print("=" * 30)
    
    passed = 0
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("All UI fixes are working correctly!")
        return True
    else:
        print("Some UI fixes need attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
