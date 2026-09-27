"""
Connection Settings Dialog
Lets the user set the Raspberry Pi address manually or find it automatically
in the local network (mDNS hostname lookup, then a subnet scan).
"""

import logging

from PyQt5.QtCore import QRegExp, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QRegExpValidator
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QProgressBar, QPushButton, QVBoxLayout
)

from config import api_config
from services.raspberry_discovery import discover_raspberry, probe_host

logger = logging.getLogger(__name__)

_IP_REGEXP = QRegExp(
    r"^((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)$"
)


class DiscoveryWorker(QThread):
    """Searches for the Raspberry Pi off the GUI thread."""

    progress = pyqtSignal(int, int)
    finished_with_result = pyqtSignal(str)

    def __init__(self, port: int, parent=None):
        super().__init__(parent)
        self._port = port
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            ip = discover_raspberry(
                self._port,
                progress_callback=lambda done, total: self.progress.emit(done, total),
                is_cancelled=lambda: self._cancelled,
            )
        except Exception as e:
            logger.error(f"Raspberry Pi discovery failed: {e}")
            ip = None
        self.finished_with_result.emit(ip or "")


class ConnectionSettingsDialog(QDialog):
    """Modal dialog for configuring the Raspberry Pi connection."""

    address_changed = pyqtSignal(str)

    def __init__(self, interface_text=None, parent=None):
        super().__init__(parent)
        self.interface_text = interface_text
        self._worker = None
        self._build_ui()
        self.ip_edit.setText(api_config.get_raspberry_ip())

    # ------------------------------------------------------------------ #
    #  helpers                                                             #
    # ------------------------------------------------------------------ #

    def _t(self, key: str, fallback: str) -> str:
        """Return translated string or fallback."""
        if self.interface_text is not None:
            return getattr(self.interface_text, key, lambda: fallback)()
        return fallback

    # ------------------------------------------------------------------ #
    #  UI construction                                                     #
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        title = self._t("connection_settings_title", "Connection Settings")
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(420)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setSpacing(10)

        self.ip_edit = QLineEdit()
        self.ip_edit.setValidator(QRegExpValidator(_IP_REGEXP, self))
        self.ip_edit.setPlaceholderText("192.168.1.42")
        form.addRow(self._t("raspberry_ip", "Raspberry Pi IP:"), self.ip_edit)
        main_layout.addLayout(form)

        buttons_row = QHBoxLayout()
        self.find_btn = QPushButton(self._t("find_raspberry", "Find Raspberry"))
        self.find_btn.clicked.connect(self._on_find)
        buttons_row.addWidget(self.find_btn)

        self.test_btn = QPushButton(self._t("test_connection", "Test connection"))
        self.test_btn.clicked.connect(self._on_test)
        buttons_row.addWidget(self.test_btn)
        buttons_row.addStretch()
        main_layout.addLayout(buttons_row)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        main_layout.addWidget(self.progress)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: gray;")
        main_layout.addWidget(self.status_label)

        note = QLabel(self._t("apply_restart", "Apply (restart required for full effect)"))
        note.setWordWrap(True)
        note.setStyleSheet("color: gray; font-size: 10pt;")
        main_layout.addWidget(note)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._on_ok)
        btn_box.rejected.connect(self.reject)
        main_layout.addWidget(btn_box)

    # ------------------------------------------------------------------ #
    #  actions                                                             #
    # ------------------------------------------------------------------ #

    def _on_find(self):
        """Start background auto-discovery of the Raspberry Pi."""
        if self._worker is not None:
            return

        self.find_btn.setEnabled(False)
        self.test_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.status_label.setText(self._t("searching_raspberry", "Searching for Raspberry Pi..."))

        self._worker = DiscoveryWorker(api_config.get_api_port(), self)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_with_result.connect(self._on_found)
        self._worker.start()

    def _on_progress(self, done: int, total: int):
        self.progress.setRange(0, total)
        self.progress.setValue(done)

    def _on_found(self, ip: str):
        self.progress.setVisible(False)
        self.find_btn.setEnabled(True)
        self.test_btn.setEnabled(True)
        self._worker = None

        if ip:
            self.ip_edit.setText(ip)
            self.status_label.setText(
                self._t("raspberry_found", "Raspberry Pi found: {}").format(ip)
            )
        else:
            self.status_label.setText(
                self._t("raspberry_not_found", "Raspberry Pi not found in the local network")
            )

    def _on_test(self):
        """Check that the API server answers on the entered address."""
        ip = self.ip_edit.text().strip()
        if not ip:
            return
        self.status_label.setText(self._t("checking_connection", "Checking connection..."))
        if probe_host(ip, api_config.get_api_port(), timeout=2.0):
            self.status_label.setText(self._t("connection_ok", "Connection OK"))
        else:
            self.status_label.setText(self._t("connection_failed", "No response from {}").format(ip))

    def _on_ok(self):
        ip = self.ip_edit.text().strip()
        if not ip:
            self.reject()
            return
        if ip != api_config.get_raspberry_ip():
            api_config.set_raspberry_ip(ip)
            self.address_changed.emit(ip)
        self.accept()

    def reject(self):
        if self._worker is not None:
            self._worker.cancel()
        super().reject()
