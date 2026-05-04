import cv2
import sys
import os
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage

# Add path for database service
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'RaspberryPi', 'services'))

class CameraThread(QThread):
    frame_ready = pyqtSignal(QImage)
    status_ready = pyqtSignal(str)

    def __init__(self, camera_source=0):
        super().__init__()
        self.camera_source = camera_source
        self.running = False
        self.cap = None

    def load_camera_settings(self):
        """Load camera settings from database"""
        try:
            # Use absolute import path
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'RaspberryPi', 'services')
            if db_path not in sys.path:
                sys.path.insert(0, db_path)
            
            from database_service import db_service
            settings = db_service.get_camera_settings()
            
            if not settings:
                self.status_ready.emit("No camera settings found in database")
                return None
            
            self.status_ready.emit(f"Loaded settings from database: AE={settings.get('AeEnable')}, AWB={settings.get('AwbEnable')}")
            return settings
            
        except Exception as e:
            self.status_ready.emit(f"Error loading settings from database: {e}")
            return None

    def apply_camera_settings(self, cap, settings):
        """Apply database settings to camera"""
        try:
            # Apply exposure settings
            if not settings.get('AeEnable', True):
                # Manual exposure
                exposure_time = settings.get('ExposureTime', 10000)
                gain = settings.get('AnalogueGain', 1.0)
                
                # Convert exposure time from microseconds to appropriate value for OpenCV
                # Note: This is a simplified conversion - actual implementation may need calibration
                exposure_value = exposure_time / 10000.0  # Normalize to reasonable range
                
                cap.set(cv2.CAP_PROP_EXPOSURE, exposure_value)
                cap.set(cv2.CAP_PROP_GAIN, gain)
                
                self.status_ready.emit(f"Applied manual settings: Exposure={exposure_time}, Gain={gain}")
            else:
                # Auto exposure
                cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
                self.status_ready.emit("Applied auto exposure settings")
                
            return True
            
        except Exception as e:
            self.status_ready.emit(f"Error applying camera settings: {e}")
            return False

    def run(self):
        self.status_ready.emit(f"Connecting to {self.camera_source}")
        
        # Load settings from database first
        settings = self.load_camera_settings()
        
        # Connect to camera
        cap = cv2.VideoCapture(self.camera_source)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap = cap

        if not cap.isOpened():
            self.status_ready.emit(f"Camera not opened: {self.camera_source}")
            return

        # Apply database settings to camera
        if settings:
            self.apply_camera_settings(cap, settings)

        self.running = True
        self.status_ready.emit("Camera started with database settings")

        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
            self.frame_ready.emit(img)

        cap.release()
        self.status_ready.emit("Camera stopped")

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()