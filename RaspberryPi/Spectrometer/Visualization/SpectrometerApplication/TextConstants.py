# Application text

#---------------------------------------------------- NOT User Zone ----------------------------------------------------

# Array of all application languages
APPLICATION_LANGUAGES = ['en', 'ru']

# application window text
WINDOW_TITLE = {'en': "Real-time Graph", 'ru': "Real-time Graph"}
LEFT_GRAPHIC_LABEL = {'en': "Intensity, intensity counts", 'ru': "Intensity, intensity counts"}
BOTTOM_GRAPHIC_LABEL = {'en': "Wavelength, nm", 'ru': "Wavelength, nm"}

# input directory field text
INPUT_DIRECTORY_LABEL = {'en': "Save Directory:", 'ru': "Save Directory:"}
INPUT_PLACEHOLDER_TEXT = {'en': "No Folder Selected", 'ru': "No Folder Selected"}
INPUT_DIRECTORY_BUTTON = {'en': "Select", 'ru': "Select"}
INPUT_DIRECTORY_WINDOW_NAME = {'en': "Select Directory", 'ru': "Select Directory"}

# directory selector function text
SELECT_DIRECTORY_FILE_DIALOG = {'en': "Select Directory", 'ru': "Select Directory"}

# select directory warnings
WARNING_SELECT_OUT_OF_HOME = {
    'en': "Access Denied.\nWARNING: You can only select folders in your home directory!",
    'ru': "Access Denied.\nWARNING: You can only select folders in your home directory!"
}

# save file to directory button text
SAVE_SPECTROMETER_DATA_BUTTON = {'en': "Save Data", 'ru': "Save Data"}

# save file warnings and critical
WARNING_NO_DIRECTORY_SELECTED = {
    'en': "No directory selected.\nPlease select a directory to save the data.",
    'ru': "No directory selected.\nPlease select a directory to save the data."
}
WARNING_SAWING_OUT_OF_HOME = {
    'en': "Access Denied.\nWARNING: Saving outside the home directory is prohibited!",
    'ru': "Access Denied.\nWARNING: Saving outside the home directory is prohibited!"
}
CRITICAL_SAVING_FAILED = {
    'en': "Failed to save spectrum data.",
    'ru': "Failed to save spectrum data."
}

# can't input data from file
WARNING_WRONG_DATA_FILE = {
    'en': "Error in file.\nWARNING: Failed to extract contents!",
    'ru': "Error in file.\nWARNING: Failed to extract contents!"
}

# input field to set integral time text
INPUT_INTEGRAL_TIME_LABEL = {'en': "Integral Time (ms):", 'ru': "Integral Time (ms):"}

# set dark spectrum button text
SET_DARK_SPECTRUM_BUTTON = {'en': "Set Dark Spectrum", 'ru': "Set Dark Spectrum"}

# clear dark spectrum button text
CLEAR_DARK_SPECTRUM_BUTTON = {'en': "Clear Dark Spectrum", 'ru': "Clear Dark Spectrum"}

# switch theme button
SWITCH_TO_LIGHT_THEME_BUTTON = {'en': "Switch to Light Theme", 'ru': "Switch to Light Theme"}
SWITCH_TO_DARK_THEME_BUTTON = {'en': "Switch to Dark Theme", 'ru': "Switch to Dark Theme"}

# reset zoom button text
RESET_ZOOM_BUTTON = {'en': "Reset Zoom", 'ru': "Reset Zoom"}

# overillumination warning massage text
OVERILLUMINATION_WARNING_TEXT = {'en': "Overillumination!", 'ru': "Overillumination!"}

# language selector label text
LANGUAGE_SELECTOR = {'en': "Language:", 'ru': "Language:"}

# spectrum load button text
SPECTRUM_LOAD_BUTTON = {'en': "Select spectrum files", 'ru': "Select spectrum files"}

# name of window to get file with spectrum
SELECT_SPECTRUM_FILE_WINDOW_NAME = {'en': "Select spectrum files", 'ru': "Select spectrum files"}

# spectrum remove button text
SPECTRUM_REMOVE_BUTTON = {'en': "Remove selected spectrum", 'ru': "Remove selected spectrum"}

# run external process button text
EXTERNAL_PROCESS_BUTTON = {'en': "Generate Scilab script", 'ru': "Generate Scilab script"}

# warning title (for all warning windows)
WARNING_TITLE = {'en': "Warning", 'ru': "Warning"}

# warn user that application will be quit, and new settings take effect after restart
WARNING_LANGUAGE_CHANGE_REQUIRES_RESTART = {'en': "After changing language application will be closed. Changes take effect after restart.",
                                'ru': "After changing language application will be closed. Changes take effect after restart."}

WARNING_NO_SPECTROMETER_CONNECTION = {'en': "Spectrometer is not connected, the application is running in an empty mode",
                                      'ru': "Spectrometer is not connected, the application is running in an empty mode"}
