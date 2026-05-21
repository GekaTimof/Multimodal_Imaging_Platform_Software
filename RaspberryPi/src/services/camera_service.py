import time
import threading
import numpy as np
import cv2
import sys
import os
import signal
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
        """Initialize camera using rpicam-vid continuous MJPEG stream."""
        self.rpicam_process = None
        self._mjpeg_buffer = b''
        self._mjpeg_lock = threading.Lock()

        # Verify camera is accessible by doing a quick test
        test_result = subprocess.run(
            ['rpicam-vid', '--list-cameras'],
            capture_output=True, timeout=5
        )
        if test_result.returncode != 0 and b'Available cameras' not in test_result.stdout + test_result.stderr:
            raise Exception("No cameras found by rpicam-vid")

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
                # Parse video resolution from database (format: "1920x1080")
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

                # Parse photo resolution from database
                photo_resolution = settings.get('PhotoResolution', '3280x2464')
                if 'x' in photo_resolution:
                    width_str, height_str = photo_resolution.split('x')
                    self.photo_width = int(width_str)
                    self.photo_height = int(height_str)
                else:
                    self.photo_width, self.photo_height = 3280, 2464

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
                self.photo_width, self.photo_height = 3280, 2464
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
            self.photo_width, self.photo_height = 3280, 2464
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

    def _start_rpicam_vid(self):
        """Start rpicam-vid process for continuous MJPEG streaming."""
        cmd = [
            'rpicam-vid',
            '-t', '0',
            '--width', str(self.width),
            '--height', str(self.height),
            '--framerate', str(self.fps),
            '--codec', 'mjpeg',
            '--quality', '70',
            '--flush',
            '-o', '-',
        ]
        # Auto exposure settings
        # rpicam-apps uses --shutter presence to control manual/auto exposure
        if not self.ae_enable:
            max_shutter_us = int(1_000_000 / self.fps)
            if self.exposure_time <= max_shutter_us:
                cmd.extend(['--shutter', str(int(self.exposure_time))])
                cmd.extend(['--gain', str(float(self.analogue_gain))])
            # else: exposure too long for video fps → let camera handle it

        # Auto white balance settings
        # Valid modes: auto, incandescent, tungsten, fluorescent, indoor, daylight, cloudy, custom
        if not self.awb_enable:
            cmd.append('--awb=custom')  # Use custom AWB mode with manual gains
            if self.red_gain and self.blue_gain:
                cmd.extend(['--awbgains', f"{float(self.red_gain)},{float(self.blue_gain)}"])
        else:
            cmd.append('--awb=auto')  # Enable auto white balance

        self.rpicam_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0
        )
        print(f"rpicam-vid started (PID {self.rpicam_process.pid}): {' '.join(cmd)}")

    def start(self):
        if self.running:
            return
        self.running = True
        if self.camera_backend == "rpicam":
            self._start_rpicam_vid()
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def _capture_loop(self):
        if self.camera_backend == "rpicam" and self.use_real_camera:
            self._capture_loop_rpicam_vid()
        else:
            self._capture_loop_generic()

    def _capture_loop_rpicam_vid(self):
        """Read MJPEG frames from rpicam-vid stdout."""
        SOI = b'\xff\xd8'
        EOI = b'\xff\xd9'
        buf = b''
        consecutive_errors = 0

        while self.running:
            try:
                if self.rpicam_process is None or self.rpicam_process.poll() is not None:
                    print("rpicam-vid process died, restarting...")
                    self._start_rpicam_vid()
                    buf = b''

                chunk = self.rpicam_process.stdout.read(65536)
                if not chunk:
                    time.sleep(0.01)
                    continue

                buf += chunk
                consecutive_errors = 0

                while True:
                    start = buf.find(SOI)
                    if start == -1:
                        buf = b''
                        break
                    end = buf.find(EOI, start + 2)
                    if end == -1:
                        buf = buf[start:]
                        break
                    jpeg_bytes = buf[start:end + 2]
                    buf = buf[end + 2:]
                    with self.frame_lock:
                        self.current_frame = jpeg_bytes

            except Exception as e:
                consecutive_errors += 1
                print(f"rpicam-vid read error ({consecutive_errors}): {e}")
                if consecutive_errors > 10:
                    print("Too many errors, falling back to test pattern")
                    self.use_real_camera = False
                    self.camera_backend = "test"
                    self._capture_loop_generic()
                    return
                time.sleep(0.1)

    def _capture_loop_generic(self):
        """Capture loop for OpenCV/picamera2/test backends."""
        while self.running:
            if self.use_real_camera:
                try:
                    if self.camera_backend == "opencv":
                        ret, frame = self.cap.read()
                        if not ret or frame is None:
                            raise Exception("Failed to read frame from OpenCV camera")
                    elif self.camera_backend == "picamera2":
                        frame = self.picam2.capture_array()
                    else:
                        raise Exception("Unknown camera backend")
                except Exception as e:
                    print(f"Camera capture error: {e}")
                    self.use_real_camera = False
                    self.camera_backend = "test"
            else:
                frame = self._generate_test_pattern()

            ret, jpeg = cv2.imencode('.jpg', frame)
            if ret:
                with self.frame_lock:
                    self.current_frame = jpeg.tobytes()
            time.sleep(1 / self.fps)
    
    def _capture_rpicam_frame(self):
        """Legacy method - not used when rpicam-vid is running."""
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

    def _pause_video_stream(self):
        """Pause video stream by stopping rpicam-vid process and killing any remaining camera processes."""
        # Stop our own process first - use kill immediately for faster release
        if hasattr(self, 'rpicam_process') and self.rpicam_process is not None:
            try:
                # Try graceful termination first, but quickly move to kill
                self.rpicam_process.terminate()
                try:
                    self.rpicam_process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    print("Process didn't terminate gracefully, killing...")
                    self.rpicam_process.kill()
                    try:
                        self.rpicam_process.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        # Force kill with SIGKILL if still running
                        import signal
                        try:
                            os.kill(self.rpicam_process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass  # Process already dead
            except Exception as e:
                print(f"Warning: error stopping video stream: {e}")
            finally:
                self.rpicam_process = None

        # Kill any other rpicam processes that might be holding the camera
        try:
            import subprocess
            # Find and kill any rpicam-vid or rpicam-still processes
            # Use separate simple patterns instead of regex alternation
            all_pids = set()
            for pattern in ['rpicam-vid', 'rpicam-still']:
                result = subprocess.run(['pgrep', '-f', pattern],
                                      capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    for pid in result.stdout.strip().split('\n'):
                        if pid.strip():
                            all_pids.add(pid.strip())

            if all_pids:
                print(f"Killing remaining rpicam processes: {sorted(all_pids)}")
                for pid in sorted(all_pids):
                    try:
                        subprocess.run(['kill', '-9', pid], check=False)
                    except Exception:
                        pass
                # Wait longer for processes to die and camera to be released
                import time
                time.sleep(1.0)
        except Exception as e:
            print(f"Warning: could not check for other rpicam processes: {e}")

        # Additional wait to ensure camera is released
        import time
        time.sleep(1)
        print("Video stream paused, camera should be free")

    def _resume_video_stream(self):
        """Resume video stream by restarting rpicam-vid process."""
        if self.running:
            try:
                # Wait extra time to ensure camera is fully released by previous process
                # libcamera needs time to clean up resources
                import time
                time.sleep(2)
                print("Resuming video stream...")
                self._start_rpicam_vid()
                print("Video stream resumed")
            except Exception as e:
                print(f"Error resuming video stream: {e}")

    def capture_photo(self, output_path: Optional[str] = None) -> Tuple[bool, Union[np.ndarray, str]]:
        """Capture a high-quality photo using PhotoResolution and all camera settings.

        Args:
            output_path: Optional path to save the photo. If None, returns the frame as numpy array.

        Returns:
            Tuple of (success: bool, result: Union[np.ndarray, str])
            - If output_path is None: returns (True, numpy_array) or (False, error_message)
            - If output_path is provided: returns (True, file_path) or (False, error_message)
        """
        try:
            # Reload settings to get current values
            self._load_settings()

            if self.use_real_camera and self.camera_backend == "rpicam":
                # Pause video stream to free camera for still capture
                # Camera cannot be used by rpicam-vid and rpicam-still simultaneously
                video_was_running = self.running
                if video_was_running:
                    print("Pausing video stream for photo capture...")
                    self._pause_video_stream()

                try:
                    # Build rpicam-still command with photo resolution and full quality
                    cmd = [
                        'rpicam-still',
                        '-n',  # No preview
                        '--width', str(self.photo_width),
                        '--height', str(self.photo_height),
                        '--quality', '95',  # High quality for photos
                    ]

                    # Add exposure settings
                    if self.exposure_time is not None and self.exposure_time > 0:
                        cmd.extend(['--shutter', str(int(self.exposure_time))])

                    if self.analogue_gain is not None and self.analogue_gain >= 0:
                        cmd.extend(['--gain', str(float(self.analogue_gain))])

                    if self.exposure_value is not None:
                        cmd.extend(['--ev', str(float(self.exposure_value))])

                    # Auto white balance settings
                    # Valid modes: auto, incandescent, tungsten, fluorescent, indoor, daylight, cloudy, custom
                    if not self.awb_enable:
                        # Use custom mode with manual gains
                        cmd.append('--awb=custom')
                        if self.red_gain is not None and self.blue_gain is not None:
                            cmd.extend(['--awbgains', f"{float(self.red_gain)},{float(self.blue_gain)}"])
                    else:
                        cmd.append('--awb=auto')

                    # Calculate timeout based on exposure time + buffer (min 10s for photos)
                    timeout_seconds = max(10, (self.exposure_time / 1_000_000) + 3)
                    print(f"rpicam-still command: {' '.join(cmd)}, timeout={timeout_seconds}s")

                    if output_path:
                        # Save to file
                        cmd.extend(['-o', output_path])
                        result = subprocess.run(cmd, capture_output=True, timeout=timeout_seconds)
                        if result.returncode == 0:
                            return True, output_path
                        else:
                            error_msg = result.stderr.decode('utf-8', errors='ignore') if result.stderr else "Unknown error"
                            print(f"rpicam-still failed: {error_msg}")
                            return False, f"rpicam-still failed: {error_msg}"
                    else:
                        # Return as numpy array
                        cmd.extend(['-o', '-'])
                        result = subprocess.run(cmd, capture_output=True, timeout=timeout_seconds)
                        if result.returncode == 0:
                            frame_array = np.frombuffer(result.stdout, dtype=np.uint8)
                            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                            if frame is not None:
                                return True, frame
                            else:
                                print("Failed to decode captured image from rpicam-still output")
                                return False, "Failed to decode captured image"
                        else:
                            error_msg = result.stderr.decode('utf-8', errors='ignore') if result.stderr else "Unknown error"
                            print(f"rpicam-still failed (stdout mode): {error_msg}")
                            return False, f"rpicam-still failed: {error_msg}"

                finally:
                    # Always resume video stream if it was running
                    if video_was_running:
                        print("Resuming video stream...")
                        self._resume_video_stream()

            elif self.use_real_camera and self.camera_backend == "opencv":
                # For OpenCV backend, capture frame at photo resolution if possible
                try:
                    # Try to set photo resolution temporarily
                    if hasattr(self, 'cap'):
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.photo_width)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.photo_height)
                        time.sleep(0.5)  # Wait for resolution change

                    ret, frame = self.cap.read()
                    if ret and frame is not None:
                        if output_path:
                            cv2.imwrite(output_path, frame)
                            return True, output_path
                        else:
                            return True, frame
                    else:
                        return False, "Failed to capture frame from OpenCV camera"
                except Exception as e:
                    return False, f"OpenCV capture error: {e}"

            else:
                # Test pattern - generate at photo resolution
                # Temporarily set resolution for test pattern
                orig_width, orig_height = self.width, self.height
                self.width, self.height = self.photo_width, self.photo_height
                frame = self._generate_test_pattern()
                self.width, self.height = orig_width, orig_height

                if output_path:
                    cv2.imwrite(output_path, frame)
                    return True, output_path
                else:
                    return True, frame

        except subprocess.TimeoutExpired:
            return False, f"Photo capture timeout (exposure={self.exposure_time}us)"
        except Exception as e:
            return False, f"Photo capture error: {e}"

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
        elif self.camera_backend == "rpicam" and self.use_real_camera:
            # Restart rpicam-vid to apply new settings (exposure, AWB, etc.)
            print("Restarting rpicam-vid with updated settings...")
            self._restart_rpicam_vid()

    def _restart_rpicam_vid(self):
        """Terminate current rpicam-vid and start a new one with updated settings."""
        if hasattr(self, 'rpicam_process') and self.rpicam_process is not None:
            try:
                self.rpicam_process.terminate()
                self.rpicam_process.wait(timeout=3)
            except Exception:
                pass
            self.rpicam_process = None
        self._start_rpicam_vid()

    def _reinitialize_camera(self):
        """Reinitialize camera with new settings."""
        if self.camera_backend == "rpicam":
            self._restart_rpicam_vid()
            return
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
            self.thread.join(timeout=2.0)

        if hasattr(self, 'rpicam_process') and self.rpicam_process is not None:
            try:
                self.rpicam_process.terminate()
                self.rpicam_process.wait(timeout=3)
            except Exception:
                pass
            self.rpicam_process = None

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
