import base64
import logging

import requests
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage

from config.api_config import API_BASE_URL

logger = logging.getLogger(__name__)


class PhotoCaptureThread(QThread):
    """Thread for capturing a high-resolution photo via the RaspberryPi API.

    Signals:
        finished(image, photo_info)  – emitted on success; image is QImage, photo_info is dict
        failed(error_message)        – emitted on any error
    """

    finished = pyqtSignal(QImage, dict)
    failed = pyqtSignal(str)

    def __init__(self, timeout: float = 70.0):
        super().__init__()
        self.timeout = timeout

    def run(self):
        try:
            api_url = f"{API_BASE_URL}/camera/photo"
            logger.info(f"PhotoCaptureThread: POST {api_url}, timeout={self.timeout}s")
            response = requests.post(api_url, timeout=self.timeout)
            logger.info(f"PhotoCaptureThread: status={response.status_code}")

            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "image_base64" in data.get("data", {}):
                    image_base64 = data["data"]["image_base64"]
                    image_bytes = base64.b64decode(image_base64)

                    image = QImage.fromData(image_bytes, "JPEG")
                    if image.isNull():
                        image = QImage()
                        if not image.loadFromData(image_bytes):
                            self.failed.emit("Failed to decode image data")
                            return

                    self.finished.emit(image, data["data"])
                else:
                    self.failed.emit(data.get("message", "Unknown API error"))
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", error_msg)
                except Exception:
                    pass
                self.failed.emit(f"API request failed: {error_msg}")

        except requests.Timeout:
            self.failed.emit("Photo capture timeout (exposure too long?)")
        except Exception as e:
            logger.error(f"PhotoCaptureThread error: {e}")
            self.failed.emit(str(e))
