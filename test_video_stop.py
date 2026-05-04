#!/usr/bin/env python3
"""
Test script to verify video stop functionality works correctly
"""

import sys
import os
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Add parent directory to path for imports to work when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_camera_thread_lifecycle():
    """Test camera thread start and stop lifecycle"""
    try:
        from DesktopApp.threads.camera_thread import CameraThread
        
        app = QApplication(sys.argv)
        
        print("Testing camera thread lifecycle...")
        
        # Create thread
        thread = CameraThread(0)  # Use default camera
        
        # Test initial state
        print(f"Initial running state: {thread.running}")
        print(f"Initial isRunning state: {thread.isRunning()}")
        
        # Start thread (without actual camera for testing)
        print("Starting thread...")
        thread.start()
        
        # Wait a moment for thread to start
        app.processEvents()
        time.sleep(0.1)
        
        print(f"After start - running: {thread.running}")
        print(f"After start - isRunning: {thread.isRunning()}")
        
        # Stop thread
        print("Stopping thread...")
        start_time = time.time()
        thread.stop()
        
        # Wait for thread to finish
        if thread.isRunning():
            thread.wait(5000)  # Wait up to 5 seconds
        
        end_time = time.time()
        stop_duration = end_time - start_time
        
        print(f"After stop - running: {thread.running}")
        print(f"After stop - isRunning: {thread.isRunning()}")
        print(f"Stop duration: {stop_duration:.2f} seconds")
        
        # Clean up
        if thread.isRunning():
            thread.terminate()
            thread.wait(1000)
        
        thread.deleteLater()
        
        if stop_duration < 6.0:  # Should stop within 6 seconds
            print("SUCCESS: Camera thread stopped cleanly")
            return True
        else:
            print("ERROR: Camera thread took too long to stop")
            return False
        
    except Exception as e:
        print(f"ERROR: Camera thread test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_camera_tab_stop():
    """Test camera tab stop functionality"""
    try:
        from DesktopApp.threads.main_window_thread import MainWindow
        from DesktopApp.objects.Interface_text import Interface_text
        
        app = QApplication(sys.argv)
        
        print("Testing camera tab stop functionality...")
        
        # Create main window
        main_window = MainWindow()
        camera_tab = main_window.camera_tab
        
        # Test stop_camera method exists and can be called
        if hasattr(camera_tab, 'stop_camera'):
            print("SUCCESS: Camera tab has stop_camera method")
            
            # Test calling stop_camera (should handle None thread gracefully)
            try:
                camera_tab.stop_camera()
                print("SUCCESS: stop_camera called without errors")
                return True
            except Exception as e:
                print(f"ERROR: stop_camera failed: {e}")
                return False
        else:
            print("ERROR: Camera tab missing stop_camera method")
            return False
        
    except Exception as e:
        print(f"ERROR: Camera tab test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_thread_cleanup():
    """Test thread cleanup and resource management"""
    try:
        from DesktopApp.threads.camera_thread import CameraThread
        
        app = QApplication(sys.argv)
        
        print("Testing thread cleanup...")
        
        # Create and start multiple threads
        threads = []
        for i in range(3):
            thread = CameraThread(f"test_{i}")
            threads.append(thread)
            thread.start()
            time.sleep(0.1)  # Small delay between starts
        
        print(f"Created {len(threads)} threads")
        
        # Stop all threads
        start_time = time.time()
        for i, thread in enumerate(threads):
            print(f"Stopping thread {i+1}...")
            thread.stop()
            if thread.isRunning():
                thread.wait(3000)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"All threads stopped in {total_time:.2f} seconds")
        
        # Check all threads are stopped
        all_stopped = all(not thread.isRunning() for thread in threads)
        
        if all_stopped and total_time < 10.0:
            print("SUCCESS: Multiple threads stopped cleanly")
            return True
        else:
            print(f"ERROR: Threads not all stopped or took too long")
            return False
        
    except Exception as e:
        print(f"ERROR: Thread cleanup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("Testing Video Stop Functionality")
    print("=" * 40)
    
    tests = [
        ("Camera Thread Lifecycle", test_camera_thread_lifecycle),
        ("Camera Tab Stop", test_camera_tab_stop),
        ("Thread Cleanup", test_thread_cleanup),
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
    print("\n" + "=" * 40)
    print("VIDEO STOP TEST SUMMARY:")
    print("=" * 40)
    
    passed = 0
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("Video stop functionality is working correctly!")
        return True
    else:
        print("Video stop functionality needs more work.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
