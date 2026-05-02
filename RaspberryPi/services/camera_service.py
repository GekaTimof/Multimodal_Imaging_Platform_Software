import time
import threading
from picamera2 import Picamera2
import cv2


class CameraService:
    """Service responsible for capturing frames from the Raspberry Pi camera."""

    def __init__(self, width=640, height=480, fps=20):
        self.width = width
        self.height = height
        self.fps = fps
        self.picam2 = Picamera2()
        self.frame_lock = threading.Lock()
        self.current_frame = None
        self.running = False

        config = self.picam2.create_preview_configuration(
            main={"size": (self.width, self.height), "format": "RGB888"}
        )
        self.picam2.configure(config)
        self.picam2.start()

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def _capture_loop(self):
        while self.running:
            frame = self.picam2.capture_array()
            ret, jpeg = cv2.imencode('.jpg', frame)
            if ret:
                with self.frame_lock:
                    self.current_frame = jpeg.tobytes()
            time.sleep(1 / self.fps)

    def get_frame(self):
        with self.frame_lock:
            return self.current_frame

    def stop(self):
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=1.0)
        try:
            self.picam2.stop()
        except Exception:
            pass
