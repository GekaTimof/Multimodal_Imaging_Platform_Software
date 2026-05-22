# RaspberryPi Server / Сервер Raspberry Pi

**[English](#english) | [Русский](#русский)**

---

<a name="english"></a>
## English

Hardware control server running on Raspberry Pi 5. Manages camera, spectrometer, and light control devices. Receives commands via REST API over Ethernet and continuously streams data (video or spectrum) in response.

### Overview

The Raspberry Pi component acts as the hardware control layer, providing:
- REST API for device control (port 8000)
- MJPEG video streaming server (port 8080)
- Spectrometer data streaming (port 8081)
- SQLite database for settings storage (single source of truth)
- Hardware interface for camera (Picamera2), spectrometer, and light switcher

### Architecture

```
RaspberryPi/
├── main.py                    # Entry point - starts all services
├── requirements.txt           # Python dependencies
├── raspberrypi-settings.service  # Systemd service file
├── README.md                  # This documentation (EN/RU)
│
├── src/
│   ├── config/               # Configuration
│   │   └── raspberry_pi_config.py
│   │
│   ├── core/                 # Core streaming modules
│   │   ├── streaming.py           # MJPEG video streaming server
│   │   └── spectrum_streaming.py  # Spectrometer data streaming
│   │
│   └── services/             # Hardware control services
│       ├── fastapi_server.py      # FastAPI REST endpoints
│       ├── camera_service.py      # Picamera2 integration
│       ├── spectrometer_service.py # Spectrometer control
│       ├── light_switcher_service.py # Arduino light control
│       └── database_service.py     # SQLite database operations
│
├── Spectrometer/             # Spectrometer utilities
│   ├── Get_data/            # Data acquisition scripts
│   └── Visualization/       # Visualization tools
│
└── Light_switcher/          # Arduino light control
    ├── light_switcher_distance_switch/
    └── light_switcher_end_switch.ino/
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| FastAPI Server | 8000 | REST API for device control and settings |
| Video Stream | 8080 | MJPEG video stream from camera |
| Spectrum Stream | 8081 | Real-time spectrometer data stream |

### Hardware Requirements

- **Raspberry Pi 5** (with sufficient cooling)
- **Camera**: Raspberry Pi Camera Module (via Picamera2)
- **Spectrometer**: USB spectrometer device
- **Light Switcher**: Arduino-based light control module

### Installation

1. **Prepare Raspberry Pi:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Enable camera and GPIO interfaces
sudo raspi-config
# Interface Options → Camera → Enable
# Interface Options → GPIO → Enable
```

2. **Install dependencies:**
```bash
cd /home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi
pip3 install -r requirements.txt
```

3. **Initialize database (automatic on first run):**
```bash
python3 main.py
```

### Running the Server

#### Manual Start
```bash
cd /home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi
python3 main.py
```

#### Auto-start with Systemd

The service file `raspberrypi-settings.service` is provided.

**Install:**
```bash
sudo cp raspberrypi-settings.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable raspberrypi-settings.service
sudo systemctl start raspberrypi-settings.service
```

**Manage:**
```bash
sudo systemctl status raspberrypi-settings.service  # Check status
sudo systemctl start raspberrypi-settings.service   # Start
sudo systemctl stop raspberrypi-settings.service    # Stop
sudo systemctl restart raspberrypi-settings.service # Restart
sudo journalctl -u raspberrypi-settings.service -f    # View logs
```

### API Endpoints

Base URL: `http://<raspberry-pi-ip>:8000/api`

#### Health & Status
- `GET /api/health` — Server health check
- `GET /api/status` — Get current system status

#### Settings Management
- `GET /api/settings/{table}` — Get all settings from table
- `GET /api/settings/{table}/slot/{slot_id}` — Get specific slot (0-9)
- `POST /api/settings/update` — Update single parameter
- `POST /api/settings/{table}` — Update all settings
- `POST /api/settings/{table}/save-slot/{slot_id}` — Save to slot
- `GET /api/settings/{table}/validation-rules` — Get validation rules

#### Camera Control
- `GET /api/camera/stream` — Video stream status
- `POST /api/camera/mode/{mode}` — Set camera mode (camera/spectrometer/wells)

#### Spectrometer
- `GET /api/spectrometer/data` — Get current spectrum data
- `POST /api/spectrometer/integration-time` — Set integration time
- `POST /api/spectrometer/dark-spectrum` — Set/clear dark spectrum

### Streams

**Video Stream:**
```
http://<raspberry-pi-ip>:8080/video
```

**Status Check:**
```
http://<raspberry-pi-ip>:8080/status
```

**Spectrum Stream:**
```
http://<raspberry-pi-ip>:8081/stream
```

### Database

- **Location**: `/home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi/DevicesSettings.db`
- **Type**: SQLite3
- **Tables**:
  - `CameraSettings` — Camera parameters (10 slots)
  - `SpectrometerSettings` — Spectrometer parameters (10 slots)
  - `PositionerSettings` — Positioner parameters (10 slots)

The database is the **single source of truth** for all device settings. DesktopApp connects via API only.

### Troubleshooting

**Camera not detected:**
```bash
# Check camera connection
libcamera-hello --list-cameras

# Restart camera service
sudo systemctl restart raspberrypi-settings.service
```

**Database locked:**
```bash
# Check for stale locks
lsof DevicesSettings.db

# Restart the service
sudo systemctl restart raspberrypi-settings.service
```

**API not responding:**
```bash
# Check if port 8000 is in use
sudo lsof -i :8000

# Check service logs
sudo journalctl -u raspberrypi-settings.service -n 50
```

---

<a name="русский"></a>
## Русский

Сервер управления оборудованием на Raspberry Pi 5. Управляет камерой, спектрометром и устройством управления подсветкой. Получает команды через REST API по Ethernet и непрерывно передаёт данные (видео или спектр) в ответ.

### Обзор

Компонент Raspberry Pi работает как слой управления оборудованием, обеспечивая:
- REST API для управления устройствами (порт 8000)
- MJPEG сервер видеопотока (порт 8080)
- Поток данных спектрометра (порт 8081)
- Базу данных SQLite для хранения настроек (единый источник правды)
- Аппаратный интерфейс для камеры (Picamera2), спектрометра и переключателя подсветки

### Архитектура

```
RaspberryPi/
├── main.py                    # Точка входа - запускает все сервисы
├── requirements.txt           # Зависимости Python
├── raspberrypi-settings.service  # Файл systemd сервиса
├── README.md                  # Эта документация (EN/RU)
│
├── src/
│   ├── config/               # Конфигурация
│   │   └── raspberry_pi_config.py
│   │
│   ├── core/                 # Основные модули стриминга
│   │   ├── streaming.py           # MJPEG сервер видеопотока
│   │   └── spectrum_streaming.py  # Стриминг данных спектрометра
│   │
│   └── services/             # Сервисы управления оборудованием
│       ├── fastapi_server.py      # FastAPI REST endpoints
│       ├── camera_service.py      # Интеграция Picamera2
│       ├── spectrometer_service.py # Управление спектрометром
│       ├── light_switcher_service.py # Управление подсветкой Arduino
│       └── database_service.py     # Операции с SQLite
│
├── Spectrometer/             # Утилиты спектрометра
│   ├── Get_data/            # Скрипты сбора данных
│   └── Visualization/       # Инструменты визуализации
│
└── Light_switcher/          # Управление подсветкой Arduino
    ├── light_switcher_distance_switch/
    └── light_switcher_end_switch.ino/
```

### Сервисы

| Сервис | Порт | Описание |
|--------|------|----------|
| FastAPI Сервер | 8000 | REST API для управления устройствами и настройками |
| Видеопоток | 8080 | MJPEG видеопоток с камеры |
| Поток Спектра | 8081 | Поток данных спектрометра в реальном времени |

### Требования к оборудованию

- **Raspberry Pi 5** (с достаточным охлаждением)
- **Камера**: Raspberry Pi Camera Module (через Picamera2)
- **Спектрометр**: USB спектрометр
- **Переключатель подсветки**: Модуль управления подсветкой на Arduino

### Установка

1. **Подготовка Raspberry Pi:**
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Включение интерфейсов камеры и GPIO
sudo raspi-config
# Interface Options → Camera → Enable
# Interface Options → GPIO → Enable
```

2. **Установка зависимостей:**
```bash
cd /home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi
pip3 install -r requirements.txt
```

3. **Инициализация базы данных (автоматическая при первом запуске):**
```bash
python3 main.py
```

### Запуск сервера

#### Ручной запуск
```bash
cd /home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi
python3 main.py
```

#### Автозапуск через Systemd

Файл сервиса `raspberrypi-settings.service` предоставлен.

**Установка:**
```bash
sudo cp raspberrypi-settings.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable raspberrypi-settings.service
sudo systemctl start raspberrypi-settings.service
```

**Управление:**
```bash
sudo systemctl status raspberrypi-settings.service  # Проверить статус
sudo systemctl start raspberrypi-settings.service   # Запуск
sudo systemctl stop raspberrypi-settings.service    # Остановка
sudo systemctl restart raspberrypi-settings.service # Перезапуск
sudo journalctl -u raspberrypi-settings.service -f    # Просмотр логов
```

### API Endpoints

Базовый URL: `http://<ip-raspberry-pi>:8000/api`

#### Проверка работоспособности и статус
- `GET /api/health` — Проверка работоспособности сервера
- `GET /api/status` — Получить текущий статус системы

#### Управление настройками
- `GET /api/settings/{table}` — Получить все настройки из таблицы
- `GET /api/settings/{table}/slot/{slot_id}` — Получить конкретный слот (0-9)
- `POST /api/settings/update` — Обновить один параметр
- `POST /api/settings/{table}` — Обновить все настройки
- `POST /api/settings/{table}/save-slot/{slot_id}` — Сохранить в слот
- `GET /api/settings/{table}/validation-rules` — Получить правила валидации

#### Управление камерой
- `GET /api/camera/stream` — Статус видеопотока
- `POST /api/camera/mode/{mode}` — Установить режим камеры (camera/spectrometer/wells)

#### Спектрометр
- `GET /api/spectrometer/data` — Получить текущие данные спектра
- `POST /api/spectrometer/integration-time` — Установить время интеграции
- `POST /api/spectrometer/dark-spectrum` — Установить/очистить темновой спектр

### Потоки

**Видеопоток:**
```
http://<ip-raspberry-pi>:8080/video
```

**Проверка статуса:**
```
http://<ip-raspberry-pi>:8080/status
```

**Поток спектра:**
```
http://<ip-raspberry-pi>:8081/stream
```

### База данных

- **Расположение**: `/home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi/DevicesSettings.db`
- **Тип**: SQLite3
- **Таблицы**:
  - `CameraSettings` — Параметры камеры (10 слотов)
  - `SpectrometerSettings` — Параметры спектрометра (10 слотов)
  - `PositionerSettings` — Параметры позиционера (10 слотов)

База данных является **единым источником правды** для всех настроек устройств. DesktopApp подключается только через API.

### Устранение неполадок

**Камера не обнаружена:**
```bash
# Проверка подключения камеры
libcamera-hello --list-cameras

# Перезапуск сервиса камеры
sudo systemctl restart raspberrypi-settings.service
```

**База данных заблокирована:**
```bash
# Проверка блокировок
lsof DevicesSettings.db

# Перезапуск сервиса
sudo systemctl restart raspberrypi-settings.service
```

**API не отвечает:**
```bash
# Проверка порта 8000
sudo lsof -i :8000

# Просмотр логов сервиса
sudo journalctl -u raspberrypi-settings.service -n 50
```
