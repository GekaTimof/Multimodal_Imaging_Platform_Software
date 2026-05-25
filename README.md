# Multimodal Imaging Platform Software / Мультимодальная Платформа Управления

**[English](#english) | [Русский](#русский)**

---

<a name="english"></a>
## English

A comprehensive platform for controlling scientific instruments (spectrometer, camera, acquisition analysis) through a desktop application connected to Raspberry Pi hardware.

### Overview

This software platform provides an intuitive graphical interface for managing scientific instruments with multilingual support (English/Russian). It consists of two main components:

- **DesktopApp** — PyQt5 GUI application running on user's computer
- **RaspberryPi** — Hardware control server running on Raspberry Pi 5

### Architecture

The platform follows a client-server architecture:
- DesktopApp communicates with RaspberryPi via REST API
- Single database located on Raspberry Pi (DevicesSettings.db)
- Real-time video streaming and spectrometer data acquisition

See `ARCHITECTURE.md` for detailed architecture documentation.

### Project Structure

```
Multimodal_Imaging_Platform_Software/
├── README.md                    # This file (EN/RU)
├── ARCHITECTURE.md             # Architecture documentation
├── .gitignore                  # Git ignore patterns
├── requirements-base.txt       # Base dependencies
├── DesktopApp/                 # Desktop GUI application
│   ├── main.py                 # Application entry point
│   ├── README.md               # Desktop app documentation (EN/RU)
│   ├── requirements.txt        # DesktopApp dependencies
│   ├── src/
│   │   ├── config/            # Configuration modules
│   │   ├── core/              # Core application logic
│   │   ├── models/            # Data models
│   │   └── ui/                # UI components and widgets
│   └── tests/                 # DesktopApp tests
├── RaspberryPi/                # Raspberry Pi server code
│   ├── main.py                 # Server entry point
│   ├── README.md               # Pi server documentation (EN/RU)
│   ├── requirements.txt        # RaspberryPi dependencies
│   ├── raspberrypi-settings.service  # Systemd service file
│   ├── src/
│   │   ├── config/            # Server configuration
│   │   ├── core/              # Core server logic
│   │   │   ├── streaming.py   # MJPEG video streaming
│   │   │   └── spectrum_streaming.py  # Spectrometer streaming
│   │   └── services/          # Device control services
│   ├── Spectrometer/          # Spectrometer utilities
│   └── Light_switcher/        # Arduino light control
├── docs/                       # Documentation
│   ├── Diploma/               # Diploma thesis materials
│   └── reports/               # Development reports
└── tests/                     # Test suite
    ├── unit/                   # Unit tests
    ├── integration/            # Integration tests
    └── fixtures/               # Test data and mocks
```

### Quick Start

1. **Create virtual environment:**
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

2. **Install dependencies:**
```bash
pip install -r requirements-base.txt
```

3. **Configure Raspberry Pi:**
   - Install Raspberry Pi OS on Raspberry Pi 5
   - Enable Camera and GPIO interfaces
   - Install dependencies: `pip install -r RaspberryPi/requirements.txt`
   - Run server: `cd RaspberryPi && python main.py`

4. **Run Desktop Application:**
```bash
cd DesktopApp
pip install -r requirements.txt
python main.py
```

5. **Verify connection:**
   - Check API: `http://<raspberry-pi-ip>:8000/api/health`
   - Check video stream: `http://<raspberry-pi-ip>:8080/video`

### Features

| Feature | Description |
|---------|-------------|
| **Camera Control** | IP camera video streaming, image capture, parameter configuration |
| **Spectrometer** | Spectral data acquisition, integration time control, dark spectrum calibration |
| **Acquisition Analysis** | Acquisition data visualization and analysis |
| **Multilingual UI** | English and Russian interface support |
| **Settings Management** | Slot-based settings storage (10 slots per device) |
| **Real-time Streaming** | MJPEG video and spectrum data streaming |

### API Endpoints

Base URL: `http://<raspberry-pi-ip>:8000/api`

- `GET /api/health` — Health check
- `GET /api/settings/{table}` — Get settings from table
- `POST /api/settings/update` — Update single parameter
- `GET /api/settings/camera/slot/{slot_id}` — Get camera settings slot (0-9)
- `POST /api/settings/camera/save-slot/{slot_id}` — Save settings to slot
- `GET /api/settings/camera/validation-rules` — Get validation rules

### Testing

```bash
# Unit tests
python -m pytest tests/unit/

# Integration tests
python -m pytest tests/integration/

# All tests
python -m pytest tests/
```

### Documentation

- `ARCHITECTURE.md` — Detailed architecture documentation
- `DesktopApp/README.md` — Desktop application documentation
- `RaspberryPi/README.md` — Raspberry Pi server documentation
- `docs/reports/` — Development reports

---

<a name="русский"></a>
## Русский

Комплексная платформа для управления научными приборами (спектрометр, камера, анализ лунок) через десктопное приложение, подключенное к оборудованию Raspberry Pi.

### Обзор

Эта программная платформа предоставляет интуитивный графический интерфейс для управления научными приборами с поддержкой нескольких языков (Английский/Русский). Состоит из двух основных компонентов:

- **DesktopApp** — GUI приложение на PyQt5, работающее на компьютере пользователя
- **RaspberryPi** — Сервер управления оборудованием на Raspberry Pi 5

### Архитектура

Платформа использует клиент-серверную архитектуру:
- DesktopApp взаимодействует с RaspberryPi через REST API
- Единая база данных на Raspberry Pi (DevicesSettings.db)
- Потоковая передача видео и данных спектрометра в реальном времени

Подробная документация архитектуры в файле `ARCHITECTURE.md`.

### Структура проекта

```
Multimodal_Imaging_Platform_Software/
├── README.md                    # Этот файл (EN/RU)
├── ARCHITECTURE.md             # Документация архитектуры
├── .gitignore                  # Шаблоны Git ignore
├── requirements-base.txt       # Базовые зависимости
├── DesktopApp/                 # Десктопное GUI приложение
│   ├── main.py                 # Точка входа
│   ├── README.md               # Документация (EN/RU)
│   ├── requirements.txt        # Зависимости DesktopApp
│   ├── src/
│   │   ├── config/            # Модули конфигурации
│   │   ├── core/              # Основная логика приложения
│   │   ├── models/            # Модели данных
│   │   └── ui/                # UI компоненты и виджеты
│   └── tests/                 # Тесты DesktopApp
├── RaspberryPi/                # Код сервера Raspberry Pi
│   ├── main.py                 # Точка входа сервера
│   ├── README.md               # Документация сервера (EN/RU)
│   ├── requirements.txt        # Зависимости RaspberryPi
│   ├── raspberrypi-settings.service  # Файл systemd сервиса
│   ├── src/
│   │   ├── config/            # Конфигурация сервера
│   │   ├── core/              # Основная логика сервера
│   │   │   ├── streaming.py   # MJPEG видеостриминг
│   │   │   └── spectrum_streaming.py  # Стриминг спектрометра
│   │   └── services/          # Сервисы управления устройствами
│   ├── Spectrometer/          # Утилиты спектрометра
│   └── Light_switcher/        # Управление подсветкой Arduino
├── docs/                       # Документация
│   ├── Diploma/               # Материалы диплома
│   └── reports/               # Отчеты разработки
└── tests/                     # Тестовый набор
    ├── unit/                   # Модульные тесты
    ├── integration/            # Интеграционные тесты
    └── fixtures/               # Тестовые данные и моки
```

### Быстрый старт

1. **Создать виртуальное окружение:**
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

2. **Установить зависимости:**
```bash
pip install -r requirements-base.txt
```

3. **Настроить Raspberry Pi:**
   - Установить Raspberry Pi OS на Raspberry Pi 5
   - Включить интерфейсы Camera и GPIO
   - Установить зависимости: `pip install -r RaspberryPi/requirements.txt`
   - Запустить сервер: `cd RaspberryPi && python main.py`

4. **Запустить Desktop Application:**
```bash
cd DesktopApp
pip install -r requirements.txt
python main.py
```

5. **Проверить подключение:**
   - Проверить API: `http://<ip-raspberry-pi>:8000/api/health`
   - Проверить видеопоток: `http://<ip-raspberry-pi>:8080/video`

### Возможности

| Возможность | Описание |
|-------------|----------|
| **Управление камерой** | Потоковое видео с IP-камеры, захват изображений, настройка параметров |
| **Спектрометр** | Сбор спектральных данных, управление временем интеграции, калибровка темнового спектра |
| **Анализ приобретения** | Визуализация и анализ данных приобретения |
| **Мультиязычный UI** | Поддержка английского и русского интерфейса |
| **Управление настройками** | Хранение настроек в слотах (10 слотов на устройство) |
| **Потоковая передача** | MJPEG видео и данные спектрометра в реальном времени |

### API Endpoints

Базовый URL: `http://<ip-raspberry-pi>:8000/api`

- `GET /api/health` — Проверка работоспособности
- `GET /api/settings/{table}` — Получить настройки из таблицы
- `POST /api/settings/update` — Обновить параметр
- `GET /api/settings/camera/slot/{slot_id}` — Получить слот настроек камеры (0-9)
- `POST /api/settings/camera/save-slot/{slot_id}` — Сохранить настройки в слот
- `GET /api/settings/camera/validation-rules` — Получить правила валидации

### Тестирование

```bash
# Модульные тесты
python -m pytest tests/unit/

# Интеграционные тесты
python -m pytest tests/integration/

# Все тесты
python -m pytest tests/
```

### Документация

- `ARCHITECTURE.md` — Подробная документация архитектуры
- `DesktopApp/README.md` — Документация десктопного приложения
- `RaspberryPi/README.md` — Документация сервера Raspberry Pi
- `docs/reports/` — Отчеты разработки

---

## License / Лицензия

This project is part of a diploma thesis / Этот проект является частью дипломной работы.
