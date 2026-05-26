# DesktopApp / Десктопное Приложение

**[English](#english) | [Русский](#русский)**

---

<a name="english"></a>
## English

PyQt5 GUI application for controlling scientific instruments (spectrometer, camera, positioner) connected to Raspberry Pi 5.

### Overview

Three-tab interface with multilingual support (English/Russian) and slot-based settings storage (10 slots per device).

### Project Structure

```
DesktopApp/
├── main.py                         # Entry point
├── requirements.txt                # Dependencies
├── src/
│   ├── config/                     # Configuration
│   │   ├── api_config.py          # API settings
│   │   ├── interface_config.py    # UI settings (theme, language)
│   │   ├── path_manager.py        # Path configuration
│   │   └── theme_manager.py       # Dark/light theme
│   ├── core/
│   │   ├── constants/             # Constants (camera, spectrometer, UI)
│   │   └── threads/               # Worker threads (camera, photo capture)
│   ├── models/
│   │   ├── errors.py              # Error definitions
│   │   └── interface_text.py      # UI text and translations
│   ├── services/
│   │   ├── directory_control.py   # Directory management
│   │   ├── light_switcher_service.py  # Light control API
│   │   ├── raspberry_mode.py      # Raspberry Pi mode switching
│   │   ├── save_photo.py          # Photo saving utility
│   │   └── spectrometer_service.py    # Spectrometer API client
│   ├── ui/
│   │   ├── main_window.py         # Main application window
│   │   ├── tabs/                  # Three tabs: camera, spectrometer, acquisition
│   │   └── widgets/               # UI widgets (video, spectrometer, settings)
│   └── utils/
│       └── error_handler.py       # Error handling utilities
├── resources/
│   ├── interface_settings.json    # UI settings
│   ├── paths_config.json          # Path configuration
│   ├── settings.json              # App settings (API URL, theme, language)
│   └── language_variations/       # Translation files (EN/RU)
└── tests/                         # Unit and integration tests
```

### Installation

```bash
cd DesktopApp
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### Running

```bash
python main.py
```

### Configuration

Edit `resources/settings.json`:
- `api.base_url` — Raspberry Pi IP (default: `http://10.78.112.189:8000/api`)
- `ui.theme` — Theme setting
- `ui.language` — Language (English/Russian)

### Features

| Tab | Features |
|-----|----------|
| **Camera** | Live video streaming, photo capture, slot-based settings |
| **Spectrometer** | Real-time spectrum, integration time, dark calibration |
| **Acquisition** | Acquisition data visualization |

---

<a name="русский"></a>
## Русский

PyQt5 GUI-приложение для управления научными приборами (спектрометр, камера, позиционер), подключенными к Raspberry Pi 5.

### Обзор

Трёхтабличный интерфейс с поддержкой двух языков (английский/русский) и хранением настроек в слотах (10 слотов на устройство).

### Структура проекта

```
DesktopApp/
├── main.py                         # Точка входа
├── requirements.txt                # Зависимости
├── src/
│   ├── config/                     # Конфигурация
│   │   ├── api_config.py          # Настройки API
│   │   ├── interface_config.py    # Настройки UI (тема, язык)
│   │   ├── path_manager.py        # Конфигурация путей
│   │   └── theme_manager.py       # Тёмная/светлая тема
│   ├── core/
│   │   ├── constants/             # Константы (камера, спектрометр, UI)
│   │   └── threads/               # Рабочие потоки (камера, захват фото)
│   ├── models/
│   │   ├── errors.py              # Определения ошибок
│   │   └── interface_text.py      # Текст UI и переводы
│   ├── services/
│   │   ├── directory_control.py   # Управление директориями
│   │   ├── light_switcher_service.py  # API управления подсветкой
│   │   ├── raspberry_mode.py      # Переключение режимов Raspberry Pi
│   │   ├── save_photo.py          # Утилита сохранения фото
│   │   └── spectrometer_service.py    # API клиент спектрометра
│   ├── ui/
│   │   ├── main_window.py         # Главное окно приложения
│   │   ├── tabs/                  # Три вкладки: камера, спектрометр, приобретение
│   │   └── widgets/               # UI виджеты (видео, спектрометр, настройки)
│   └── utils/
│       └── error_handler.py       # Утилиты обработки ошибок
├── resources/
│   ├── interface_settings.json    # Настройки UI
│   ├── paths_config.json          # Конфигурация путей
│   ├── settings.json              # Настройки приложения (API URL, тема, язык)
│   └── language_variations/       # Файлы переводов (EN/RU)
└── tests/                         # Модульные и интеграционные тесты
```

### Установка

```bash
cd DesktopApp
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### Запуск

```bash
python main.py
```

### Конфигурация

Отредактируйте `resources/settings.json`:
- `api.base_url` — IP Raspberry Pi (по умолчанию: `http://10.78.112.189:8000/api`)
- `ui.theme` — Настройка темы
- `ui.language` — Язык (English/Russian)

### Функциональность

| Вкладка | Возможности |
|---------|-------------|
| **Камера** | Потоковое видео, захват фото, настройки в слотах |
| **Спектрометр** | Спектр в реальном времени, время интеграции, тёмная калибровка |
| **Приобретение** | Визуализация данных приобретения |
