import os
from PyQt5.QtGui import QPixmap
from DesktopApp.config import path_manager

def save_photo(image):
    """
    Сохраняет изображение в файл на основе настроек из path_manager.

    Args:
        image (QImage): Изображение для сохранения.
        
    Returns:
        str: Полный путь к сохраненному файлу
    """
    # Получаем путь сохранения из path_manager
    full_path = path_manager.get_full_path('photo')
    
    # Создаем директорию, если не существует
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    # Сохраняем изображение
    pixmap = QPixmap.fromImage(image)
    pixmap.save(full_path)
    
    return full_path