"""
Spectrum Streaming Thread
Reads SSE (Server-Sent Events) stream from RaspberryPi spectrum server,
analogous to CameraThread for the video stream.
"""

import json
import logging

import numpy as np
import requests
from PyQt5.QtCore import QThread, pyqtSignal

from config.api_config import SPECTRUM_STREAM_URL

logger = logging.getLogger(__name__)


class SpectrumThread(QThread):
    """Thread that reads an SSE spectrum stream and emits parsed data."""

    spectrum_ready = pyqtSignal(np.ndarray, np.ndarray)  # wavelengths, intensities
    status_ready = pyqtSignal(str)

    def __init__(self, stream_url: str = SPECTRUM_STREAM_URL):
        super().__init__()
        self.stream_url = stream_url
        self.running = False

    def run(self):
        try:
            self.status_ready.emit(f"Connecting to {self.stream_url}")
            response = requests.get(self.stream_url, stream=True, timeout=10)

            if response.status_code != 200:
                self.status_ready.emit(f"Spectrum stream error: HTTP {response.status_code}")
                return

            self.running = True
            self.status_ready.emit("Spectrometer started")

            buffer = ""
            # Larger chunk size reduces latency by minimizing HTTP read overhead
            for chunk in response.iter_content(chunk_size=4096, decode_unicode=True):
                if not self.running:
                    break

                buffer += chunk
                # SSE events are separated by double newlines
                while "\n\n" in buffer:
                    event_str, buffer = buffer.split("\n\n", 1)
                    self._parse_event(event_str)

        except requests.exceptions.ConnectionError as e:
            self.status_ready.emit(f"Spectrum stream connection failed: {e}")
        except requests.exceptions.Timeout:
            self.status_ready.emit("Spectrum stream connection timed out")
        except Exception as e:
            self.status_ready.emit(f"Spectrum stream error: {e}")
        finally:
            self.running = False
            self.status_ready.emit("Spectrometer stopped")

    def _parse_event(self, event_str: str):
        """Parse a single SSE event and emit spectrum data."""
        for line in event_str.split("\n"):
            if line.startswith("data: "):
                json_str = line[len("data: "):]
                try:
                    data = json.loads(json_str)
                    wavelengths = np.array(data.get("wavelength", []))
                    intensities = np.array(data.get("spectrum", []))
                    if len(wavelengths) > 0 and len(intensities) > 0:
                        self.spectrum_ready.emit(wavelengths, intensities)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse spectrum event: {e}")

    def stop(self):
        self.running = False

        # Wait for thread to finish
        if self.isRunning():
            if not self.wait(3000):  # Wait up to 3 seconds
                self.terminate()
                self.wait(1000)
