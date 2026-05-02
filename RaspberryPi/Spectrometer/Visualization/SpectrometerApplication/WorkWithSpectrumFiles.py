import os
import datetime
import pwd
import numpy as np

# text that separate session info and spectrum data
SPECTRUM_DATA_SEPARATOR = ">>>>> Begin Spectral Data <<<<<"


# function to generate array with X and Y (for saving text data)
def generate_spectrum_data_array(x_data: np.array, y_data: np.array):
    if x_data.size == y_data.size:
        text_array = []
        for i, elem in enumerate(x_data):
            text_array.append(f"{x_data[i]} {y_data[i]}")
        return text_array
    else:
        return None


# function to generate name for file with data from spectrometer
def generate_spectrum_file_name(prefix: str = ""):
    name = prefix + str(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')) + ".txt"
    return name


# function to crate full data about spectrum (session info + separator + spectrum data)
def create_full_spectrum_data(session_info, x_data, y_data):
    data_array = generate_spectrum_data_array(x_data, y_data)
    return session_info + [SPECTRUM_DATA_SEPARATOR] + data_array if data_array is not None else None


# function to save file with data to selected folder (if folder exist)
def save_data_to_folder(data, file_name: str, folder):
    if os.path.isdir(folder):
        path_to_file = os.path.join(folder, file_name)

        # get name of user in whose directory the program is located
        script_dir = os.path.dirname(os.path.realpath(__file__))
        dir_stat = os.stat(script_dir)
        user_info = pwd.getpwuid(dir_stat.st_uid)
        user_name = user_info.pw_name

        try:
            # get info about user
            user_info = pwd.getpwnam(user_name)
            uid, gid = user_info.pw_uid, user_info.pw_gid
            # create file
            with open(path_to_file, "w") as file:
                pass
            # switch file owner fore user
            os.chown(path_to_file, uid, gid)

            # save data
            with open(path_to_file, "w") as file:
                file.writelines(f"{i}\n" for i in data)
        except KeyError:
            print(f"⚠ Error: The user could not be found {user_name}")
    else:
        raise Exception(f"{folder} is not a directory")


# function to get spectrum array (X,Y) from file
def read_spectrum_from_file(file_path):
    x_data = []
    y_data = []
    start_reading = False

    with open(file_path, 'r') as f:
        for line in f:
            if not start_reading:
                if SPECTRUM_DATA_SEPARATOR in line.strip():
                    start_reading = True
            else:
                parts = line.strip().split()
                if len(parts) >= 2:
                    try:
                        x, y = float(parts[0]), float(parts[1])
                        x_data.append(x)
                        y_data.append(y)
                    except ValueError:
                        continue

    # check that we get data
    if len(x_data) == 0:
        x_data = None
    if len(y_data) == 0:
        y_data = None
    return x_data, y_data
