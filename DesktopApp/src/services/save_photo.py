import os
from PyQt5.QtGui import QPixmap
from config import path_manager

def save_photo(image, custom_directory=None):
    """
    Сохраняет изображение в файл на основе настроек из path_manager или пользовательской директории.

    Args:
        image (QImage): Изображение для сохранения.
        custom_directory (str, optional): Пользовательская директория для сохранения.
        
    Returns:
        str: Полный путь к сохраненному файлу
    """
    if custom_directory:
        # Используем пользовательскую директорию
        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"camera_snapshot_{timestamp}.png"
        full_path = os.path.join(custom_directory, filename)
    else:
        # Получаем путь сохранения из path_manager
        full_path = path_manager.get_full_path('photo')
    
    # Создаем директорию, если не существует
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    # Сохраняем изображение
    pixmap = QPixmap.fromImage(image)
    pixmap.save(full_path)
    
    return full_path