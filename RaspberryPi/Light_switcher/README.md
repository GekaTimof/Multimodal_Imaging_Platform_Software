# Light Switcher Service

Сервис для управления Arduino переключателем концевиков, который подключается к Raspberry Pi через Serial порт.

## Обзор

Система состоит из:
- **Arduino** с прошивкой `light_switcher_end_switch.ino` для управления шаговым двигателем и концевиками
- **Python сервиса** для связи с Arduino через Serial
- **REST API** для управления переключателем
- **Systemd демона** для постоянной работы сервиса

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

### Автоматическая установка

```bash
cd /home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi
sudo ./install_light_switcher_service.sh install
```

### Ручная установка

1. **Установка зависимостей:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-serial
pip3 install pyserial
```

2. **Настройка systemd сервиса:**
```bash
sudo ./install_light_switcher_service.sh setup
```

3. **Запуск сервиса:**
```bash
sudo ./install_light_switcher_service.sh start
```

## Управление сервисом

```bash
# Запуск
sudo ./install_light_switcher_service.sh start

# Остановка
sudo ./install_light_switcher_service.sh stop

# Перезапуск
sudo ./install_light_switcher_service.sh restart

# Проверка статуса
sudo ./install_light_switcher_service.sh status

# Просмотр логов
sudo ./install_light_switcher_service.sh logs

# Включение автозапуска
sudo ./install_light_switcher_service.sh enable

# Отключение автозапуска
sudo ./install_light_switcher_service.sh disable
```

## Тестирование

### Тест подключения к Arduino
```bash
./install_light_switcher_service.sh test
```

### Тестирование API

1. **Запустите FastAPI сервер:**
```bash
cd /home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi/services
python3 fastapi_server.py
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

Отредактируйте файл `services/light_switcher_service.py`:

```python
# Измените порт по умолчанию
self.port = "/dev/ttyUSB0"  # или другой порт
```

### Изменение скорости передачи

```python
self.baudrate = 9600  # должна соответствовать настройкам Arduino
```

## Логирование

Логи сервиса сохраняются в:
- `logs/light_switcher_daemon.log` - логи демона
- Systemd journal: `journalctl -u light-switcher.service`

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

### 3. Сервис не запускается
```bash
# Проверьте логи
sudo ./install_light_switcher_service.sh status
sudo ./install_light_switcher_service.sh logs
```

## Структура файлов

```
RaspberryPi/
├── services/
│   ├── light_switcher_service.py      # Основной сервис
│   ├── light_switcher_daemon.py       # Демон
│   └── fastapi_server.py              # API сервер (с добавленными endpoints)
├── light-switcher.service              # Systemd конфиг
├── install_light_switcher_service.sh   # Скрипт установки
├── logs/                              # Логи сервиса
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
python3 services/light_switcher_service.py
```
