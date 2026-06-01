"""
Spectrometer Service
Handles control commands for the spectrometer API on Raspberry Pi.
Spectrum data is received via SSE stream in SpectrumThread (analogous to CameraThread).
This service only handles control operations: integral time, dark spectrum, save, info.
"""

import time
import logging
from typing import Optional, Dict, Any

import requests
from PyQt5.QtCore import QObject, pyqtSignal

from config.api_config import SPECTRUM_STREAM_URL, TIMEOUT_SECONDS, RETRY_ATTEMPTS, RETRY_DELAY

logger = logging.getLogger(__name__)


class SpectrometerService(QObject):
    """Service for spectrometer control commands via streaming server HTTP API."""
    
    # Signals
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self):
        super().__init__()
        # Control endpoints live on the same host:port as the SSE stream
        self.base_url = SPECTRUM_STREAM_URL.rsplit("/spectrum", 1)[0]
    
    def _make_request(self, path: str, method: str = "GET", params: Optional[Dict] = None) -> Optional[Dict]:
        """Make HTTP request with retry logic."""
        url = f"{self.base_url}{path}"
            
        for attempt in range(RETRY_ATTEMPTS):
            try:
                if method == "GET":
                    response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
                else:
                    logger.error(f"Unsupported method: {method}")
                    return None
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Request failed with status {response.status_code}: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < RETRY_ATTEMPTS - 1:
                    time.sleep(RETRY_DELAY)
                    
        return None
    
    def set_integral_time(self, integral_time: int) -> bool:
        """Set spectrometer integral time."""
        try:
            response = self._make_request(
                "/control/set_integral_time", params={"time": integral_time}
            )
            return response is not None and response.get("success", False)
        except Exception as e:
            logger.error(f"Failed to set integral time: {e}")
            self.error_occurred.emit(f"Failed to set integral time: {e}")
            return False
    
    def set_dark_spectrum(self) -> bool:
        """Set dark spectrum."""
        try:
            response = self._make_request("/control/set_dark_spectrum")
            return response is not None and response.get("success", False)
        except Exception as e:
            logger.error(f"Failed to set dark spectrum: {e}")
            self.error_occurred.emit(f"Failed to set dark spectrum: {e}")
            return False
    
    def clear_dark_spectrum(self) -> bool:
        """Clear dark spectrum."""
        try:
            response = self._make_request("/control/clear_dark_spectrum")
            return response is not None and response.get("success", False)
        except Exception as e:
            logger.error(f"Failed to clear dark spectrum: {e}")
            self.error_occurred.emit(f"Failed to clear dark spectrum: {e}")
            return False
    
    def save_spectrum(self, directory: str, filename: Optional[str] = None) -> bool:
        """Save current spectrum to file via single-shot endpoint."""
        try:
            response = self._make_request("/spectrum/single")
            if response is None:
                return False
            # Spectrum data received — save locally
            import numpy as np, os
            from datetime import datetime
            wavelength = response.get("wavelength", [])
            spectrum = response.get("spectrum", [])
            if not wavelength or not spectrum:
                return False
            os.makedirs(directory, exist_ok=True)
            if not filename:
                filename = f"spectrum_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = os.path.join(directory, filename)
            data = np.column_stack((wavelength, spectrum))
            np.savetxt(filepath, data, fmt="%.6f", header="Wavelength Intensity")
            logger.info(f"Spectrum saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save spectrum: {e}")
            self.error_occurred.emit(f"Failed to save spectrum: {e}")
            return False
    
    def get_spectrometer_info(self) -> Optional[Dict[str, Any]]:
        """Get spectrometer information."""
        try:
            return self._make_request("/info")
        except Exception as e:
            logger.error(f"Failed to get spectrometer info: {e}")
            return None
