"""
Spectrometer Service
Handles control commands for the spectrometer API on Raspberry Pi.
Supports both FastAPI endpoints (preferred) and legacy streaming server HTTP API.
Spectrum data is received via SSE stream in SpectrumThread.
This service handles control operations: integral time, dark spectrum, settings, info.
"""

import time
import logging
from typing import Optional, Dict, Any

import requests
from PyQt5.QtCore import QObject, pyqtSignal

from config.api_config import (
    SPECTRUM_STREAM_URL, TIMEOUT_SECONDS, RETRY_ATTEMPTS, RETRY_DELAY,
    ENDPOINTS, HEADERS
)

logger = logging.getLogger(__name__)


class SpectrometerService(QObject):
    """Service for spectrometer control commands via FastAPI and streaming server HTTP API."""
    
    # Signals
    error_occurred = pyqtSignal(str)  # error message
    settings_updated = pyqtSignal(dict)  # spectrometer settings updated
    
    def __init__(self):
        super().__init__()
        # Control endpoints live on the same host:port as the SSE stream
        self.base_url = SPECTRUM_STREAM_URL.rsplit("/spectrum", 1)[0]
        self.use_fastapi = True  # Prefer FastAPI endpoints
    
    def _make_request(self, path: str, method: str = "GET", params: Optional[Dict] = None, 
                    json_data: Optional[Dict] = None, use_fastapi: Optional[bool] = None) -> Optional[Dict]:
        """Make HTTP request with retry logic."""
        if use_fastapi is None:
            use_fastapi = self.use_fastapi
            
        if use_fastapi:
            # Use FastAPI endpoints
            url = ENDPOINTS.get(path, path)
            if not url.startswith('http'):
                url = f"{self.base_url}{url}"
        else:
            # Use legacy streaming server endpoints
            url = f"{self.base_url}{path}"
            
        for attempt in range(RETRY_ATTEMPTS):
            try:
                if method == "GET":
                    response = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT_SECONDS)
                elif method == "POST":
                    response = requests.post(url, params=params, json=json_data, headers=HEADERS, timeout=TIMEOUT_SECONDS)
                else:
                    logger.error(f"Unsupported method: {method}")
                    return None
                
                if response.status_code == 200:
                    try:
                        return response.json()
                    except ValueError:
                        return {"success": True}
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
            if self.use_fastapi:
                response = self._make_request(
                    "spectrometer_integral_time", method="POST", 
                    json_data={"integral_time": integral_time}
                )
            else:
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
            if self.use_fastapi:
                response = self._make_request("spectrometer_dark_capture", method="POST")
            else:
                response = self._make_request("/control/set_dark_spectrum")
            return response is not None and response.get("success", False)
        except Exception as e:
            logger.error(f"Failed to set dark spectrum: {e}")
            self.error_occurred.emit(f"Failed to set dark spectrum: {e}")
            return False
    
    def clear_dark_spectrum(self) -> bool:
        """Clear dark spectrum."""
        try:
            if self.use_fastapi:
                response = self._make_request("spectrometer_dark_clear", method="POST")
            else:
                response = self._make_request("/control/clear_dark_spectrum")
            return response is not None and response.get("success", False)
        except Exception as e:
            logger.error(f"Failed to clear dark spectrum: {e}")
            self.error_occurred.emit(f"Failed to clear dark spectrum: {e}")
            return False
    
    def save_spectrum(self, directory: str, filename: Optional[str] = None) -> bool:
        """Save current spectrum to file via single-shot endpoint."""
        try:
            if self.use_fastapi:
                response = self._make_request("spectrometer_spectrum")
            else:
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
            if self.use_fastapi:
                return self._make_request("spectrometer_info")
            else:
                return self._make_request("/info")
        except Exception as e:
            logger.error(f"Failed to get spectrometer info: {e}")
            return None
    
    def get_spectrometer_settings(self) -> Optional[Dict[str, Any]]:
        """Get spectrometer settings from database."""
        try:
            if self.use_fastapi:
                response = self._make_request("spectrometer_settings")
                return response
            else:
                # Legacy streaming server doesn't have settings endpoint
                logger.warning("Settings endpoint not available in legacy mode")
                return None
        except Exception as e:
            logger.error(f"Failed to get spectrometer settings: {e}")
            return None
    
    def update_spectrometer_settings(self, settings: Dict[str, Any]) -> bool:
        """Update spectrometer settings."""
        try:
            if self.use_fastapi:
                response = self._make_request(
                    "spectrometer_settings", method="POST", json_data=settings
                )
                if response and response.get("success"):
                    self.settings_updated.emit(settings)
                    return True
            else:
                logger.warning("Settings update not available in legacy mode")
                return False
        except Exception as e:
            logger.error(f"Failed to update spectrometer settings: {e}")
            self.error_occurred.emit(f"Failed to update settings: {e}")
            return False
    
    def load_dark_spectrum_file(self, filepath: str = None) -> bool:
        """Load dark spectrum from file path or standard location.
        
        Args:
            filepath: If provided, used for legacy mode. New API loads from standard location.
        """
        try:
            if self.use_fastapi:
                # New API loads from standard location on server, no parameters needed
                response = self._make_request("spectrometer_dark_load", method="POST")
            else:
                # Legacy mode requires file upload - not implemented
                logger.warning("Dark spectrum file loading not available in legacy mode")
                return False
            return response is not None and response.get("success", False)
        except Exception as e:
            logger.error(f"Failed to load dark spectrum file: {e}")
            self.error_occurred.emit(f"Failed to load dark spectrum file: {e}")
            return False
    
    def reconnect_spectrometer(self) -> bool:
        """Reinitialize spectrometer on Raspberry Pi (useful after hot-plug or startup failure)."""
        try:
            response = self._make_request("spectrometer_reconnect", method="POST")
            return response is not None and response.get("success", False)
        except Exception as e:
            logger.error(f"Failed to reconnect spectrometer: {e}")
            self.error_occurred.emit(f"Failed to reconnect spectrometer: {e}")
            return False

    def get_validation_rules(self) -> Optional[Dict[str, Any]]:
        """Get validation rules for spectrometer parameters."""
        try:
            if self.use_fastapi:
                response = self._make_request("spectrometer_validation")
                return response.get("data") if response else None
            else:
                # Return hardcoded rules for legacy mode
                return {
                    "integral_time_range": [1, 99999],
                    "overillumination_threshold_range": [0, 65535]
                }
        except Exception as e:
            logger.error(f"Failed to get validation rules: {e}")
            return None
