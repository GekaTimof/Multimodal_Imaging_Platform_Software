import os

from SpectrometerApplication.TextConstants import EXTERNAL_PROCESS_BUTTON

#------------------------------------------------------ User Zone ------------------------------------------------------

# Path to base save directory (directory to save spectrum datas)
BASE_FILES_DIR = "/home/evgeniy/Documents/Microscope_project/Spectrometer/save_data_folder"

# Path to start external process
EXTERNAL_PROCESS_PATH = ""

# Set Dark theme like base (True/False)
DARK_THEME = True

# Set base language ("en"/"ru")
BASE_LANGUAGE = "en"

# Font settings
FONT_SIZE = 14
FONT = "Arial"
WARNING_FONT_SIZE = 24
COORDINATES_FONT_SIZE = 11

# graph lines settings
LINE_WIGHT = 3

#---------------------------------------------------- NOT User Zone ----------------------------------------------------

# Path to base directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Link to file with application icon
Assets_directory_name = "Assets"
App_icon_name = "icon.png"
ASSETS_DIR = os.path.join(CURRENT_DIR, ".." , Assets_directory_name)
APP_ICON = os.path.join(ASSETS_DIR, App_icon_name)

# Minimum graphic Y
MIN_GRAPHIC_Y_RANGE = 1000

# Style for dark theme (this isn't full style settings)
DARK_THEME_STYLE = """
            QWidget {
                background-color: #2b2b2b;
                color: #f0f0f0;
            }
            QPushButton {
                background-color: #3c3f41;
                color: #ffffff;
            }
            QLineEdit, QSpinBox {
                background-color: #3c3f41;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            """