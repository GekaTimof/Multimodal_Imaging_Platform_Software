"""
Spectrometer Service
Handles communication with the spectrometer API on Raspberry Pi.
"""

import requests
import numpy as np
from typing import Optional, Tuple, Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import logging

from ..config.api_config import API_BASE_URL, TIMEOUT_SECONDS, RETRY_ATTEMPTS, RETRY_DELAY

logger = logging.getLogger(__name__)


class SpectrometerService(QObject):
    """Service for managing spectrometer communication via API."""
    
    # Signals
    spectrum_received = pyqtSignal(np.ndarray, np.ndarray)  # x_data, y_data
    connection_status_changed = pyqtSignal(bool)  # connected/disconnected
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self):
        super().__init__()
        self.base_url = API_BASE_URL
        self.is_connected = False
        self.spectrum_timer = QTimer()
        self.spectrum_timer.timeout.connect(self.request_spectrum)
        self.current_x_data = None
        self.current_y_data = None
        
    def get_spectrometer_endpoints(self) -> Dict[str, str]:
        """Get spectrometer API endpoints."""
        return {
            "status": f"{self.base_url}/spectrometer/status",
            "connect": f"{self.base_url}/spectrometer/connect",
            "disconnect": f"{self.base_url}/spectrometer/disconnect",
            "get_spectrum": f"{self.base_url}/spectrometer/spectrum",
            "set_integral_time": f"{self.base_url}/spectrometer/integral_time",
            "set_dark_spectrum": f"{self.base_url}/spectrometer/dark_spectrum/set",
            "clear_dark_spectrum": f"{self.base_url}/spectrometer/dark_spectrum/clear",
            "save_spectrum": f"{self.base_url}/spectrometer/save",
            "get_wavelength_range": f"{self.base_url}/spectrometer/wavelength_range",
            "get_info": f"{self.base_url}/spectrometer/info"
        }
    
    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Dict]:
        """Make HTTP request with retry logic."""
        endpoints = self.get_spectrometer_endpoints()
        url = endpoints.get(endpoint)
        if not url:
            logger.error(f"Unknown endpoint: {endpoint}")
            return None
            
        for attempt in range(RETRY_ATTEMPTS):
            try:
                if method == "GET":
                    response = requests.get(url, timeout=TIMEOUT_SECONDS)
                elif method == "POST":
                    response = requests.post(url, json=data, timeout=TIMEOUT_SECONDS)
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
                    import time
                    time.sleep(RETRY_DELAY)
                    
        return None
    
    def check_connection(self) -> bool:
        """Check if spectrometer is connected and available."""
        try:
            response = self._make_request("status")
            if response and response.get("connected", False):
                if not self.is_connected:
                    self.is_connected = True
                    self.connection_status_changed.emit(True)
                return True
            else:
                if self.is_connected:
                    self.is_connected = False
                    self.connection_status_changed.emit(False)
                return False
        except Exception as e:
            logger.error(f"Connection check failed: {e}")
            if self.is_connected:
                self.is_connected = False
                self.connection_status_changed.emit(False)
            return False
    
    def connect_spectrometer(self) -> bool:
        """Connect to spectrometer."""
        try:
            response = self._make_request("connect", "POST")
            if response and response.get("success", False):
                self.is_connected = True
                self.connection_status_changed.emit(True)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to connect spectrometer: {e}")
            self.error_occurred.emit(f"Failed to connect: {e}")
            return False
    
    def disconnect_spectrometer(self) -> bool:
        """Disconnect from spectrometer."""
        try:
            self.stop_spectrum_stream()
            response = self._make_request("disconnect", "POST")
            self.is_connected = False
            self.connection_status_changed.emit(False)
            return response and response.get("success", False)
        except Exception as e:
            logger.error(f"Failed to disconnect spectrometer: {e}")
            return False
    
    def request_spectrum(self) -> bool:
        """Request current spectrum data."""
        if not self.is_connected:
            return False
            
        try:
            response = self._make_request("get_spectrum")
            if response:
                x_data = np.array(response.get("wavelengths", []))
                y_data = np.array(response.get("intensities", []))
                
                if len(x_data) > 0 and len(y_data) > 0:
                    self.current_x_data = x_data
                    self.current_y_data = y_data
                    self.spectrum_received.emit(x_data, y_data)
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to get spectrum: {e}")
            self.error_occurred.emit(f"Failed to get spectrum: {e}")
            return False
    
    def start_spectrum_stream(self, interval_ms: int = 100):
        """Start continuous spectrum streaming."""
        if self.is_connected:
            self.spectrum_timer.start(interval_ms)
    
    def stop_spectrum_stream(self):
        """Stop spectrum streaming."""
        self.spectrum_timer.stop()
    
    def set_integral_time(self, integral_time: int) -> bool:
        """Set spectrometer integral time."""
        try:
            response = self._make_request("set_integral_time", "POST", {"integral_time": integral_time})
            return response and response.get("success", False)
        except Exception as e:
            logger.error(f"Failed to set integral time: {e}")
            self.error_occurred.emit(f"Failed to set integral time: {e}")
            return False
    
    def set_dark_spectrum(self) -> bool:
        """Set dark spectrum."""
        try:
            response = self._make_request("set_dark_spectrum", "POST")
            return response and response.get("success", False)
        except Exception as e:
            logger.error(f"Failed to set dark spectrum: {e}")
            self.error_occurred.emit(f"Failed to set dark spectrum: {e}")
            return False
    
    def clear_dark_spectrum(self) -> bool:
        """Clear dark spectrum."""
        try:
            response = self._make_request("clear_dark_spectrum", "POST")
            return response and response.get("success", False)
        except Exception as e:
            logger.error(f"Failed to clear dark spectrum: {e}")
            self.error_occurred.emit(f"Failed to clear dark spectrum: {e}")
            return False
    
    def save_spectrum(self, directory: str, filename: Optional[str] = None) -> bool:
        """Save current spectrum to file."""
        try:
            data = {"directory": directory}
            if filename:
                data["filename"] = filename
            response = self._make_request("save_spectrum", "POST", data)
            return response and response.get("success", False)
        except Exception as e:
            logger.error(f"Failed to save spectrum: {e}")
            self.error_occurred.emit(f"Failed to save spectrum: {e}")
            return False
    
    def get_wavelength_range(self) -> Optional[np.ndarray]:
        """Get wavelength range from spectrometer."""
        try:
            response = self._make_request("get_wavelength_range")
            if response:
                return np.array(response.get("wavelengths", []))
            return None
        except Exception as e:
            logger.error(f"Failed to get wavelength range: {e}")
            return None
    
    def get_spectrometer_info(self) -> Optional[Dict[str, Any]]:
        """Get spectrometer information."""
        try:
            return self._make_request("get_info")
        except Exception as e:
            logger.error(f"Failed to get spectrometer info: {e}")
            return None
    
    def get_current_spectrum(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Get the most recent spectrum data."""
        return self.current_x_data, self.current_y_data
