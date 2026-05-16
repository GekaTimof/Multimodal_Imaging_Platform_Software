import os
from pathlib import Path
from PyQt5.QtWidgets import QFileDialog, QMessageBox

def get_home_directory():
    return str(Path.home())

def is_path_inside(path: str, parent: str) -> bool:
    """
    Кроссплатформенная проверка: path находится внутри parent.
    Корректно работает на Windows (регистронезависимо) и Linux.
    """
    try:
        Path(os.path.abspath(path)).relative_to(os.path.abspath(parent))
        return True
    except ValueError:
        return False

def is_directory_allowed(directory):
    """
    Проверяет, что директория находится в домашней директории пользователя.

    Args:
        directory (str): Путь к директории для проверки.

    Returns:
        bool: True, если директория разрешена, иначе False.
    """
    return is_path_inside(directory, get_home_directory())

class DirectorySelector:
    def __init__(self, parent, interface_text, dir_input):
        self.parent = parent
        self.interface_text = interface_text
        self.dir_input = dir_input

    def select_directory(self):
        # get home directory of user in whose directory the program is located
        home_dir = get_home_directory()

        options = QFileDialog.Option.DontUseNativeDialog
        options |= QFileDialog.Option.ReadOnly

        # if user already select directory we will set it to selection field, if not select, we will set home directory
        current_directory = self.dir_input.text() if os.path.isdir(self.dir_input.text()) else home_dir

        directory = QFileDialog.getExistingDirectory(self.parent, self.interface_text.select_save_directory(),
                                                     current_directory, options)
        if directory:
            # check that user try to select folder in home directory
            if not is_path_inside(directory, home_dir):
                QMessageBox.warning(self.parent, self.interface_text.warning_title(),
                                    self.interface_text.warning_select_out_of_home())
                return

            self.dir_input.setText(directory)
