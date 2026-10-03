# RaspberryPi Server / Сервер Raspberry Pi

**[English](#english) | [Русский](#русский)**

---

<a name="english"></a>
## English

Hardware control server running on Raspberry Pi 5. Manages camera, spectrometer, light control, and positioner. Provides a FastAPI REST API and streaming services for the DesktopApp.

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
├── requirements.txt                # Python dependencies
├── raspberrypi-settings.service    # systemd service unit
├── scripts/
│   ├── daemons/
│   │   ├── light_switcher_daemon.py   # Standalone light switcher watchdog
│   │   └── light_switcher_daemon.sh   # SysV-style control script
│   └── spectrometer_check.py       # Spectrometer diagnostics script
├── src/
│   ├── api/                        # FastAPI per-device routers
│   │   ├── __init__.py
│   │   ├── camera.py              # Camera API endpoints
│   │   ├── common.py              # Shared Pydantic models
│   │   ├── light_switcher.py      # Light switcher API endpoints
│   │   ├── positioner.py          # Positioner API endpoints
│   │   └── settings.py            # Generic settings endpoints
│   ├── config/
│   │   └── settings.py            # Server configuration
│   ├── core/
│   │   ├── http_utils.py          # Threaded HTTP server helper
│   │   ├── spectrum_streaming.py  # Spectrometer streaming server
│   │   └── streaming.py           # MJPEG video streaming server
│   ├── services/
│   │   ├── camera_backends.py     # Pluggable camera backends (rpicam/OpenCV/test)
│   │   ├── camera_service.py      # High-level camera service
│   │   ├── database_ini.py        # Database initialization and migrations
│   │   ├── database_service.py    # SQLite operations
│   │   ├── fastapi_server.py     # FastAPI app, spectrometer endpoints, exception handlers
│   │   ├── light_switcher_service.py # Arduino light switcher control
│   │   ├── positioner_service.py  # GRBL positioner control
│   │   └── spectrometer_service.py # Spectrometer control (kept unchanged)
│   └── utils/
│       └── error_handlers.py      # Error handling decorators
├── Spectrometer/                 # Standalone spectrometer utilities
├── Light_switcher/                # Arduino sketches
├── Camera_test/                   # Legacy camera test script
├── Positioner_test/               # Legacy positioner test script
└── DevicesSettings.db             # Single SQLite database (ignored by git)
```

### Hardware Requirements

- **Raspberry Pi 5** (with cooling)
- **Camera**: Raspberry Pi Camera Module (IMX477 via rpicam-apps, with OpenCV fallback)
- **Spectrometer**: USB spectrometer (Optosky)
- **Positioner**: MKS DLC32 GRBL controller over USB serial
- **Light Switcher**: Arduino-based module over USB serial

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
- **Tables**: `CameraSettings`, `SpectrometerSettings`, `PositionerSettings`
- Each table supports slots 0–10 (slot 0 = current session, 1–10 = saved presets)
- Database is the single source of truth and is accessed via API only

### API Endpoints

Base URL: `http://<raspberry-pi-ip>:8000/api`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/settings/{table}` | GET | Get all settings from a table |
| `/settings/update` | POST | Update a single parameter |
| `/settings/camera` | GET/POST | Get/update current camera settings |
| `/settings/camera/slot/{id}` | GET | Get camera settings slot |
| `/settings/camera/slots` | GET | Get all camera slots |
| `/settings/camera/save-slot/{id}` | POST | Save camera settings to slot |
| `/settings/camera/load-slot/{id}` | POST | Load camera settings from slot |
| `/settings/camera/apply` | POST | Apply camera settings without saving to DB |
| `/settings/camera/validation-rules` | GET | Camera validation ranges |
| `/camera/photo` | POST | Capture high-quality photo |
| `/camera/awb-gains` | GET | Read current AWB gains |
| `/spectrometer/settings` | GET/POST | Get/update spectrometer settings |
| `/spectrometer/info` | GET | Spectrometer hardware info |
| `/spectrometer/spectrum` | GET | Single spectrum snapshot |
| `/spectrometer/integral-time` | POST | Set integration time |
| `/spectrometer/dark-spectrum/*` | POST/GET | Dark spectrum capture/clear/load/get |
| `/spectrometer/reconnect` | POST | Reinitialize spectrometer |
| `/light-switcher/status` | GET | Get switcher status |
| `/light-switcher/connect` | POST | Connect to Arduino |
| `/light-switcher/switch` | POST | Switch to state1/state2 |
| `/light-switcher/disconnect` | POST | Disconnect from Arduino |
| `/positioner/settings` | GET/POST | Get/update positioner settings |
| `/positioner/settings/slots` | GET | Get all positioner slots |
| `/positioner/settings/{slot_id}` | GET | Get positioner slot |
| `/positioner/settings/{slot_id}` | POST | Save positioner settings to slot |
| `/positioner/settings/load/{slot_id}` | POST | Load positioner settings from slot |
| `/positioner/limits` | GET | Get calibrated axis limits |
| `/positioner/status` | GET | Get positioner status |
| `/positioner/connect` | POST | Connect to positioner |
| `/positioner/move` | POST | Move to absolute coordinates |
| `/positioner/home` | POST | Home positioner |
| `/positioner/stop` | POST | Feed hold / stop motion |
| `/positioner/busy` | GET | Query busy state |
| `/positioner/calibrate` | POST | Calibrate all axes |
| `/positioner/calibrate/{axis}` | POST | Calibrate single axis |

### Tests

```bash
python3 -m unittest discover -s tests -v
```

---

<a name="русский"></a>
## Русский

Сервер управления оборудованием на Raspberry Pi 5. Управляет камерой, спектрометром, подсветкой и позиционером. Предоставляет REST API и стриминговые сервисы для DesktopApp.

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
├── requirements.txt                # Python-зависимости
├── raspberrypi-settings.service    # Юнит systemd
├── scripts/
│   ├── daemons/
│   │   ├── light_switcher_daemon.py   # Демон подсветки
│   │   └── light_switcher_daemon.sh   # Скрипт управления демоном
│   └── spectrometer_check.py       # Диагностика спектрометра
├── src/
│   ├── api/                        # FastAPI-роутеры по устройствам
│   │   ├── __init__.py
│   │   ├── camera.py              # Эндпоинты камеры
│   │   ├── common.py              # Общие Pydantic-модели
│   │   ├── light_switcher.py      # Эндпоинты переключателя подсветки
│   │   ├── positioner.py          # Эндпоинты позиционера
│   │   └── settings.py            # Общие эндпоинты настроек
│   ├── config/
│   │   └── settings.py            # Конфигурация сервера
│   ├── core/
│   │   ├── http_utils.py          # Threaded HTTP server
│   │   ├── spectrum_streaming.py  # Стриминг спектрометра
│   │   └── streaming.py           # MJPEG видеостриминг
│   ├── services/
│   │   ├── camera_backends.py     # Бэкенды камеры (rpicam/OpenCV/test)
│   │   ├── camera_service.py      # Высокоуровневый сервис камеры
│   │   ├── database_ini.py        # Инициализация и миграции БД
│   │   ├── database_service.py    # Операции SQLite
│   │   ├── fastapi_server.py     # FastAPI-приложение, эндпоинты спектрометра
│   │   ├── light_switcher_service.py # Управление Arduino подсветкой
│   │   ├── positioner_service.py  # Управление позиционером GRBL
│   │   └── spectrometer_service.py # Управление спектрометром (без изменений)
│   └── utils/
│       └── error_handlers.py      # Обработчики ошибок
├── Spectrometer/                 # Утилиты спектрометра
├── Light_switcher/                # Скетчи Arduino
├── Camera_test/                   # Легаси-скрипт теста камеры
├── Positioner_test/               # Легаси-скрипт теста позиционера
└── DevicesSettings.db             # База SQLite (исключена из git)
```

### Требования к оборудованию

- **Raspberry Pi 5** (с охлаждением)
- **Камера**: Raspberry Pi Camera Module (IMX477 через rpicam-apps, с fallback на OpenCV)
- **Спектрометр**: USB-спектрометр (Optosky)
- **Позиционер**: GRBL-контроллер MKS DLC32 по USB serial
- **Переключатель подсветки**: Модуль на Arduino по USB serial

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
- **Таблицы**: `CameraSettings`, `SpectrometerSettings`, `PositionerSettings`
- Каждая таблица поддерживает слоты 0–10 (0 — текущая сессия, 1–10 — пресеты)
- База данных — единый источник правды, доступ только через API

### API Endpoints

Базовый URL: `http://<ip-raspberry-pi>:8000/api`

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/health` | GET | Проверка работоспособности |
| `/settings/{table}` | GET | Получить все настройки таблицы |
| `/settings/update` | POST | Обновить один параметр |
| `/settings/camera` | GET/POST | Получить/обновить настройки камеры |
| `/settings/camera/slot/{id}` | GET | Получить слот настроек камеры |
| `/settings/camera/slots` | GET | Получить все слоты камеры |
| `/settings/camera/save-slot/{id}` | POST | Сохранить настройки камеры в слот |
| `/settings/camera/load-slot/{id}` | POST | Загрузить настройки камеры из слота |
| `/settings/camera/apply` | POST | Применить настройки камеры без сохранения в БД |
| `/settings/camera/validation-rules` | GET | Диапазоны валидации камеры |
| `/camera/photo` | POST | Сделать фото высокого качества |
| `/camera/awb-gains` | GET | Прочитать текущие AWB-усиления |
| `/spectrometer/settings` | GET/POST | Получить/обновить настройки спектрометра |
| `/spectrometer/info` | GET | Информация о спектрометре |
| `/spectrometer/spectrum` | GET | Один снимок спектра |
| `/spectrometer/integral-time` | POST | Установить время интеграции |
| `/spectrometer/dark-spectrum/*` | POST/GET | Захват/очистка/загрузка/получение тёмного спектра |
| `/spectrometer/reconnect` | POST | Переинициализировать спектрометр |
| `/light-switcher/status` | GET | Статус переключателя |
| `/light-switcher/connect` | POST | Подключиться к Arduino |
| `/light-switcher/switch` | POST | Переключить в state1/state2 |
| `/light-switcher/disconnect` | POST | Отключиться от Arduino |
| `/positioner/settings` | GET/POST | Получить/обновить настройки позиционера |
| `/positioner/settings/slots` | GET | Все слоты позиционера |
| `/positioner/settings/{slot_id}` | GET | Слот позиционера |
| `/positioner/settings/{slot_id}` | POST | Сохранить слот позиционера |
| `/positioner/settings/load/{slot_id}` | POST | Загрузить слот позиционера |
| `/positioner/limits` | GET | Калиброванные пределы осей |
| `/positioner/status` | GET | Статус позиционера |
| `/positioner/connect` | POST | Подключить позиционер |
| `/positioner/move` | POST | Переместиться в абсолютные координаты |
| `/positioner/home` | POST | Домой |
| `/positioner/stop` | POST | Остановить движение |
| `/positioner/busy` | GET | Состояние занятости |
| `/positioner/calibrate` | POST | Калибровать все оси |
| `/positioner/calibrate/{axis}` | POST | Калибровать одну ось |

### Тесты

```bash
python3 -m unittest discover -s tests -v
```
