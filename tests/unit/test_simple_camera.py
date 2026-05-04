#!/usr/bin/env python3
"""
Test simple camera thread without database dependencies
"""

import sys
import os
import time
from PyQt5.QtWidgets import QApplication

# Add parent directory to path for imports to work when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_simple_camera_thread():
    """Test simple camera thread lifecycle"""
    try:
        from DesktopApp.threads.simple_camera_thread import SimpleCameraThread
        
        app = QApplication(sys.argv)
        
        print("Testing simple camera thread...")
        
        # Create thread
        thread = SimpleCameraThread(0)
        
        print(f"Initial running: {thread.running}")
        print(f"Initial isRunning: {thread.isRunning()}")
        
        # Start thread
        print("Starting thread...")
        thread.start()
        
        # Wait a moment
        time.sleep(0.5)
        app.processEvents()
        
        print(f"After start - running: {thread.running}")
        print(f"After start - isRunning: {thread.isRunning()}")
        
        # Stop thread
        print("Stopping thread...")
        start_time = time.time()
        thread.stop()
        
        # Wait for finish
        if thread.isRunning():
            thread.wait(5000)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"After stop - running: {thread.running}")
        print(f"After stop - isRunning: {thread.isRunning()}")
        print(f"Stop duration: {duration:.2f}s")
        
        if duration < 6.0 and not thread.isRunning():
            print("SUCCESS: Simple camera thread works")
            return True
        else:
            print("ERROR: Simple camera thread failed")
            return False
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_camera_thread()
    sys.exit(0 if success else 1)
