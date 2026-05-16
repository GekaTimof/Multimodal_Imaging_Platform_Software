"""
Language File Paths Configuration
Maps language names to their respective JSON text files.

This dictionary provides the file paths for different language translations
used by the Interface_text class to load appropriate UI text.
"""

import os

# Mapping of language names to their JSON translation files
# Paths are relative to the 'resources/' directory inside DesktopApp/
Languages: dict = {
    "Russian": os.path.join("language_variations", "text_variations", "russian_text.json"),
    "English": os.path.join("language_variations", "text_variations", "english_text.json"),
}