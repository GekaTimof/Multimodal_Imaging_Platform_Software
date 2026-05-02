import os
import pwd

def get_home_directory():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    dir_stat = os.stat(script_dir)
    user_info = pwd.getpwuid(dir_stat.st_uid)
    return user_info.pw_dir
