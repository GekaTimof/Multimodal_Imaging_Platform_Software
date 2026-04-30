import os
import pwd
from PyQt5.QtWidgets import QFileDialog, QMessageBox

def get_home_directory():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    dir_stat = os.stat(script_dir)
    user_info = pwd.getpwuid(dir_stat.st_uid)
    return user_info.pw_dir

def is_directory_allowed(directory):
    """
    Проверяет, что директория находится в домашней директории пользователя.

    Args:
        directory (str): Путь к директории для проверки.

    Returns:
        bool: True, если директория разрешена, иначе False.
    """
    home_dir = get_home_directory()
    return directory.startswith(home_dir)

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
            if not directory.startswith(home_dir):
                QMessageBox.warning(self.parent, self.interface_text.warning_title(),
                                    self.interface_text.warning_select_out_of_home())
                return

            self.dir_input.setText(directory)
