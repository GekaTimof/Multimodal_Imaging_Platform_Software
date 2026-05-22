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
DEFAULT_RED_GAIN = 1.0
DEFAULT_BLUE_GAIN = 1.0

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
RED_GAIN_RANGE = (0.1, 32.0)
BLUE_GAIN_RANGE = (0.1, 32.0)

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
