import os
import time
import logging
from PyQt5.QtGui import QPixmap

logger = logging.getLogger(__name__)

def save_photo(image, directory: str):
    """
    Сохраняет изображение в файл в указанную директорию.

    Args:
        image (QImage): Изображение для сохранения.
        directory (str): Директория для сохранения. Обязательный параметр.

    Returns:
        str: Полный путь к сохраненному файлу

    Raises:
        ValueError: Если изображение пустое или директория не задана/не существует
        RuntimeError: Если не удалось сохранить файл
    """
    if image.isNull():
        raise ValueError("Cannot save null image")

    if not directory:
        raise ValueError("Save directory is not specified")

    if not os.path.isdir(directory):
        raise ValueError(f"Save directory does not exist: {directory}")

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"camera_snapshot_{timestamp}.png"
    full_path = os.path.join(directory, filename)

    # Сохраняем изображение
    pixmap = QPixmap.fromImage(image)
    if pixmap.isNull():
        raise ValueError("Failed to convert QImage to QPixmap")
    
    save_success = pixmap.save(full_path)
    if not save_success:
        raise RuntimeError(f"Failed to save image to {full_path}")
    
    logger.info(f"Photo saved successfully to: {full_path}")
    return full_path