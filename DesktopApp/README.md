# DesktopApp / Десктопное Приложение

**[English](#english) | [Русский](#русский)**

---

<a name="english"></a>
## English

Desktop GUI application for controlling scientific instruments (spectrometer, camera, acquisition analysis) connected to Raspberry Pi hardware.

### Overview

PyQt5 application with a three-tab interface for managing scientific instruments. Supports multilingual interface (English/Russian) and configurable device parameters with slot-based settings storage.

### Architecture

- **Pattern**: MVVM (Model-View-ViewModel) with clear separation of concerns
- **Communication**: REST API client for Raspberry Pi communication
- **Internationalization**: JSON-based translation system
- **Settings**: Slot-based storage (10 slots per device type)

### Project Structure

```
DesktopApp/
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── README.md                   # This documentation (EN/RU)
│
├── src/
│   ├── config/                # Configuration modules
│   │   └── constants/         # Application constants
│   │       └── spectrometer_constants.py
│   │
│   ├── core/                  # Core application logic
│   │   ├── device_registry.py # Device registration and management
│   │   ├── mode_controller.py # Raspberry Pi mode switching
│   │   └── settings_controller.py # Settings management
│   │
│   ├── models/                # Data models
│   │   ├── base_device_model.py
│   │   ├── camera_model.py
│   │   ├── spectrometer_model.py
│   │   └── Acquisition_model.py
│   │
│   └── ui/                    # User interface
│       ├── threads/           # Background threads
│       │   ├── camera_thread.py      # Camera streaming thread
│       │   └── main_window_thread.py # Main window controller
│       │
│       ├── tabs/              # Main interface tabs
│       │   ├── camera_tab.py         # Camera control tab
│       │   ├── spectrometer_tab.py   # Spectrometer tab
│       │   └── Acquisition_tab.py    # Acquisition analysis tab
│       │
│       ├── widgets/           # Reusable UI components
│       │   ├── device_settings_widget/  # Settings widgets
│       │   ├── spectrometer_widget.py     # Spectrometer display
│       │   └── video_widget.py            # Video display
│       │
│       └── windows/           # Dialog windows
│           └── device_settings_window.py  # Settings dialog
│
├── resources/                 # Application resources
│   ├── language_variations/   # Translation files
│   │   ├── language_link.py   # Language mapping
│   │   └── text_variations/   # JSON translations (EN/RU)
│   └── settings.json          # Application settings
│
└── tests/                     # Unit and integration tests
    ├── unit/
    └── integration/
```

### Features

#### Camera Tab
- Real-time IP camera video streaming from Raspberry Pi
- Start/stop recording controls
- Save directory selection
- Single frame capture
- Camera parameter configuration (slots 0-9)

#### Spectrometer Tab
- Real-time spectral data acquisition
- Integration time adjustment
- Dark spectrum calibration (set/clear)
- Spectrum data export to files
- Spectral visualization with matplotlib

#### Acquisition Tab
- Acquisition data visualization
- Analysis parameter settings
- Data export functionality

#### Settings Management
- 10 configurable slots per device type
- Validation rules enforcement
- Save/load settings to/from Raspberry Pi
- Automatic mode switching on Raspberry Pi

### Prerequisites

- Python 3.8+
- PyQt5
- pyqtgraph
- requests

### Installation

```bash
cd DesktopApp
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

On Linux distributions with an externally managed Python environment, do not install the dependencies with system `pip`. Use the virtual environment above. If you already have PyQt5 installed in the user/system environment and installation fails on Python 3.12 because of PyQt5 build dependencies, create the environment with access to system site packages and install the missing dependencies there:

```bash
cd DesktopApp
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install pyqtgraph==0.13.3
```

### Running the Application

```bash
.venv/bin/python main.py
```

If you run the application from the repository root with the root virtual environment, use:

```bash
/home/evgeniy/Projects/Multimodal_Imaging_Platform_Software/.venv/bin/python /home/evgeniy/Projects/Multimodal_Imaging_Platform_Software/DesktopApp/main.py
```

If the application starts but prints `Connection refused` for `10.78.112.189:8000` or `10.78.112.189:8080`, the desktop app is running but the Raspberry Pi backend/video server is not reachable.

### Configuration

Edit `resources/settings.json` to configure:
- Raspberry Pi IP address (default: `10.43.70.189`)
- Default save directories
- Language preference
- Stream URLs

### API Communication

The application communicates with Raspberry Pi via REST API:

```
Base URL: http://<raspberry-pi-ip>:8000/api
```

Key endpoints:
- `GET /api/health` — Server health check
- `GET /api/settings/{table}` — Get device settings
- `POST /api/settings/update` — Update parameter
- `GET /api/settings/camera/slot/{slot_id}` — Get camera slot settings
- `POST /api/settings/camera/save-slot/{slot_id}` — Save to slot

---

<a name="русский"></a>
## Русский

Десктопное GUI приложение для управления научными приборами (спектрометр, камера, анализ лунок), подключенными к оборудованию Raspberry Pi.

### Обзор

Приложение на PyQt5 с трёхтабличным интерфейсом для управления научными приборами. Поддерживает многоязычный интерфейс (Английский/Русский) и настраиваемые параметры устройств с хранением настроек в слотах.

### Архитектура

- **Паттерн**: MVVM (Model-View-ViewModel) с чётким разделением ответственности
- **Коммуникация**: REST API клиент для связи с Raspberry Pi
- **Интернационализация**: Система переводов на основе JSON
- **Настройки**: Хранение в слотах (10 слотов на тип устройства)

### Структура проекта

```
DesktopApp/
├── main.py                     # Точка входа приложения
├── requirements.txt            # Зависимости Python
├── README.md                   # Эта документация (EN/RU)
│
├── src/
│   ├── config/                # Модули конфигурации
│   │   └── constants/         # Константы приложения
│   │       └── spectrometer_constants.py
│   │
│   ├── core/                  # Основная логика приложения
│   │   ├── device_registry.py # Регистрация и управление устройствами
│   │   ├── mode_controller.py # Переключение режимов Raspberry Pi
│   │   └── settings_controller.py # Управление настройками
│   │
│   ├── models/                # Модели данных
│   │   ├── base_device_model.py
│   │   ├── camera_model.py
│   │   ├── spectrometer_model.py
│   │   └── Acquisition_model.py
│   │
│   └── ui/                    # Пользовательский интерфейс
│       ├── threads/           # Фоновые потоки
│       │   ├── camera_thread.py      # Поток видеостриминга
│       │   └── main_window_thread.py # Контроллер главного окна
│       │
│       ├── tabs/              # Основные вкладки интерфейса
│       │   ├── camera_tab.py         # Вкладка управления камерой
│       │   ├── spectrometer_tab.py   # Вкладка спектрометра
│       │   └── Acquisition_tab.py    # Вкладка анализа приобретения
│       │
│       ├── widgets/           # Переиспользуемые UI компоненты
│       │   ├── device_settings_widget/  # Виджеты настроек
│       │   ├── spectrometer_widget.py     # Отображение спектрометра
│       │   └── video_widget.py            # Отображение видео
│       │
│       └── windows/           # Диалоговые окна
│           └── device_settings_window.py  # Диалог настроек
│
├── resources/                 # Ресурсы приложения
│   ├── language_variations/   # Файлы переводов
│   │   ├── language_link.py   # Сопоставление языков
│   │   └── text_variations/   # JSON переводы (EN/RU)
│   └── settings.json          # Настройки приложения
│
└── tests/                     # Модульные и интеграционные тесты
    ├── unit/
    └── integration/
```

### Функциональность

#### Вкладка Камеры
- Потоковое видео с IP-камеры Raspberry Pi в реальном времени
- Кнопки управления записью (старт/стоп)
- Выбор директории сохранения
- Захват отдельного кадра
- Настройка параметров камеры (слоты 0-9)

#### Вкладка Спектрометра
- Сбор спектральных данных в реальном времени
- Регулировка времени интеграции
- Калибровка темнового спектра (установка/очистка)
- Экспорт данных спектра в файлы
- Визуализация спектра с matplotlib

#### Вкладка Приобретения
- Визуализация данных приобретения
- Настройка параметров анализа
- Экспорт данных

#### Управление Настройками
- 10 настраиваемых слотов на тип устройства
- Применение правил валидации
- Сохранение/загрузка настроек на Raspberry Pi
- Автоматическое переключение режимов на Raspberry Pi

### Требования

- Python 3.8+
- PyQt5
- pyqtgraph
- requests

### Установка

```bash
cd DesktopApp
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

В Linux-дистрибутивах с защищённым системным Python не устанавливайте зависимости через системный `pip`. Используйте виртуальное окружение выше. Если PyQt5 уже установлен в пользовательском/системном окружении, а установка на Python 3.12 падает из-за build-зависимостей PyQt5, создайте окружение с доступом к системным пакетам и установите недостающие зависимости туда:

```bash
cd DesktopApp
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install pyqtgraph==0.13.3
```

### Запуск Приложения

```bash
.venv/bin/python main.py
```

Если приложение запускается из корня репозитория через корневое виртуальное окружение, используйте:

```bash
/home/evgeniy/Projects/Multimodal_Imaging_Platform_Software/.venv/bin/python /home/evgeniy/Projects/Multimodal_Imaging_Platform_Software/DesktopApp/main.py
```

Если приложение запускается, но выводит `Connection refused` для `10.78.112.189:8000` или `10.78.112.189:8080`, значит DesktopApp уже стартовал, но backend/video server на Raspberry Pi недоступен.

### Конфигурация

Отредактируйте `resources/settings.json` для настройки:
- IP-адрес Raspberry Pi (по умолчанию: `10.43.70.189`)
- Директории сохранения по умолчанию
- Предпочитаемый язык
- URL потоков

### API Коммуникация

Приложение взаимодействует с Raspberry Pi через REST API:

```
Базовый URL: http://<ip-raspberry-pi>:8000/api
```

Основные endpoints:
- `GET /api/health` — Проверка работоспособности сервера
- `GET /api/settings/{table}` — Получить настройки устройства
- `POST /api/settings/update` — Обновить параметр
- `GET /api/settings/camera/slot/{slot_id}` — Получить настройки слота камеры
- `POST /api/settings/camera/save-slot/{slot_id}` — Сохранить в слот
