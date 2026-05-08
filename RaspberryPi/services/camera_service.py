import time
import threading
import numpy as np
import cv2
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from RaspberryPi.services.database_service import db_service

# Disable picamera2 for now due to libcamera issues
PICAMERA2_AVAILABLE = False


class CameraService:
    """Service responsible for capturing frames from the Raspberry Pi camera."""

    def __init__(self, fps=20):
        self.fps = fps
        self.frame_lock = threading.Lock()
        self.current_frame = None
        self.running = False
        self.use_real_camera = False
        
        # Load settings from database
        self._load_settings()
        
        # Try to initialize real camera
        if PICAMERA2_AVAILABLE:
            try:
                self.picam2 = Picamera2()
                self._configure_camera()
                self.use_real_camera = True
                print("Real camera initialized successfully")
            except Exception as e:
                print(f"Failed to initialize real camera: {e}")
                self.use_real_camera = False
        else:
            print("Picamera2 not available, using test pattern")
            self.use_real_camera = False

    def _load_settings(self):
        """Load camera settings from database."""
        try:
            settings = db_service.get_camera_settings()
            if settings:
                # Parse resolution from database (format: "1920x1080")
                video_resolution = settings.get('VideoResolution', '1280x720')
                if 'x' in video_resolution:
                    width_str, height_str = video_resolution.split('x')
                    width = int(width_str)
                    height = int(height_str)
                    # Use safe resolutions for IMX477
                    safe_resolutions = [(640, 480), (1280, 720), (1920, 1080)]
                    if (width, height) in safe_resolutions:
                        self.width, self.height = width, height
                    else:
                        self.width, self.height = 1280, 720  # Safe fallback
                else:
                    self.width, self.height = 1280, 720
                    
                # Load other camera settings
                self.ae_enable = settings.get('AeEnable', True)
                self.awb_enable = settings.get('AwbEnable', True)
                self.exposure_time = settings.get('ExposureTime', 10000)
                self.analogue_gain = settings.get('AnalogueGain', 1.0)
                self.exposure_value = settings.get('ExposureValue', 0.0)
                self.red_gain = settings.get('RedGain', 1.0)
                self.blue_gain = settings.get('BlueGain', 1.0)
            else:
                # Default settings if database is empty - use safe defaults
                self.width, self.height = 1280, 720
                self.ae_enable = True
                self.awb_enable = True
                self.exposure_time = 10000
                self.analogue_gain = 1.0
                self.exposure_value = 0.0
                self.red_gain = 1.0
                self.blue_gain = 1.0
                
        except Exception as e:
            print(f"Error loading camera settings: {e}")
            # Fallback to safe default settings
            self.width, self.height = 1280, 720
            self.ae_enable = True
            self.awb_enable = True
            self.exposure_time = 10000
            self.analogue_gain = 1.0
            self.exposure_value = 0.0
            self.red_gain = 1.0
            self.blue_gain = 1.0

    def _configure_camera(self):
        """Configure camera with current settings."""
        try:
            # Try the most basic configuration first
            print("Attempting basic camera configuration...")
            config = self.picam2.create_preview_configuration()
            self.picam2.configure(config)
            self.picam2.start()
            print("Camera configured with basic settings")
            
        except Exception as e:
            print(f"Error with basic configuration: {e}")
            # Try with explicit small resolution
            try:
                print("Trying with 640x480...")
                config = self.picam2.create_preview_configuration(
                    main={"size": (640, 480)}
                )
                self.picam2.configure(config)
                self.picam2.start()
                print("Camera configured with 640x480")
            except Exception as e2:
                print(f"All camera configurations failed: {e2}")
                raise e2

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def _capture_loop(self):
        while self.running:
            if self.use_real_camera:
                try:
                    frame = self.picam2.capture_array()
                except Exception as e:
                    print(f"Camera capture error: {e}")
                    self.use_real_camera = False
            else:
                # Generate test pattern with correct resolution
                frame = self._generate_test_pattern()
            
            ret, jpeg = cv2.imencode('.jpg', frame)
            if ret:
                with self.frame_lock:
                    self.current_frame = jpeg.tobytes()
            time.sleep(1 / self.fps)
    
    def _generate_test_pattern(self):
        """Generate a test pattern with the configured resolution."""
        # Create a colorful test pattern
        height, width = self.height, self.width
        
        # Create gradient background
        x = np.linspace(0, 255, width)
        y = np.linspace(0, 255, height)
        X, Y = np.meshgrid(x, y)
        
        # Create RGB channels with different patterns
        R = np.uint8(X)
        G = np.uint8(Y)
        B = np.uint8(255 - X)
        
        # Stack channels to create RGB image
        frame = np.stack([R, G, B], axis=2)
        
        # Add some text overlay
        text = f"Camera Test Pattern {width}x{height}"
        cv2.putText(frame, text, (50, height//2), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"Real Camera: {self.use_real_camera}", (50, height//2 + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return frame

    def get_frame(self):
        with self.frame_lock:
            return self.current_frame

    def stop(self):
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=1.0)
        if self.use_real_camera and hasattr(self, 'picam2'):
            try:
                self.picam2.stop()
            except Exception:
                pass
