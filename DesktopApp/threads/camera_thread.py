import cv2
import sys
import os
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage

class CameraThread(QThread):
    frame_ready = pyqtSignal(QImage)
    status_ready = pyqtSignal(str)

    def __init__(self, camera_source=0):
        super().__init__()
        self.camera_source = camera_source
        self.running = False
        self.cap = None

    def load_camera_settings(self, slot_id=0):
        """Load camera settings from database slot - called from main thread"""
        try:
            # Use absolute import path
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'RaspberryPi', 'services')
            if db_path not in sys.path:
                sys.path.insert(0, db_path)
            
            from database_service import db_service
            settings = db_service.get_camera_settings_by_slot(slot_id)
            
            if not settings:
                self.status_ready.emit(f"No camera settings found in slot {slot_id}")
                return None
            
            self.status_ready.emit(f"Loaded settings from slot {slot_id}: {settings.get('SettingsName')} - {settings.get('Resolution')}")
            return settings
            
        except Exception as e:
            self.status_ready.emit(f"Error loading settings from slot {slot_id}: {e}")
            return None

    def apply_camera_settings(self, settings):
        """Apply database settings to camera - called from main thread"""
        try:
            if self.cap and self.cap.isOpened():
                # Apply resolution first
                resolution = settings.get('Resolution', '1920x1080')
                if 'x' in resolution:
                    width, height = map(int, resolution.split('x'))
                    
                    # Set camera resolution
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                    
                    # Verify the resolution was applied
                    actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    
                    self.status_ready.emit(f"Resolution set to {width}x{height} (actual: {actual_width}x{actual_height})")
                
                # Apply exposure settings
                if not settings.get('AeEnable', True):
                    # Manual exposure
                    exposure_time = settings.get('ExposureTime', 10000)
                    gain = settings.get('AnalogueGain', 1.0)
                    
                    # Convert exposure time from microseconds to appropriate value for OpenCV
                    exposure_value = exposure_time / 10000.0  # Normalize to reasonable range
                    
                    self.cap.set(cv2.CAP_PROP_EXPOSURE, exposure_value)
                    self.cap.set(cv2.CAP_PROP_GAIN, gain)
                    
                    self.status_ready.emit(f"Applied manual settings: Exposure={exposure_time}, Gain={gain}")
                else:
                    # Auto exposure
                    self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
                    self.status_ready.emit("Applied auto exposure settings")
                    
                return True
            else:
                return False
                
        except Exception as e:
            self.status_ready.emit(f"Error applying camera settings: {e}")
            return False

    def run(self):
        try:
            self.status_ready.emit(f"Connecting to {self.camera_source}")
            
            # Load settings before initializing camera
            settings = self.load_camera_settings()
            
            # Simple camera connection
            cap = cv2.VideoCapture(self.camera_source)
            if not cap.isOpened():
                self.status_ready.emit(f"Camera not opened: {self.camera_source}")
                return
            
            self.cap = cap
            
            # Apply initial settings including resolution
            if settings:
                self.apply_camera_settings(settings)
            
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
            except Exception:
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