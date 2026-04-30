import json
import os
from datetime import datetime
from PyQt5.QtGui import QPixmap

def save_photo(image):
    """
    Сохраняет изображение в файл на основе настроек из settings.json.

    Args:
        image (QImage): Изображение для сохранения.
    """
    # Читаем настройки
    settings_path = os.path.join(os.path.dirname(__file__), '..', 'settings.json')
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings = json.load(f)

    # Получаем настройки для фото
    photo_settings = settings.get('photo', {})
    save_directory = photo_settings.get('save_directory', '')
    filename_template = photo_settings.get('filename_template', 'camera_snapshot_{timestamp}.png')
    image_format = photo_settings.get('format', 'PNG')

    # Проверяем, что директория выбрана
    if not save_directory:
        raise ValueError("Save directory not set in settings.json")

    # Создаем директорию, если не существует
    os.makedirs(save_directory, exist_ok=True)

    # Формируем имя файла с timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = filename_template.format(timestamp=timestamp)
    full_path = os.path.join(save_directory, filename)

    # Сохраняем изображение
    pixmap = QPixmap.fromImage(image)
    if not pixmap.save(full_path, image_format):
        raise IOError(f"Failed to save image to {full_path}")

    return full_path