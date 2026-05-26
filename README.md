# Multimodal Imaging Platform / Мультимодальная Платформа

**[English](#english) | [Русский](#русский)**

---

<a name="english"></a>
## English

A platform for controlling scientific instruments (spectrometer, camera, positioner) through a PyQt5 desktop application connected to Raspberry Pi 5 hardware.

### Overview

- **DesktopApp** — PyQt5 GUI application running on user's computer
- **RaspberryPi** — Hardware control server running on Raspberry Pi 5

### Project Structure

```
├── DesktopApp/              # Desktop GUI application
│   ├── main.py             # Entry point
│   ├── src/
│   │   ├── config/        # Configuration (API, interface, theme)
│   │   ├── core/          # Constants and worker threads
│   │   ├── models/        # Data models and translations
│   │   ├── services/      # API clients and utilities
│   │   ├── ui/            # Main window, tabs, widgets
│   │   └── utils/         # Error handlers
│   ├── resources/         # Settings and translations
│   └── tests/             # Unit and integration tests
├── RaspberryPi/           # Hardware control server
│   ├── main.py            # Server entry point
│   ├── src/
│   │   ├── config/        # Server configuration
│   │   ├── core/          # Streaming servers (video, spectrum)
│   │   ├── services/      # FastAPI, camera, spectrometer, database
│   │   └── utils/         # Error handlers
│   ├── Spectrometer/      # Spectrometer utilities
│   └── Light_switcher/    # Arduino light control
└── docs/Diploma/          # Thesis materials
```

### Quick Start

```bash
# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 2. Install base dependencies
pip install -r requirements-base.txt

# 3. Start Raspberry Pi server
cd RaspberryPi
pip install -r requirements.txt
python main.py

# 4. Start Desktop App (in another terminal)
cd DesktopApp
pip install -r requirements.txt
python main.py
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| FastAPI | 8000 | REST API for device control |
| Video | 8080 | MJPEG camera stream |
| Spectrum | 8081 | Spectrometer data stream |

### Documentation

- `ARCHITECTURE.md` — Architecture overview
- `DesktopApp/README.md` — Desktop app details
- `RaspberryPi/README.md` — Server details

---

<a name="русский"></a>
## Русский

Платформа для управления научными приборами (спектрометр, камера, позиционер) через десктопное PyQt5-приложение, подключенное к оборудованию Raspberry Pi 5.

### Обзор

- **DesktopApp** — GUI-приложение на PyQt5, работающее на компьютере пользователя
- **RaspberryPi** — Сервер управления оборудованием на Raspberry Pi 5

### Структура проекта

```
├── DesktopApp/              # Десктопное GUI-приложение
│   ├── main.py             # Точка входа
│   ├── src/
│   │   ├── config/        # Конфигурация (API, интерфейс, тема)
│   │   ├── core/          # Константы и рабочие потоки
│   │   ├── models/        # Модели данных и переводы
│   │   ├── services/      # API-клиенты и утилиты
│   │   ├── ui/            # Главное окно, вкладки, виджеты
│   │   └── utils/         # Обработчики ошибок
│   ├── resources/         # Настройки и переводы
│   └── tests/             # Модульные и интеграционные тесты
├── RaspberryPi/           # Сервер управления оборудованием
│   ├── main.py            # Точка входа сервера
│   ├── src/
│   │   ├── config/        # Конфигурация сервера
│   │   ├── core/          # Стриминговые серверы (видео, спектр)
│   │   ├── services/      # FastAPI, камера, спектрометр, БД
│   │   └── utils/         # Обработчики ошибок
│   ├── Spectrometer/      # Утилиты спектрометра
│   └── Light_switcher/    # Управление подсветкой Arduino
└── docs/Diploma/          # Материалы диплома
```

### Быстрый старт

```bash
# 1. Создать виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 2. Установить базовые зависимости
pip install -r requirements-base.txt

# 3. Запустить сервер Raspberry Pi
cd RaspberryPi
pip install -r requirements.txt
python main.py

# 4. Запустить Desktop App (в другом терминале)
cd DesktopApp
pip install -r requirements.txt
python main.py
```

### Сервисы

| Сервис | Порт | Описание |
|--------|------|----------|
| FastAPI | 8000 | REST API для управления устройствами |
| Video | 8080 | MJPEG поток с камеры |
| Spectrum | 8081 | Поток данных спектрометра |

### Документация

- `ARCHITECTURE.md` — Обзор архитектуры
- `DesktopApp/README.md` — Детали десктопного приложения
- `RaspberryPi/README.md` — Детали сервера

---

## License / Лицензия

This project is part of a diploma thesis / Этот проект является частью дипломной работы.
