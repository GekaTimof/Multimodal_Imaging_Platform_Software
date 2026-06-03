"""
UI Utilities
Shared helper functions for layout and sizing across all UI modules.
"""

from PyQt5.QtWidgets import QApplication

from config import interface_config


def get_relative_margin(base_em: float = 0.5) -> int:
    """Calculate margin/spacing relative to configured font size (in em units)."""
    current_font_size = interface_config.get('ui_scaling.font_point_size', 11)
    ui_scale = interface_config.get('ui_scaling.ui_scale_factor', 100) / 100
    return int(base_em * current_font_size * ui_scale)


def get_font_relative_size(base_em: float, base_font_size: int = 11) -> int:
    """Calculate pixel size relative to font size in em units with UI scaling."""
    current_font_size = interface_config.get('ui_scaling.font_point_size', base_font_size)
    ui_scale = interface_config.get('ui_scaling.ui_scale_factor', 100) / 100
    return int(base_em * current_font_size * ui_scale)


def get_scaled_size(base_size: int) -> int:
    """Calculate DPI-scaled size based on current screen DPI and UI scale factor."""
    screen = QApplication.primaryScreen()
    if screen:
        dpi = screen.logicalDotsPerInch()
        dpi_scaled = int(base_size * dpi / 96)
        ui_scale = interface_config.get('ui_scaling.ui_scale_factor', 100) / 100
        return int(dpi_scaled * ui_scale)
    return base_size
