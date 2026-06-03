"""
Interface Settings Dialog
Allows the user to configure UI scaling parameters: font size, font family,
status bar height, and side panel minimum width.
Settings are persisted via InterfaceConfig and applied immediately where possible.
"""

import logging
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLabel,
    QSpinBox, QComboBox, QVBoxLayout, QFrame
)
from config import interface_config

logger = logging.getLogger(__name__)


class InterfaceSettingsDialog(QDialog):
    """
    Modal dialog for editing interface scaling settings.

    Emits settings_applied when the user clicks Apply/OK so that
    the caller can refresh font / layout immediately.
    """

    settings_applied = pyqtSignal()

    def __init__(self, interface_text=None, parent=None):
        super().__init__(parent)
        self.interface_text = interface_text
        self._build_ui()
        self._load_current_values()

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
        title = self._t("interface_settings_title", "Interface Settings")
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Title label
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        # Form
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setSpacing(10)

        # Font family
        self.font_family_combo = QComboBox()
        available_fonts = QFontDatabase().families()
        common_fonts = ["DejaVu Sans", "Arial", "Helvetica", "Tahoma",
                        "Verdana", "Calibri", "Segoe UI", "Ubuntu",
                        "Liberation Sans", "Noto Sans"]
        for f in common_fonts:
            if f in available_fonts:
                self.font_family_combo.addItem(f)
        for f in available_fonts:
            if f not in common_fonts:
                self.font_family_combo.addItem(f)
        form.addRow(self._t("font_family", "Font family:"), self.font_family_combo)

        # Font size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(7, 24)
        self.font_size_spin.setSuffix(" pt")
        form.addRow(self._t("font_size", "Font size (pt):"), self.font_size_spin)

        # UI Scale factor (percentage)
        self.ui_scale_spin = QSpinBox()
        self.ui_scale_spin.setRange(80, 200)
        self.ui_scale_spin.setSuffix(" %")
        self.ui_scale_spin.setValue(100)
        form.addRow(self._t("ui_scale", "UI Scale (%):"), self.ui_scale_spin)

        # Error/status font size
        self.error_font_spin = QSpinBox()
        self.error_font_spin.setRange(7, 24)
        self.error_font_spin.setSuffix(" pt")
        form.addRow(self._t("error_font_size", "Status font size (pt):"), self.error_font_spin)

        # Side panel min width
        self.side_panel_spin = QSpinBox()
        self.side_panel_spin.setRange(160, 600)
        self.side_panel_spin.setSuffix(" px")
        form.addRow(self._t("side_panel_min_width", "Side panel min width (px):"), self.side_panel_spin)

        main_layout.addLayout(form)

        # Note label
        note = QLabel(self._t("apply_restart",
                               "Apply (restart required for full effect)"))
        note.setWordWrap(True)
        note.setStyleSheet("color: gray; font-size: 10pt;")
        main_layout.addWidget(note)

        # Buttons
        btn_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Reset
        )
        btn_box.accepted.connect(self._on_ok)
        btn_box.rejected.connect(self.reject)
        btn_box.button(QDialogButtonBox.Reset).clicked.connect(self._on_reset)
        main_layout.addWidget(btn_box)

    # ------------------------------------------------------------------ #
    #  data                                                                #
    # ------------------------------------------------------------------ #

    def _load_current_values(self):
        """Populate widgets with values from InterfaceConfig."""
        family = interface_config.get('ui_scaling.font_family', 'DejaVu Sans')
        idx = self.font_family_combo.findText(family)
        if idx >= 0:
            self.font_family_combo.setCurrentIndex(idx)

        self.font_size_spin.setValue(
            interface_config.get('ui_scaling.font_point_size', 11))
        self.ui_scale_spin.setValue(
            interface_config.get('ui_scaling.ui_scale_factor', 100))
        self.error_font_spin.setValue(
            interface_config.get('ui_scaling.error_font_size', 12))
        self.side_panel_spin.setValue(
            interface_config.get('ui_scaling.side_panel_min_width', 320))

    def _apply_values(self):
        """Save current widget values to InterfaceConfig."""
        interface_config.set('ui_scaling.font_family',
                             self.font_family_combo.currentText())
        interface_config.set('ui_scaling.font_point_size',
                             self.font_size_spin.value())
        interface_config.set('ui_scaling.ui_scale_factor',
                             self.ui_scale_spin.value())
        interface_config.set('ui_scaling.error_font_size',
                             self.error_font_spin.value())
        interface_config.set('ui_scaling.side_panel_min_width',
                             self.side_panel_spin.value())
        self.settings_applied.emit()
        logger.debug("Interface settings saved")

    def _on_ok(self):
        self._apply_values()
        self.accept()

    def _on_reset(self):
        """Reset to built-in defaults."""
        self.font_family_combo.setCurrentText('DejaVu Sans')
        self.font_size_spin.setValue(11)
        self.ui_scale_spin.setValue(100)
        self.error_font_spin.setValue(12)
        self.side_panel_spin.setValue(320)
