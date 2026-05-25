"""
Interface Text Manager
Handles multilingual text support for the desktop application.

This class loads language-specific text from JSON files and provides
methods to access translated strings for UI elements.
"""

import sys
import os
import json

# Add DesktopApp root (parent of 'src/') to path so that 'resources' package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from resources.language_variations.language_link import Languages
from .errors import Wrong_argument_exception


class Interface_text():
    """
    Manages interface text for different languages.
    
    Loads language-specific JSON files and provides access to translated strings.
    Each method returns a specific text element for UI components.
    """
    
    def __init__(self, name: str):
        """
        Initialize text manager for specified language.
        
        Args:
            name (str): Language name ('English' or 'Russian')
            
        Raises:
            Wrong_argument_exception: If language not supported or file not found
        """
        if name not in Languages.keys():
            print(f"Language '{name}' not found in available languages: {list(Languages.keys())}")
            # Fallback to first available language
            name = list(Languages.keys())[0]
            print(f"Falling back to language: {name}")
        
        # Get absolute path to language file relative to this script
        # Go up from src/models/objects/ to DesktopApp/ then to resources/
        desktop_app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        link = os.path.join(desktop_app_root, 'resources', Languages[name])
        self.file = link
        try:
            with open(link, 'r', encoding='utf-8') as f:
                self.text_json = json.load(f)
        except FileNotFoundError:
            print(f"Language file not found: {link}")
            raise Wrong_argument_exception(f"Language file not found: {link}")
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in language file: {link} - {e}")
            raise Wrong_argument_exception(f"Invalid JSON in language file: {link}")
        
    def abbreviation(self):
        """Return language abbreviation (e.g., 'EN', 'RU')."""
        return self.text_json["Abbreviation"]
    
    def name(self):
        """Return full language name."""
        return self.text_json["Name"]
    
    def language(self):
        return self.text_json["Language"]
    
    def wells(self):
        return self.text_json["Wells"]
    
    def camera(self):   
        """Return camera-related text."""
        return self.text_json["Camera"]
    
    def positioner(self):
        """Return positioner-related text."""
        return self.text_json["Positioner"]
    
    def spectrometer(self):
        return self.text_json["Spectrometer"]
    
    def spectrum(self):
        return self.text_json["Spectrum"]
    
    def switch_to_light_theme(self):
        return self.text_json["Switch_to_Light_Theme"]
    
    def switch_to_dark_theme(self):
        return self.text_json["Switch_to_Dark_Theme"]
    
    def reset_zoom(self):
        return self.text_json["Reset_zoom"]
    
    def integral_time(self):
        return self.text_json["Integral_time"]
    
    def set_dark_spectrum(self):
        return self.text_json["Set_Dark_Spectrum"]
    
    def clear_dark_spectrum(self):
        return self.text_json["Clear_Dark_Spectrum"]
    
    def save_directory(self):
        return self.text_json["Save_Directory"]
    
    def no_folder_selected(self):
        return self.text_json["No_folder_selected"]
    
    def select(self):
        return self.text_json["Select"]
    
    def save_spectrum(self):
        return self.text_json["Save_Spectrum"]
    
    def select_spectrum_file(self):
        return self.text_json["Select_spectrum_file"]
    
    def remove_selected_spectrum(self):
        return self.text_json["Remove_Selected_Spectrum"]
    
    def remove_all_spectra(self):
        return self.text_json["Remove_All_Spectra"]
    
    def start_camera(self):
        """Return 'Start Camera' button text."""
        # Returns the text for the 'Start Camera' button
        return self.text_json["Start_Camera"]   
    
    def stop_camera(self):      
        """Return 'Stop Camera' button text."""
        # Returns the text for the 'Stop Camera' button
        return self.text_json["Stop_Camera"]
    
    def select_save_directory(self):
        # Returns the text for the 'Select Save Directory' button
        return self.text_json["Select_save_directory"]
    
    def save_image(self):
        return self.text_json["Save_Image"]
    
    def no_video(self):
        return self.text_json["No_video"]
    
    def warning_title(self):
        return self.text_json["Warning_Title"]
    
    def warning_select_out_of_home(self):
        return self.text_json["Warning_Select_Out_Of_Home"]
    
    def warning_saving_out_of_home(self):
        return self.text_json["Warning_Saving_Out_Of_Home"]
    
    def photo_resolution(self):
        return self.text_json["Photo_Resolution"]
    
    def video_resolution(self):
        return self.text_json["Video_Resolution"]
    
    def auto_exposure(self):
        return self.text_json["Auto_Exposure"]
    
    def auto_white_balance(self):
        return self.text_json["Auto_White_Balance"]
    
    def exposure_time(self):
        return self.text_json["Exposure_Time"]
    
    def analogue_gain(self):
        return self.text_json["Analogue_Gain"]
    
    def exposure_value(self):
        return self.text_json["Exposure_Value"]
    
    def red_gain(self):
        return self.text_json["Red_Gain"]
    
    def blue_gain(self):
        return self.text_json["Blue_Gain"]
    
    def settings_name(self):
        return self.text_json["Settings_Name"]
    
    def camera_settings(self):
        return self.text_json["Camera_Settings"]
    
    def load(self):
        return self.text_json["Load"]
    
    def save(self):
        return self.text_json["Save"]
    
    def apply(self):
        return self.text_json["Apply"]
    
    def refresh(self):
        return self.text_json["Refresh"]
    
    def photo_save_directory(self):
        return self.text_json["Photo_Save_Directory"]
    
    def spectrum_save_directory(self):
        return self.text_json["Spectrum_Save_Directory"]
    
    def file_settings(self):
        return self.text_json["File_Settings"]
    
    # Positioner settings methods
    def position_settings(self):
        return self.text_json["Position_Settings"]
    
    def x_position(self):
        return self.text_json["X_Position"]
    
    def y_position(self):
        return self.text_json["Y_Position"]
    
    def z_position(self):
        return self.text_json["Z_Position"]
    
    def movement_settings(self):
        return self.text_json["Movement_Settings"]
    
    def speed(self):
        return self.text_json["Speed"]
    
    def acceleration(self):
        return self.text_json["Acceleration"]
    
    def position_presets(self):
        return self.text_json["Position_Presets"]
    
    def presets(self):
        return self.text_json["Presets"]
    
    def go_home(self):
        return self.text_json["Go_Home"]
    
    def move_to(self):
        return self.text_json["Move_To"]
    
    def save_preset(self):
        return self.text_json["Save_Preset"]
    
    def ready(self):
        return self.text_json["Ready"]
    
    def overillumination_warning(self):
        return self.text_json["Overillumination_Warning"]
    
    def loaded_spectra(self):
        return self.text_json["Loaded_Spectra"]
    
    def status_disconnected(self):
        return self.text_json["Status_Disconnected"]
    
    def loading_positioner_settings(self):
        return self.text_json["Loading_Positioner_Settings"]
    
    def positioner_settings_loaded(self):
        return self.text_json["Positioner_Settings_Loaded"]
    
    def applying_positioner_settings(self):
        return self.text_json["Applying_Positioner_Settings"]
    
    def positioner_settings_applied(self):
        return self.text_json["Positioner_Settings_Applied"]
    
    def moving_to_home(self):
        return self.text_json["Moving_To_Home"]
    
    def positioner_moved_home(self):
        return self.text_json["Positioner_Moved_Home"]
    
    def moving_to_position(self):
        return self.text_json["Moving_To_Position"]
    
    def moved_to_position(self):
        return self.text_json["Moved_To_Position"]
    
    def position_saved(self):
        return self.text_json["Position_Saved"]
    
    def light_switcher_connected(self):
        return self.text_json["Light_Switcher_Connected"]
    
    def light_switcher_disconnected(self):
        return self.text_json["Light_Switcher_Disconnected"]
    
    def light_switcher_checking(self):
        return self.text_json["Light_Switcher_Checking"]
    
    def light_switcher_switching(self):
        return self.text_json["Light_Switcher_Switching"]
    
    def light_switcher_switching_camera(self):
        """Текст для переключения в режим камеры"""
        if self.language == "Russian":
            return "Пожалуйста, подождите пока переключается камера..."
        else:
            return "Please wait while switching camera position..."
    
    def light_switcher_switching_spectrometer(self):
        """Текст для переключения в режим спектрометра"""
        if self.language == "Russian":
            return "Пожалуйста, подождите пока переключается спектрометр..."
        else:
            return "Please wait while switching spectrometer position..."
    
    def light_switcher_switch_error(self):
        return self.text_json["Light_Switcher_Switch_Error"]
    
    def light_switcher_error(self):
        return self.text_json["Light_Switcher_Error"]
    
    def light_switcher_reconnect(self):
        return self.text_json["Light_Switcher_Reconnect"]
    
    def light_switcher_reset(self):
        return self.text_json["Light_Switcher_Reset"]
    
