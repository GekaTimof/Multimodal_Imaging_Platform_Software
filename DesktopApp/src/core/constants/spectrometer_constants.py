"""
Spectrometer Constants
Constants related to spectrometer operations and settings.
"""

# Spectrometer display ranges
WAVELENGTH_MIN = 200
WAVELENGTH_MAX = 1100
SPECTRUM_Y_MAX = 65535

# Default spectrometer settings
DEFAULT_INTEGRAL_TIME = 100
DEFAULT_STREAM_INTERVAL_MS = 100

# Spectrometer graph settings
GRAPH_PADDING = 0
OVERILLUMINATION_COLOR = 'r'
OVERILLUMINATION_TEXT = "OVERILLUMINATION WARNING"
OVERILLUMINATION_FONT = "Arial"
OVERILLUMINATION_FONT_SIZE = 12

# Coordinate display settings
COORD_FONT = "Arial"
COORD_FONT_SIZE = 8
COORD_COLOR = 'k'

# Graph range margins
VIEW_MARGIN_X_PERCENT = 0.04
VIEW_MARGIN_Y_PERCENT = 0.05

# Thread settings
SPECTRUM_THREAD_SLEEP_MS = 100
