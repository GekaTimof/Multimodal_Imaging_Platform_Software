import cv2
import time
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage

class SimpleCameraThread(QThread):
    frame_ready = pyqtSignal(QImage)
    status_ready = pyqtSignal(str)

    def __init__(self, camera_source=0):
        super().__init__()
        self.camera_source = camera_source
        self.running = False
        self.cap = None

    def run(self):
        try:
            self.status_ready.emit(f"Connecting to {self.camera_source}")
            
            # Simple camera connection without database
            cap = cv2.VideoCapture(self.camera_source)
            if not cap.isOpened():
                self.status_ready.emit(f"Camera not opened: {self.camera_source}")
                return
            
            self.cap = cap
            self.running = True
            self.status_ready.emit("Camera started")

            # Simple capture loop
            while self.running:
                ret, frame = cap.read()
                if not ret or not self.running:
                    break

                # Convert to QImage
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
                self.frame_ready.emit(img)

        except Exception as e:
            self.status_ready.emit(f"Camera error: {e}")
        
        finally:
            # Clean up
            try:
                if hasattr(self, 'cap') and self.cap is not None:
                    self.cap.release()
            except:
                pass
            self.cap = None
            self.status_ready.emit("Camera stopped")

    def stop(self):
        self.running = False
        
        # Wait for thread to finish
        if self.isRunning():
            if not self.wait(3000):  # Wait up to 3 seconds
                self.terminate()
                self.wait(1000)
