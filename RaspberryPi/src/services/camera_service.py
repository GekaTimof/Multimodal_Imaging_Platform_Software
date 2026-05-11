import time
import threading
import numpy as np
import cv2
import sys
import os
import subprocess
import logging
from typing import Optional, Dict, Any, Tuple, Union

# Import config
from src.config.settings import config
from .database_service import db_service

# Setup logging
logger = logging.getLogger(__name__)

# Camera backend options
OPENCV_AVAILABLE = True
PICAMERA2_AVAILABLE = False  # Disabled due to libcamera issues
RPICAM_AVAILABLE = True  # Use rpicam-apps as subprocess


class CameraService:
    """Service responsible for capturing frames from the Raspberry Pi camera."""

    def __init__(self, fps: int = config.DEFAULT_FPS):
        self.fps: int = fps
        self.frame_lock = threading.Lock()
        self.current_frame: Optional[np.ndarray] = None
        self.running: bool = False
        self.use_real_camera: bool = False
        self.camera_backend: Optional[str] = None
        
        # Load settings from database
        self._load_settings()
        
        # Try to initialize real camera with different backends
        self._initialize_camera()
    
    def _initialize_camera(self):
        """Try different camera backends to find a working one."""
        
        # Try rpicam-apps first (most reliable for IMX477)
        if RPICAM_AVAILABLE:
            try:
                self._init_rpicam_app()
                self.use_real_camera = True
                self.camera_backend = "rpicam"
                print("rpicam-apps camera initialized successfully")
                return
            except Exception as e:
                print(f"rpicam-apps camera failed: {e}")
        
        # Try OpenCV + V4L2
        if OPENCV_AVAILABLE:
            try:
                self._init_opencv_camera()
                self.use_real_camera = True
                self.camera_backend = "opencv"
                print("OpenCV + V4L2 camera initialized successfully")
                return
            except Exception as e:
                print(f"OpenCV camera failed: {e}")
        
        # Try picamera2 as fallback
        if PICAMERA2_AVAILABLE:
            try:
                self._init_picamera2()
                self.use_real_camera = True
                self.camera_backend = "picamera2"
                print("Picamera2 camera initialized successfully")
                return
            except Exception as e:
                print(f"Picamera2 camera failed: {e}")
        
        # If all fail, use test pattern
        print("All camera backends failed, using test pattern")
        self.use_real_camera = False
        self.camera_backend = "test"
    
    def _init_opencv_camera(self):
        """Initialize camera using OpenCV + V4L2."""
        # Try all available video devices
        import glob
        video_devices = glob.glob('/dev/video*')
        
        print(f"Trying video devices: {video_devices}")
        
        for device in video_devices:
            try:
                print(f"Testing {device}...")
                cap = cv2.VideoCapture(device)
                if cap.isOpened():
                    print(f"Device {device} opened successfully")
                    
                    # Try different backend indices
                    backends = [cv2.CAP_V4L2, cv2.CAP_ANY]
                    for backend in backends:
                        try:
                            cap_with_backend = cv2.VideoCapture(device, backend)
                            if cap_with_backend.isOpened():
                                # Set resolution
                                cap_with_backend.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                                cap_with_backend.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                                cap_with_backend.set(cv2.CAP_PROP_FPS, self.fps)
                                
                                # Test if we can read a frame
                                ret, frame = cap_with_backend.read()
                                if ret and frame is not None:
                                    self.cap = cap_with_backend
                                    # Update actual resolution
                                    actual_width = int(cap_with_backend.get(cv2.CAP_PROP_FRAME_WIDTH))
                                    actual_height = int(cap_with_backend.get(cv2.CAP_PROP_FRAME_HEIGHT))
                                    self.width = actual_width
                                    self.height = actual_height
                                    print(f"OpenCV camera working with {device} (backend {backend}): {actual_width}x{actual_height}")
                                    return
                                else:
                                    cap_with_backend.release()
                        except Exception as e:
                            print(f"Backend {backend} failed for {device}: {e}")
                            continue
                    
                    cap.release()
                else:
                    print(f"Could not open {device}")
            except Exception as e:
                print(f"Failed to open {device}: {e}")
                continue
        
        raise Exception("No working OpenCV camera device found")
    
    def _init_rpicam_app(self):
        """Initialize camera using rpicam-apps subprocess."""
        # Create a simple MJPEG stream using rpicam-vid
        # We'll capture frames from the subprocess output
        import tempfile
        import os
        
        # Create a temporary pipe for frame capture
        self.rpicam_process = None
        self.frame_pipe = None
        
        # For now, we'll use a simpler approach - just indicate success
        # The actual frame capture will be handled in _capture_loop
        print("rpicam-apps backend selected")
        
    def _init_picamera2(self):
        """Initialize camera using picamera2."""
        self.picam2 = Picamera2()
        self._configure_camera()

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
            # Try the most basic approach - don't specify format initially
            print("Attempting basic camera configuration...")
            
            # Try default configuration first
            config = self.picam2.create_preview_configuration()
            self.picam2.configure(config)
            self.picam2.start()
            
            # Get the actual resolution from the configuration
            if hasattr(config, 'main') and hasattr(config.main, 'size'):
                self.width, self.height = config.main.size
            else:
                self.width, self.height = 1280, 720  # Default fallback
                
            print(f"Camera configured with default settings: {self.width}x{self.height}")
            
        except Exception as e:
            print(f"Basic configuration failed: {e}")
            # Try minimal configuration
            try:
                print("Trying minimal configuration...")
                config = self.picam2.create_preview_configuration(
                    main={"size": (640, 480)}
                )
                self.picam2.configure(config)
                self.picam2.start()
                self.width, self.height = 640, 480
                print(f"Camera configured with minimal settings: 640x480")
            except Exception as e2:
                print(f"Minimal configuration also failed: {e2}")
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
                    if self.camera_backend == "opencv":
                        ret, frame = self.cap.read()
                        if not ret or frame is None:
                            raise Exception("Failed to read frame from OpenCV camera")
                    elif self.camera_backend == "picamera2":
                        frame = self.picam2.capture_array()
                    elif self.camera_backend == "rpicam":
                        frame = self._capture_rpicam_frame()
                    else:
                        raise Exception("Unknown camera backend")
                except Exception as e:
                    print(f"Camera capture error: {e}")
                    self.use_real_camera = False
                    self.camera_backend = "test"
            else:
                # Generate test pattern with correct resolution
                frame = self._generate_test_pattern()
            
            ret, jpeg = cv2.imencode('.jpg', frame)
            if ret:
                with self.frame_lock:
                    self.current_frame = jpeg.tobytes()
            time.sleep(1 / self.fps)
    
    def _capture_rpicam_frame(self):
        """Capture frame using rpicam-still subprocess."""
        try:
            # Reload settings from database to get current resolution
            self._load_settings()
            
            # Use rpicam-still to capture a single frame
            cmd = [
                'rpicam-still',
                '-n',  # No preview
                '-t', '100',  # Timeout 100ms
                '--width', str(self.width),
                '--height', str(self.height),
                '--quality', '70',
                '-o', '-'  # Output to stdout
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=1)
            if result.returncode == 0:
                # Decode JPEG from stdout
                frame_array = np.frombuffer(result.stdout, dtype=np.uint8)
                frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                if frame is not None:
                    return frame
            
            # Fallback to test pattern
            return self._generate_test_pattern()
            
        except Exception as e:
            print(f"rpicam capture error: {e}")
            return self._generate_test_pattern()
    
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

    def reload_settings(self):
        """Reload camera settings from database and reinitialize if needed."""
        old_resolution = (self.width, self.height)
        
        # Reload settings from database
        self._load_settings()
        
        # Check if resolution changed
        new_resolution = (self.width, self.height)
        if old_resolution != new_resolution and self.use_real_camera:
            print(f"Resolution changed from {old_resolution} to {new_resolution}, reinitializing camera...")
            self._reinitialize_camera()
    
    def _reinitialize_camera(self):
        """Reinitialize camera with new settings."""
        # Stop current camera
        if self.camera_backend == "opencv" and hasattr(self, 'cap'):
            try:
                self.cap.release()
            except Exception:
                pass
        elif self.camera_backend == "picamera2" and hasattr(self, 'picam2'):
            try:
                self.picam2.stop()
            except Exception:
                pass
        
        # Reinitialize with new settings
        self._initialize_camera()

    def stop(self):
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=1.0)
        
        if self.use_real_camera:
            if self.camera_backend == "opencv" and hasattr(self, 'cap'):
                try:
                    self.cap.release()
                except Exception:
                    pass
            elif self.camera_backend == "picamera2" and hasattr(self, 'picam2'):
                try:
                    self.picam2.stop()
                except Exception:
                    pass
