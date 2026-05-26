# RaspberryPi Server / Сервер Raspberry Pi

**[English](#english) | [Русский](#русский)**

---

<a name="english"></a>
## English

Hardware control server running on Raspberry Pi 5. Manages camera, spectrometer, light control, and positioner. Provides REST API and streaming services.

### Services

| Service | Port | Description |
|---------|------|-------------|
| FastAPI | 8000 | REST API for device control |
| Video | 8080 | MJPEG camera stream |
| Spectrum | 8081 | Spectrometer data stream |

### Project Structure

```
RaspberryPi/
├── main.py                         # Entry point - starts all services
├── requirements.txt                # Dependencies
├── raspberrypi-settings.service    # Systemd service file
├── raspberrypi-settings            # Service helper script
├── light_switcher_daemon.sh        # Light switcher daemon script
├── src/
│   ├── config/
│   │   └── settings.py            # Server configuration
│   ├── core/
│   │   ├── streaming.py           # MJPEG video streaming
│   │   └── spectrum_streaming.py  # Spectrometer streaming
│   ├── services/
│   │   ├── fastapi_server.py      # FastAPI REST endpoints
│   │   ├── camera_service.py      # Picamera2 integration
│   │   ├── spectrometer_service.py # Spectrometer control
│   │   ├── light_switcher_service.py # Arduino light control
│   │   ├── light_switcher_daemon.py  # Light switcher daemon
│   │   ├── database_service.py     # SQLite operations
│   │   └── database_ini.py        # Database initialization
│   └── utils/
│       └── error_handlers.py      # Error handling
├── Spectrometer/                   # Standalone spectrometer utilities
│   ├── Get_data/                  # Data acquisition scripts
│   ├── Visualization/               # Visualization tools
│   └── run.sh                       # Launch script
└── Light_switcher/                 # Arduino sketches
    ├── light_switcher_distance_switch/   # Distance-based switch
    └── light_switcher_end_switch/        # End-stop switch
```

### Hardware Requirements

- **Raspberry Pi 5** (with cooling)
- **Camera**: Raspberry Pi Camera Module (via Picamera2)
- **Spectrometer**: USB spectrometer
- **Light Switcher**: Arduino-based module

### Installation

```bash
# Update system and enable interfaces
sudo apt update && sudo apt upgrade -y
sudo raspi-config
# Interface Options → Camera → Enable
# Interface Options → GPIO → Enable

# Install dependencies
cd RaspberryPi
pip3 install -r requirements.txt
```

### Running

**Manual:**
```bash
python3 main.py
```

**Systemd service:**
```bash
sudo cp raspberrypi-settings.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable raspberrypi-settings.service
sudo systemctl start raspberrypi-settings.service
```

### Database

- **File**: `DevicesSettings.db` (SQLite3)
- **Tables**: `CameraSettings`, `SpectrometerSettings`, `PositionerSettings` (10 slots each)
- **Note**: Database is the single source of truth, accessed via API only

### API Endpoints

Base URL: `http://<raspberry-pi-ip>:8000/api`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/settings/{table}` | GET/POST | Get/update settings |
| `/settings/{table}/slot/{id}` | GET | Get slot (0-9) |
| `/settings/update` | POST | Update single parameter |
| `/spectrometer/data` | GET | Get spectrum data |
| `/camera/mode/{mode}` | POST | Set mode (camera/spectrometer/positioner) |

---

<a name="русский"></a>
## Русский

Сервер управления оборудованием на Raspberry Pi 5. Управляет камерой, спектрометром, подсветкой и позиционером. Предоставляет REST API и стриминговые сервисы.

### Сервисы

| Сервис | Порт | Описание |
|--------|------|----------|
| FastAPI | 8000 | REST API для управления устройствами |
| Video | 8080 | MJPEG поток с камеры |
| Spectrum | 8081 | Поток данных спектрометра |

### Структура проекта

```
RaspberryPi/
├── main.py                         # Точка входа - запускает все сервисы
├── requirements.txt                # Зависимости
├── raspberrypi-settings.service    # Файл systemd сервиса
├── raspberrypi-settings            # Вспомогательный скрипт сервиса
├── light_switcher_daemon.sh        # Скрипт демона подсветки
├── src/
│   ├── config/
│   │   └── settings.py            # Конфигурация сервера
│   ├── core/
│   │   ├── streaming.py           # MJPEG видеостриминг
│   │   └── spectrum_streaming.py  # Стриминг спектрометра
│   ├── services/
│   │   ├── fastapi_server.py      # FastAPI endpoints
│   │   ├── camera_service.py      # Интеграция Picamera2
│   │   ├── spectrometer_service.py # Управление спектрометром
│   │   ├── light_switcher_service.py # Управление подсветкой Arduino
│   │   ├── light_switcher_daemon.py  # Демон подсветки
│   │   ├── database_service.py     # Операции с SQLite
│   │   └── database_ini.py        # Инициализация БД
│   └── utils/
│       └── error_handlers.py      # Обработка ошибок
├── Spectrometer/                   # Автономные утилиты спектрометра
│   ├── Get_data/                  # Скрипты сбора данных
│   ├── Visualization/               # Инструменты визуализации
│   └── run.sh                       # Скрипт запуска
└── Light_switcher/                 # Скетчи Arduino
    ├── light_switcher_distance_switch/   # Дистанционный переключатель
    └── light_switcher_end_switch/        # Концевой переключатель
```

### Требования к оборудованию

- **Raspberry Pi 5** (с охлаждением)
- **Камера**: Raspberry Pi Camera Module (через Picamera2)
- **Спектрометр**: USB спектрометр
- **Переключатель подсветки**: Модуль на Arduino

### Установка

```bash
# Обновление системы и включение интерфейсов
sudo apt update && sudo apt upgrade -y
sudo raspi-config
# Interface Options → Camera → Enable
# Interface Options → GPIO → Enable

# Установка зависимостей
cd RaspberryPi
pip3 install -r requirements.txt
```

### Запуск

**Вручную:**
```bash
python3 main.py
```

**Сервис Systemd:**
```bash
sudo cp raspberrypi-settings.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable raspberrypi-settings.service
sudo systemctl start raspberrypi-settings.service
```

### База данных

- **Файл**: `DevicesSettings.db` (SQLite3)
- **Таблицы**: `CameraSettings`, `SpectrometerSettings`, `PositionerSettings` (по 10 слотов)
- **Примечание**: База данных — единый источник правды, доступ только через API

### API Endpoints

Базовый URL: `http://<ip-raspberry-pi>:8000/api`

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/health` | GET | Проверка работоспособности |
| `/settings/{table}` | GET/POST | Получить/обновить настройки |
| `/settings/{table}/slot/{id}` | GET | Получить слот (0-9) |
| `/settings/update` | POST | Обновить параметр |
| `/spectrometer/data` | GET | Получить данные спектра |
| `/camera/mode/{mode}` | POST | Установить режим (camera/spectrometer/positioner) |
