import cv2
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage

class CameraThread(QThread):
    frame_ready = pyqtSignal(QImage)
    status_ready = pyqtSignal(str)

    def __init__(self, camera_source=0):
        super().__init__()
        self.camera_source = camera_source
        self.running = False

    def run(self):
        self.status_ready.emit(f"Connecting to {self.camera_source}")
        cap = cv2.VideoCapture(self.camera_source)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():
            self.status_ready.emit(f"Camera not opened: {self.camera_source}")
            return

        self.running = True
        self.status_ready.emit("Camera started")

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