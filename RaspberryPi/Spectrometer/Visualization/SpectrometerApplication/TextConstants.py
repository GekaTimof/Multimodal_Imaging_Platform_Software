# Application text

#---------------------------------------------------- NOT User Zone ----------------------------------------------------

# Array of all application languages
APPLICATION_LANGUAGES = ['en', 'ru']

# application window text
WINDOW_TITLE = {'en': "Real-time Graph", 'ru': "График в реальном времени"}
LEFT_GRAPHIC_LABEL = {'en': "Intensity, intensity counts", 'ru': "Интенсивность, значение интенсивности"}
BOTTOM_GRAPHIC_LABEL = {'en': "Wavelength, nm", 'ru': "Длина волны, нм"}

# input directory field text
INPUT_DIRECTORY_LABEL = {'en': "Save Directory:", 'ru': "Каталог для сохранения:"}
INPUT_PLACEHOLDER_TEXT = {'en': "No Folder Selected", 'ru': "Папка не выбрана"}
INPUT_DIRECTORY_BUTTON = {'en': "Select", 'ru': "Выбрать"}
INPUT_DIRECTORY_WINDOW_NAME = {'en': "Select Directory", 'ru': "Выбор каталога"}

# directory selector function text
SELECT_DIRECTORY_FILE_DIALOG = {'en': "Select Directory", 'ru': "Выбор каталога"}

# select directory warnings
WARNING_SELECT_OUT_OF_HOME = {
    'en': "Access Denied.\n⚠ You can only select folders in your home directory!",
    'ru': "Доступ запрещён.\n⚠ Вы можете выбирать только папки в домашнем каталоге!"
}

# save file to directory button text
SAVE_SPECTROMETER_DATA_BUTTON = {'en': "Save Data", 'ru': "Сохранить данные"}

# save file warnings and critical
WARNING_NO_DIRECTORY_SELECTED = {
    'en': "No directory selected.\nPlease select a directory to save the data.",
    'ru': "Каталог не выбран.\nПожалуйста, выберите каталог для сохранения данных."
}
WARNING_SAWING_OUT_OF_HOME = {
    'en': "Access Denied.\n⚠ Saving outside the home directory is prohibited!",
    'ru': "Доступ запрещён.\n⚠ Сохранение вне домашнего каталога запрещено!"
}
CRITICAL_SAVING_FAILED = {
    'en': "Failed to save spectrum data.",
    'ru': "Не удалось сохранить спектральные данные."
}

# can't input data from file
WARNING_WRONG_DATA_FILE = {
    'en': "Error in file.\n⚠ Failed to extract contents!",
    'ru': "Ошибка в файле.\n⚠ не удалось извлечь содержимое!"
}

# input field to set integral time text
INPUT_INTEGRAL_TIME_LABEL = {'en': "Integral Time (ms):", 'ru': "Время накопления (мс):"}

# set dark spectrum button text
SET_DARK_SPECTRUM_BUTTON = {'en': "Set Dark Spectrum", 'ru': "Установить тёмный спектр"}

# clear dark spectrum button text
CLEAR_DARK_SPECTRUM_BUTTON = {'en': "Clear Dark Spectrum", 'ru': "Очистить тёмный спектр"}

# switch theme button
SWITCH_TO_LIGHT_THEME_BUTTON = {'en': "Switch to Light Theme", 'ru': "Переключиться на светлую тему"}
SWITCH_TO_DARK_THEME_BUTTON = {'en': "Switch to Dark Theme", 'ru': "Переключиться на тёмную тему"}

# reset zoom button text
RESET_ZOOM_BUTTON = {'en': "Reset Zoom", 'ru': "Сбросить масштаб"}

# overillumination warning massage text
OVERILLUMINATION_WARNING_TEXT = {'en': "Overillumination!", 'ru': "Пересвет!"}

# language selector label text
LANGUAGE_SELECTOR = {'en': "Language:", 'ru': "Язык:"}

# spectrum load button text
SPECTRUM_LOAD_BUTTON = {'en': "Select spectrum files", 'ru': "Выберите файл спектра"}

# name of window to get file with spectrum
SELECT_SPECTRUM_FILE_WINDOW_NAME = {'en': "Select spectrum files", 'ru': "Выберите файл спектра"}

# spectrum remove button text
SPECTRUM_REMOVE_BUTTON = {'en': "Remove selected spectrum", 'ru': "Удалить выбранный спектр"}

# run external process button text
EXTERNAL_PROCESS_BUTTON = {'en': "Generate Scilab script", 'ru': "Генерация Scilab скрипта"}

# warning title (for all warning windows)
WARNING_TITLE = {'en': "Warning", 'ru': "Предупреждение"}

# warn user that application will be quit, and new settings take effect after restart
WARNING_LANGUAGE_CHANGE_REQUIRES_RESTART = {'en': "After changing language application will be closed. Changes take effect after restart.",
                                'ru': "При смене языка приложение будет закрыто. Изменения вступят в силу после перезапуска."}

WARNING_NO_SPECTROMETER_CONNECTION = {'en': "Spectrometer is not connected, the application is running in an empty mode",
                                      'ru': "Спекстрометер не подключен, приложение запущено в пустом моде"}