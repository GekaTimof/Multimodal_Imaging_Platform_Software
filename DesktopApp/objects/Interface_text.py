"""
Interface Text Manager
Handles multilingual text support for the desktop application.

This class loads language-specific text from JSON files and provides
methods to access translated strings for UI elements.
"""

import sys
import os
import json

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from DesktopApp.language_variations.language_link import Languages
from DesktopApp.objects.errors import Wrong_argument_exception


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
            raise Wrong_argument_exception
        
        link = Languages[name]
        self.file = link
        try:
            with open(link, 'r') as f:
                self.text_json = json.load(f)
        except FileNotFoundError:
            raise Wrong_argument_exception(f"Language file not found: {link}")
        except json.JSONDecodeError:
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
    
