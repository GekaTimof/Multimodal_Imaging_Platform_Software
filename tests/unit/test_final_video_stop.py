#!/usr/bin/env python3
"""
Final test to verify video stop functionality works in the complete DesktopApp
"""

import sys
import os
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Add parent directory to path for imports to work when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_desktopapp_video_stop():
    """Test video stop functionality in the full DesktopApp"""
    try:
        from DesktopApp.threads.main_window_thread import MainWindow
        from DesktopApp.objects.Interface_text import Interface_text
        
        app = QApplication(sys.argv)
        
        print("Testing DesktopApp video stop functionality...")
        
        # Create main window
        main_window = MainWindow()
        camera_tab = main_window.camera_tab
        
        print("Main window created successfully")
        
        # Test camera thread creation and stopping
        print("Testing camera thread lifecycle...")
        
        # Start camera (this will create the thread)
        camera_tab.start_camera()
        
        # Wait for thread to start
        app.processEvents()
        time.sleep(0.5)
        
        if camera_tab.thread and camera_tab.thread.isRunning():
            print("SUCCESS: Camera thread started")
        else:
            print("ERROR: Camera thread failed to start")
            return False
        
        # Stop camera
        print("Stopping camera...")
        start_time = time.time()
        camera_tab.stop_camera()
        
        # Wait for thread to finish
        if camera_tab.thread:
            camera_tab.thread.wait(5000)
        
        end_time = time.time()
        stop_duration = end_time - start_time
        
        print(f"Camera stopped in {stop_duration:.2f} seconds")
        
        # Verify thread is stopped
        if camera_tab.thread is None or not camera_tab.thread.isRunning():
            print("SUCCESS: Camera thread stopped cleanly")
            success = True
        else:
            print("ERROR: Camera thread still running")
            success = False
        
        # Test multiple start/stop cycles
        print("Testing multiple start/stop cycles...")
        for i in range(3):
            print(f"Cycle {i+1}:")
            camera_tab.start_camera()
            time.sleep(0.2)
            camera_tab.stop_camera()
            time.sleep(0.2)
            
            if camera_tab.thread and camera_tab.thread.isRunning():
                print(f"ERROR: Thread still running after cycle {i+1}")
                success = False
                break
        
        if success:
            print("SUCCESS: Multiple start/stop cycles work")
        
        main_window.close()
        return success
        
    except Exception as e:
        print(f"ERROR: DesktopApp test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("Final Video Stop Test")
    print("=" * 30)
    
    success = test_desktopapp_video_stop()
    
    print("\n" + "=" * 30)
    if success:
        print("FINAL RESULT: ✅ Video stop functionality is FIXED!")
        print("The application should now stop video without hanging.")
    else:
        print("FINAL RESULT: ❌ Video stop functionality still has issues.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
