"""
API Client Thread
Background thread for non-blocking API requests.
"""

import json
import logging
from typing import Any

import requests
from PyQt5.QtCore import QThread, pyqtSignal

from config.api_config import TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


class APIClientThread(QThread):
    """Thread for making API calls to avoid blocking the UI."""
    response_received = pyqtSignal(bool, str, dict)

    def __init__(self, method: str, url: str, data: dict[str, Any] | None = None,
                 timeout: float | None = None):
        super().__init__()
        self.method = method.upper()
        self.url = url
        self.data = data
        self.timeout = timeout or TIMEOUT_SECONDS

    def run(self) -> None:
        """Execute the API request."""
        try:
            headers = {'Content-Type': 'application/json'}

            if self.method == 'GET':
                response = requests.get(self.url, timeout=self.timeout)
            elif self.method == 'POST':
                response = requests.post(self.url, json=self.data, headers=headers, timeout=self.timeout)
            else:
                logger.error(f"Unsupported method: {self.method}")
                self.response_received.emit(False, f"Unsupported method: {self.method}", {})
                return

            if response.status_code == 200:
                self.response_received.emit(True, "Success", response.json())
            elif response.status_code == 422:
                error_data = response.json()
                detail = error_data.get('detail', [])
                if isinstance(detail, list) and detail:
                    error_msg = f"Validation error: {detail[0].get('msg', 'Unknown validation error')}"
                else:
                    error_msg = f"Validation error: {error_data.get('detail', 'Unknown error')}"
                logger.warning(f"API validation error: {error_msg}")
                self.response_received.emit(False, error_msg, {})
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail') or error_data.get('error') or f"HTTP {response.status_code}: {response.text}"
                except (ValueError, json.JSONDecodeError):
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"API error: {error_msg}")
                self.response_received.emit(False, error_msg, {})

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {e}")
            self.response_received.emit(False, f"Network error: {e!s}", {})
        except (KeyError, RuntimeError, TypeError, ValueError) as e:
            logger.error(f"Unexpected error in API request: {e}")
            self.response_received.emit(False, f"Error: {e!s}", {})
