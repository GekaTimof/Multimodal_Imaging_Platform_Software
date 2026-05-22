import os
import time
import logging
from PyQt5.QtGui import QPixmap
from config import path_manager

logger = logging.getLogger(__name__)

def save_photo(image, custom_directory=None):
    """
    Сохраняет изображение в файл на основе настроек из path_manager или пользовательской директории.

    Args:
        image (QImage): Изображение для сохранения.
        custom_directory (str, optional): Пользовательская директория для сохранения.
        
    Returns:
        str: Полный путь к сохраненному файлу
        
    Raises:
        ValueError: Если изображение пустое или невалидное
        RuntimeError: Если не удалось сохранить файл
    """
    # Проверяем что изображение валидно
    if image.isNull():
        raise ValueError("Cannot save null image")
    
    if custom_directory:
        # Используем пользовательскую директорию
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"camera_snapshot_{timestamp}.png"
        full_path = os.path.join(custom_directory, filename)
        save_dir = custom_directory
    else:
        # Получаем путь сохранения из path_manager
        full_path = path_manager.get_full_path('photo')
        save_dir = os.path.dirname(full_path)
    
    # Создаем директорию, если не существует
    try:
        os.makedirs(save_dir, exist_ok=True)
    except OSError as e:
        raise RuntimeError(f"Failed to create directory {save_dir}: {e}")

    # Сохраняем изображение
    pixmap = QPixmap.fromImage(image)
    if pixmap.isNull():
        raise ValueError("Failed to convert QImage to QPixmap")
    
    save_success = pixmap.save(full_path)
    if not save_success:
        raise RuntimeError(f"Failed to save image to {full_path}")
    
    logger.info(f"Photo saved successfully to: {full_path}")
    return full_path