"""
Camera Constants
Constants related to camera operations and settings.
"""

# Default camera settings
DEFAULT_RESOLUTION_PHOTO = "3280x2464"
DEFAULT_RESOLUTION_VIDEO = "1920x1080"
DEFAULT_FPS = 20
DEFAULT_EXPOSURE_TIME = 10000
DEFAULT_ANALOGUE_GAIN = 1.0
DEFAULT_EXPOSURE_VALUE = 0.0
DEFAULT_RED_GAIN = 2.0
DEFAULT_BLUE_GAIN = 2.0

# Camera slots (0 = current session, 1-10 = saved presets)
MAX_CAMERA_SLOTS = 11
DEFAULT_CAMERA_SLOT = 0

# Thread settings
THREAD_TIMEOUT_MS = 3000
THREAD_WAIT_TIMEOUT = 1000

# Camera validation ranges
EXPOSURE_TIME_RANGE = (100, 300000000)  # 100 µs to 300 seconds (5 minutes)
ANALOGUE_GAIN_RANGE = (0.0, 32.0)
EXPOSURE_VALUE_RANGE = (-10.0, 10.0)
RED_GAIN_RANGE = (0.0, 8.0)
BLUE_GAIN_RANGE = (0.0, 8.0)

# Available resolutions (sorted by ascending resolution)
AVAILABLE_PHOTO_RESOLUTIONS = [
    '640x480',      # VGA - 4:3
    '800x600',      # SVGA - 4:3
    '1024x768',     # XGA - 4:3
    '1280x720',     # 720p HD - 16:9
    '1296x972',     # 4:3 mid-resolution
    '1640x1232',    # 4:3 aspect ratio
    '1920x1080',    # 1080p FHD - 16:9
    '2304x1296',    # 16:9 aspect ratio
    '2592x1944',    # High 4:3 resolution
    '3280x2464',    # Full 8MP resolution - 4:3
    '4608x2592',    # Full 12MP resolution - 16:9
]

AVAILABLE_VIDEO_RESOLUTIONS = [
    '640x480',      # VGA - 4:3
    '800x600',      # SVGA - 4:3
    '1024x768',     # XGA - 4:3
    '1280x720',     # 720p HD - 16:9
    '1296x972',     # 4:3 mid-resolution
    '1640x1232',    # 4:3 aspect ratio
    '1920x1080',    # 1080p FHD - 16:9
    '2304x1296',    # 16:9 aspect ratio
    '2592x1944',    # High 4:3 resolution
]

# Camera states
CAMERA_STATES = {
    'IDLE': 'idle',
    'STARTING': 'starting',
    'RUNNING': 'running',
    'STOPPING': 'stopping',
    'ERROR': 'error'
}

# Camera backends
CAMERA_BACKENDS = {
    'OPENCV': 'opencv',
    'PICAMERA2': 'picamera2',
    'RPICAM': 'rpicam',
    'TEST': 'test'
}

# Photo capture timing constants (matching RaspberryPi camera_service.py)
PHOTO_CAPTURE_PAUSE_OVERHEAD_S = 3.0  # Время на паузу видеопотока
PHOTO_CAPTURE_RESUME_OVERHEAD_S = 0.0  # Время на возобновление видеопотока
PHOTO_CAPTURE_SAFETY_MARGIN_S = 20.0  # Запас времени для HTTP таймаута

# Fallback values for capture duration estimation
PHOTO_CAPTURE_FALLBACK_DURATION_MS = 9_000  # 9 секунд по умолчанию
PHOTO_CAPTURE_FALLBACK_TIMEOUT_S = 33.0  # 33 секунды таймаут по умолчанию

# Exposure thresholds for timeout calculation (в секундах)
EXPOSURE_THRESHOLD_EXTREME = 60.0  # Экстремальная экспозиция (60с+)
EXPOSURE_THRESHOLD_VERY_LONG = 10.0  # Очень длинная экспозиция (10-60с)
EXPOSURE_THRESHOLD_LONG = 3.0  # Длинная экспозиция (3-10с)
EXPOSURE_THRESHOLD_MEDIUM = 1.0  # Средняя экспозиция (1-3с)

# Timeout additions for different exposure ranges (extreme, very_long, long, medium, short)
PHOTO_TIMEOUT_ADDITIONS = {
    'extreme': 30.0,
    'very_long': 15.0,
    'long': 15.0,
    'medium': 8.0,
    'short': 10.0
}

# Expected duration additions for different exposure ranges
PHOTO_EXPECTED_ADDITIONS = {
    'extreme': 10.0,
    'very_long': 7.0,
    'long': 6.0,
    'medium': 5.0,
    'short': 6.0
}
