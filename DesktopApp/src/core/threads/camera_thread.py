import time
import cv2
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage
from config.api_config import API_BASE_URL
from core.constants.camera_constants import EXPOSURE_TIME_RANGE, ANALOGUE_GAIN_RANGE

class CameraThread(QThread):
    frame_ready = pyqtSignal(QImage)
    status_ready = pyqtSignal(str)

    def __init__(self, camera_source=0):
        super().__init__()
        self.camera_source = camera_source
        self.running = False
        self.cap = None

    def load_camera_settings(self, slot_id=0):
        """Load camera settings from API only - called from main thread"""
        try:
            # Load settings from API only
            api_url = f"{API_BASE_URL}/settings/camera"
            response = requests.get(api_url, timeout=5)
            
            if response.status_code == 200:
                settings = response.json()
                self.status_ready.emit(f"Loaded settings from API: {settings.get('SettingsName', 'Unknown')} - {settings.get('VideoResolution', 'Unknown')}")
                return settings
            else:
                self.status_ready.emit(f"API error: HTTP {response.status_code}")
                return None
                
        except requests.RequestException as e:
            self.status_ready.emit(f"API request failed: {e}")
            return None
        except Exception as e:
            self.status_ready.emit(f"Error loading settings from API: {e}")
            return None

    def apply_camera_settings(self, settings):
        """Apply API/database settings to camera - called from main thread

        IMPORTANT NOTE: This only affects the LOCAL OpenCV camera capture.
        The video stream from RaspberryPi (rpicam-vid) uses its own settings
        from the database. To change video stream settings, use the Settings UI
        which updates the RaspberryPi database and restarts the stream.
        """
        try:
            if not settings:
                return False

            if self.cap and self.cap.isOpened():
                # Apply video resolution first (for streaming)
                video_resolution = settings.get('VideoResolution', '1920x1080')
                if 'x' in video_resolution:
                    width, height = map(int, video_resolution.split('x'))
                    
                    # Set camera resolution with validation
                    if width > 0 and height > 0:
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                        
                        # Small delay to allow camera to process
                        time.sleep(0.1)
                        
                        # Verify resolution was applied
                        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        
                        self.status_ready.emit(f"Resolution set to {width}x{height} (actual: {actual_width}x{actual_height})")
                
                # Apply exposure settings safely
                try:
                    if not settings.get('AeEnable', True):
                        # Manual exposure
                        exposure_time = settings.get('ExposureTime', 10000)
                        gain = settings.get('AnalogueGain', 1.0)
                        
                        # Validate ranges using constants from camera_constants.py
                        if EXPOSURE_TIME_RANGE[0] <= exposure_time <= EXPOSURE_TIME_RANGE[1] and \
                           ANALOGUE_GAIN_RANGE[0] <= gain <= ANALOGUE_GAIN_RANGE[1]:
                            # Convert exposure time from microseconds to appropriate value for OpenCV
                            exposure_value = min(max(exposure_time / 10000.0, 0.1), 100.0)  # Clamp to safe range
                            
                            self.cap.set(cv2.CAP_PROP_EXPOSURE, exposure_value)
                            self.cap.set(cv2.CAP_PROP_GAIN, gain)
                            
                            self.status_ready.emit(f"Applied manual settings: Exposure={exposure_time}, Gain={gain}")
                    else:
                        # Auto exposure
                        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
                        self.status_ready.emit("Applied auto exposure settings")
                except Exception as exp_error:
                    self.status_ready.emit(f"Warning: Could not apply exposure settings: {exp_error}")
                
                return True
            else:
                self.status_ready.emit("Camera not available for settings application")
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