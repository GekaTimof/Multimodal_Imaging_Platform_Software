# Light Switcher Service

Сервис для управления Arduino переключателем концевиков, который подключается к Raspberry Pi через Serial порт.

## Обзор

Система состоит из:
- **Arduino** с прошивкой `light_switcher_end_switch.ino` для управления шаговым двигателем и концевиками
- **Python сервиса** (`src/services/light_switcher_service.py`) для связи с Arduino через Serial
- **REST API** (в составе `main.py`) для управления переключателем

## Функциональность

- Подключение к Arduino через Serial порт
- Переключение между двумя состояниями (левый/правый концевик)
- Мониторинг состояния соединения
- Автоматическое переподключение при обрыве связи
- REST API для удаленного управления

## API Endpoints

### Проверка статуса
```bash
GET /api/light-switcher/status
```

Возвращает информацию о подключении и текущем состоянии.

### Подключение к Arduino
```bash
POST /api/light-switcher/connect
```

Устанавливает соединение с Arduino.

### Переключение состояния
```bash
POST /api/light-switcher/switch
Content-Type: application/json

{
  "state": "state1"  // или "state2"
}
```

Переключает в указанное состояние:
- `state1` - левый концевик
- `state2` - правый концевик

### Отключение
```bash
POST /api/light-switcher/disconnect
```

Разрывает соединение с Arduino.

## Установка

Light Switcher управляется через API сервер (запускается через `main.py`).
Отдельная установка не требуется.

## Тестирование

### Тестирование API

1. **Запустите основной сервер:**
```bash
cd /home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi
python3 main.py
```

2. **Проверка статуса:**
```bash
curl -X GET http://localhost:8000/api/light-switcher/status
```

3. **Подключение:**
```bash
curl -X POST http://localhost:8000/api/light-switcher/connect
```

4. **Переключение в состояние 1:**
```bash
curl -X POST http://localhost:8000/api/light-switcher/switch \
     -H 'Content-Type: application/json' \
     -d '{"state":"state1"}'
```

5. **Переключение в состояние 2:**
```bash
curl -X POST http://localhost:8000/api/light-switcher/switch \
     -H 'Content-Type: application/json' \
     -d '{"state":"state2"}'
```

## Аппаратное подключение

### Arduino подключение:
- **Шаговый двигатель**: пины 2, 3, 4, 5
- **Левый концевик**: пин 13
- **Правый концевик**: пин 12
- **Serial**: пины 0 (RX), 1 (TX) или USB-Serial конвертер

### Raspberry Pi подключение:
- **USB-Serial**: обычно `/dev/ttyUSB0` или `/dev/ttyACM0`
- **GPIO Serial**: `/dev/ttyAMA0` (требует настройки)

## Конфигурация

### Изменение Serial порта

Отредактируйте файл `src/services/light_switcher_service.py`:

```python
# Измените порт по умолчанию
self.port = "/dev/ttyUSB0"  # или другой порт
```

### Изменение скорости передачи

```python
self.baudrate = 9600  # должна соответствовать настройкам Arduino
```

## Логирование

Логи доступны через journal основного сервиса:
```bash
sudo journalctl -u raspberrypi-settings.service -f
```

## Возможные проблемы

### 1. Нет доступа к Serial порту
```bash
sudo usermod -a -G dialout pi
# и перезагрузка
```

### 2. Arduino не отвечает
- Проверьте подключение
- Убедитесь что Arduino запущена с правильной прошивкой
- Проверьте правильность порта и скорости

### 3. API не отвечает
```bash
# Проверьте логи основного сервиса
sudo journalctl -u raspberrypi-settings.service -f
```

## Структура файлов

```
RaspberryPi/
├── src/services/
│   ├── light_switcher_service.py      # Основной сервис
│   └── fastapi_server.py              # API сервер
├── raspberrypi-settings.service        # Systemd конфиг (общий)
└── Light_switcher/
    ├── light_switcher_end_switch.ino/  # Прошивка Arduino
    └── README.md                       # Этот файл
```

## Разработка

### Добавление новых команд

1. Добавьте команду в Arduino прошивку
2. Добавьте метод в `LightSwitcherService`
3. Добавьте API endpoint при необходимости

### Тестирование

```bash
cd /home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi
python3 src/services/light_switcher_service.py
```
