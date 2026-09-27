"""
Connection Dialog
Shown at application startup to discover and select a Raspberry Pi device
on the local network before the main window opens.

The dialog:
 - Automatically scans the local subnet for MIP API servers.
 - Displays discovered devices in a list with IP, hostname, and response time.
 - Allows the user to enter an IP address manually.
 - Returns the selected IP (and port) so the caller can configure api_config.
"""

import logging
from typing import Optional, Tuple

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QProgressBar,
    QFrame, QApplication, QMessageBox,
)

from services.network_discovery import (
    DiscoveredDevice, discover_devices, probe_single,
)

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
#  Background scanner thread                                          #
# ------------------------------------------------------------------ #

class _ScanWorker(QThread):
    """Run network discovery off the GUI thread."""

    device_found = pyqtSignal(object)   # DiscoveredDevice
    scan_finished = pyqtSignal(int)     # total devices found

    def __init__(self, port: int, saved_ip: Optional[str] = None, parent=None):
        super().__init__(parent)
        self._port = port
        self._saved_ip = saved_ip

    def run(self):
        extra = [self._saved_ip] if self._saved_ip else None
        devices = discover_devices(port=self._port, extra_ips=extra)
        for dev in devices:
            self.device_found.emit(dev)
        self.scan_finished.emit(len(devices))


class _ProbeWorker(QThread):
    """Probe a single IP (manual entry validation)."""

    result = pyqtSignal(object)  # DiscoveredDevice | None

    def __init__(self, ip: str, port: int, parent=None):
        super().__init__(parent)
        self._ip = ip
        self._port = port

    def run(self):
        dev = probe_single(self._ip, self._port)
        self.result.emit(dev)


# ------------------------------------------------------------------ #
#  Connection Dialog                                                   #
# ------------------------------------------------------------------ #

class ConnectionDialog(QDialog):
    """
    Modal dialog for selecting a Raspberry Pi device on the network.

    After ``exec_()`` returns ``QDialog.Accepted``, call
    :pyattr:`selected_ip` and :pyattr:`selected_port` to get the result.
    """

    def __init__(
        self,
        interface_text=None,
        saved_ip: Optional[str] = None,
        api_port: int = 8000,
        parent=None,
    ):
        super().__init__(parent)
        self._interface_text = interface_text
        self._saved_ip = saved_ip
        self._api_port = api_port
        self._devices: list[DiscoveredDevice] = []
        self._scan_worker: Optional[_ScanWorker] = None
        self._probe_worker: Optional[_ProbeWorker] = None

        # Result
        self.selected_ip: Optional[str] = None
        self.selected_port: int = api_port

        self._build_ui()

        # Auto-start scan after dialog is shown
        QTimer.singleShot(100, self._start_scan)

    # ------------------------------------------------------------------ #
    #  i18n helper                                                        #
    # ------------------------------------------------------------------ #

    def _t(self, key: str, fallback: str) -> str:
        if self._interface_text is not None:
            return getattr(self._interface_text, key, lambda: fallback)()
        return fallback

    # ------------------------------------------------------------------ #
    #  UI                                                                  #
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        self.setWindowTitle(self._t("discovery_title", "Connect to Raspberry Pi"))
        self.setModal(True)
        self.setMinimumSize(520, 420)
        self.resize(560, 480)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        # Title
        title = QLabel(self._t("discovery_title", "Connect to Raspberry Pi"))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        root.addWidget(title)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        root.addWidget(sep)

        # Subtitle / description
        desc = QLabel(self._t(
            "discovery_desc",
            "Scanning the local network for devices..."
        ))
        desc.setWordWrap(True)
        root.addWidget(desc)
        self._desc_label = desc

        # Progress bar (indeterminate while scanning)
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # indeterminate
        self._progress.setTextVisible(False)
        self._progress.setMaximumHeight(6)
        root.addWidget(self._progress)

        # Device list
        self._list = QListWidget()
        self._list.setMinimumHeight(140)
        self._list.itemDoubleClicked.connect(self._on_connect)
        self._list.currentRowChanged.connect(self._on_selection_changed)
        root.addWidget(self._list, stretch=1)

        # Manual entry row
        manual_row = QHBoxLayout()
        manual_label = QLabel(self._t("discovery_manual_ip", "IP address:"))
        manual_row.addWidget(manual_label)
        self._ip_edit = QLineEdit()
        self._ip_edit.setPlaceholderText("192.168.1.100")
        if self._saved_ip:
            self._ip_edit.setText(self._saved_ip)
        manual_row.addWidget(self._ip_edit, stretch=1)
        self._check_btn = QPushButton(self._t("discovery_check", "Check"))
        self._check_btn.clicked.connect(self._on_check_manual)
        manual_row.addWidget(self._check_btn)
        root.addLayout(manual_row)

        # Status label
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: gray; font-size: 10pt;")
        root.addWidget(self._status_label)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._rescan_btn = QPushButton(self._t("discovery_rescan", "Rescan"))
        self._rescan_btn.clicked.connect(self._start_scan)
        btn_row.addWidget(self._rescan_btn)

        self._connect_btn = QPushButton(self._t("discovery_connect", "Connect"))
        self._connect_btn.setEnabled(False)
        self._connect_btn.setDefault(True)
        self._connect_btn.clicked.connect(self._on_connect)
        btn_row.addWidget(self._connect_btn)

        root.addLayout(btn_row)

    # ------------------------------------------------------------------ #
    #  Scanning                                                            #
    # ------------------------------------------------------------------ #

    def _start_scan(self):
        # Reset state
        self._list.clear()
        self._devices.clear()
        self._connect_btn.setEnabled(False)
        self._progress.setRange(0, 0)
        self._progress.show()
        self._status_label.setText(
            self._t("discovery_scanning", "Scanning...")
        )
        self._desc_label.setText(
            self._t("discovery_desc", "Scanning the local network for devices...")
        )
        self._rescan_btn.setEnabled(False)

        worker = _ScanWorker(self._api_port, self._saved_ip, self)
        worker.device_found.connect(self._on_device_found)
        worker.scan_finished.connect(self._on_scan_finished)
        worker.finished.connect(worker.deleteLater)
        self._scan_worker = worker
        worker.start()

    def _on_device_found(self, device: DiscoveredDevice):
        # Skip duplicates (may arrive from scan + manual check simultaneously)
        for d in self._devices:
            if d.ip == device.ip and d.port == device.port:
                return

        self._devices.append(device)
        item = QListWidgetItem(
            f"{device.display_name}   [{device.response_time_ms:.0f} ms]"
        )
        item.setData(Qt.UserRole, len(self._devices) - 1)
        self._list.addItem(item)

        # Auto-select first item
        if self._list.count() == 1:
            self._list.setCurrentRow(0)

    def _on_scan_finished(self, count: int):
        self._progress.setRange(0, 1)
        self._progress.setValue(1)
        self._progress.hide()
        self._rescan_btn.setEnabled(True)

        if count == 0:
            self._status_label.setText(
                self._t("discovery_not_found",
                         "No devices found. Enter IP manually or rescan.")
            )
            self._desc_label.setText(
                self._t("discovery_not_found_desc",
                         "No MIP devices were detected on the local network.")
            )
        else:
            self._status_label.setText(
                self._t("discovery_found", "Found {count} device(s)").replace(
                    "{count}", str(count)
                )
            )
            self._desc_label.setText(
                self._t("discovery_found_desc",
                         "Select a device from the list and click Connect.")
            )

    def _on_selection_changed(self, row: int):
        self._connect_btn.setEnabled(row >= 0)

    # ------------------------------------------------------------------ #
    #  Manual check                                                        #
    # ------------------------------------------------------------------ #

    def _on_check_manual(self):
        ip = self._ip_edit.text().strip()
        if not ip:
            return
        self._check_btn.setEnabled(False)
        self._status_label.setText(
            self._t("discovery_checking", "Checking {ip}...").replace("{ip}", ip)
        )

        worker = _ProbeWorker(ip, self._api_port, self)
        worker.result.connect(self._on_probe_result)
        worker.finished.connect(worker.deleteLater)
        self._probe_worker = worker
        worker.start()

    def _on_probe_result(self, device):
        self._check_btn.setEnabled(True)
        if device is None:
            self._status_label.setText(
                self._t("discovery_check_fail",
                         "Device not responding. Check IP and try again.")
            )
            return

        # Add to list if not already present
        for d in self._devices:
            if d.ip == device.ip:
                self._status_label.setText(
                    self._t("discovery_already_listed",
                             "Device already in the list.")
                )
                return

        self._on_device_found(device)
        self._list.setCurrentRow(self._list.count() - 1)
        self._status_label.setText(
            self._t("discovery_check_ok", "Device found!")
        )

    # ------------------------------------------------------------------ #
    #  Actions                                                             #
    # ------------------------------------------------------------------ #

    def _on_connect(self):
        """Accept selected device or use manual IP."""
        row = self._list.currentRow()
        if row >= 0:
            idx = self._list.item(row).data(Qt.UserRole)
            dev = self._devices[idx]
            self.selected_ip = dev.ip
            self.selected_port = dev.port
        else:
            # Fallback to manual entry
            ip = self._ip_edit.text().strip()
            if not ip:
                return
            self.selected_ip = ip
            self.selected_port = self._api_port
        self.accept()


