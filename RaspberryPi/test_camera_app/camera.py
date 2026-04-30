import os
import sys
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap, QFont
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QGridLayout, QHBoxLayout,
    QVBoxLayout, QMessageBox, QScrollArea, QMainWindow, QGroupBox,
    QSpinBox, QDoubleSpinBox, QCheckBox
)

from picamera2 import Picamera2

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "test_media")
os.makedirs(MEDIA_DIR, exist_ok=True)


class CameraWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera Stable Test")
        self.setFixedSize(1280, 648)

        self.picam2 = Picamera2()

        self.busy = False
        self.preview_enabled = True

        self._build_ui()
        self._start_camera()

        self.timer = self.startTimer(50)

    def ts(self):
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)

        self.preview = QLabel("Camera preview")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setFixedSize(900, 540)
        self.preview.setStyleSheet("background: black; color: white;")
        root.addWidget(self.preview, 3)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(320)
        root.addWidget(scroll, 1)

        panel = QWidget()
        scroll.setWidget(panel)
        layout = QVBoxLayout(panel)

        layout.addWidget(QLabel(f"Save folder:\n{MEDIA_DIR}"))

        btn_box = QGroupBox("Actions")
        btn_layout = QGridLayout(btn_box)

        self.btn_photo = QPushButton("Take Photo")
        self.btn_apply = QPushButton("Apply Settings")

        btn_layout.addWidget(self.btn_photo, 0, 0)
        btn_layout.addWidget(self.btn_apply, 0, 1)

        layout.addWidget(btn_box)

        self.btn_photo.clicked.connect(self.take_photo)
        self.btn_apply.clicked.connect(self.apply_controls)

        ctrl_box = QGroupBox("Camera settings")
        ctrl = QGridLayout(ctrl_box)

        self.chk_ae = QCheckBox("Auto Exposure")
        self.chk_ae.setChecked(True)

        self.chk_awb = QCheckBox("Auto WB")
        self.chk_awb.setChecked(True)

        self.exp_time = self._spin_int(100, 3000000, 10000)
        self.gain = self._spin_double(0.0, 32.0, 1.0)
        self.exp_value = self._spin_double(-10.0, 10.0, 0.0)
        self.red_gain = self._spin_double(0.0, 8.0, 1.0)
        self.blue_gain = self._spin_double(0.0, 8.0, 1.0)

        rows = [
            ("Auto Exposure", self.chk_ae),
            ("Auto WB", self.chk_awb),
            ("ExposureTime", self.exp_time),
            ("Gain", self.gain),
            ("ExposureValue", self.exp_value),
            ("RedGain", self.red_gain),
            ("BlueGain", self.blue_gain),
        ]

        for r, (name, widget) in enumerate(rows):
            ctrl.addWidget(QLabel(name), r, 0)
            ctrl.addWidget(widget, r, 1)

        layout.addWidget(ctrl_box)

        # ✅ FIXED STATUS (no window resizing)
        self.status = QLabel("Ready")
        self.status.setWordWrap(True)
        self.status.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.status.setMaximumHeight(100)
        self.status.setStyleSheet("background: #222; color: #ddd; padding: 4px;")

        layout.addWidget(self.status)

    def _spin_int(self, mn, mx, val):
        s = QSpinBox()
        s.setRange(mn, mx)
        s.setValue(val)
        return s

    def _spin_double(self, mn, mx, val):
        s = QDoubleSpinBox()
        s.setRange(mn, mx)
        s.setDecimals(2)
        s.setValue(val)
        return s

    def _start_camera(self):
        cfg = self.picam2.create_preview_configuration(
            main={"size": (640, 360), "format": "RGB888"}
        )
        self.picam2.configure(cfg)
        self.picam2.start()

    def timerEvent(self, event):
        if self.busy or not self.preview_enabled:
            return

        try:
            frame = self.picam2.capture_array()
            h, w, ch = frame.shape

            qimg = QImage(frame.data, w, h, ch * w, QImage.Format.Format_RGB888)

            pix = QPixmap.fromImage(qimg).scaled(
                self.preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            self.preview.setPixmap(pix)

        except Exception as e:
            self.status.setText(str(e))

    def apply_controls(self):
        if self.busy:
            return

        try:
            self.busy = True
            self.preview_enabled = False

            ae = self.chk_ae.isChecked()
            awb = self.chk_awb.isChecked()

            controls = {
                "AeEnable": ae,
                "AwbEnable": awb,
            }

            if ae:
                controls["ExposureValue"] = float(self.exp_value.value())
            else:
                controls["ExposureTime"] = int(self.exp_time.value())
                controls["AnalogueGain"] = float(self.gain.value())

            if not awb:
                controls["ColourGains"] = (
                    float(self.red_gain.value()),
                    float(self.blue_gain.value())
                )

            self.picam2.set_controls(controls)

            self.status.setText(f"Applied:\n{controls}")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

        finally:
            self.preview_enabled = True
            self.busy = False

    def take_photo(self):
        if self.busy:
            return

        try:
            self.busy = True
            self.preview_enabled = False

            filename = os.path.join(MEDIA_DIR, f"photo_{self.ts()}.jpg")

            self.picam2.switch_mode_and_capture_file(
                self.picam2.create_still_configuration(),
                filename
            )

            self.status.setText(f"Saved: {os.path.basename(filename)}")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

        finally:
            self.preview_enabled = True
            self.busy = False

    def closeEvent(self, event):
        try:
            self.picam2.stop()
        except Exception:
            pass
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    font = QFont()
    font.setPointSize(11)
    app.setFont(font)

    w = CameraWindow()
    w.show()

    sys.exit(app.exec())