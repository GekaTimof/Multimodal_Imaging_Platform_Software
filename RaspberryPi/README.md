Эта часть кода размещается на Raspberry Pi и отвечает за подключение и сбор данных с приборов.
Получает команды как API по Ethernet и постоянно отправляет данные в ответ (видео поток или поток спектров).

# Архитектура Raspberry Pi

- `main.py` — точка входа, запускает API сервер (порт 8000), камеру (порт 8080) и спектрометр (порт 8081)
- `src/core/streaming.py` — MJPEG сервер видеопотока
- `src/core/spectrum_streaming.py` — сервер потока спектров
- `src/services/fastapi_server.py` — API endpoints для управления настройками
- `src/services/camera_service.py` — работа с Picamera2
- `src/services/spectrometer_service.py` — работа со спектрометром
- `src/services/light_switcher_service.py` — управление Arduino переключателем
- `src/services/database_service.py` — работа с настройками в SQLite

# Запуск

```bash
cd /home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi
python3 main.py
```

# Автозапуск через systemd

Файл сервиса уже создан: `raspberrypi-settings.service`

## Установка:

```bash
sudo cp raspberrypi-settings.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable raspberrypi-settings.service
sudo systemctl start raspberrypi-settings.service
```

## Управление:

```bash
sudo systemctl status raspberrypi-settings.service  # статус
sudo systemctl start raspberrypi-settings.service   # запуск
sudo systemctl stop raspberrypi-settings.service    # остановка
sudo systemctl restart raspberrypi-settings.service # перезапуск
sudo journalctl -u raspberrypi-settings.service -f  # логи
```

## Проверка работы

Откройте в браузере или на компьютере:

```
http://<IP-адрес-RaspberryPi>:8080/status
```

Если всё работает, должен вернуться `OK`.

Потом вы можете смотреть поток по адресу:

```
http://<IP-адрес-RaspberryPi>:8080/video
```

## Тестовый визуальный режим

Для локальной визуальной проверки камеры используйте приложение в папке `RaspberryPi/test_camera_app/`.
Оно работает независимо от основного стримингового сервиса и не влияет на работу HTTP-потока.
