Эта часть кода размещается на Raspberry Pi и отвечает за подключение и сбор данных с приборов.
Получает команды как API по Ethernet и постоянно отправляет данные в ответ (видео поток или поток спектров).

# Архитектура Raspberry Pi

- `main.py` — точка входа, простая обёртка для запуска потока.
- `streaming.py` — содержит блок, который отвечает за создание MJPEG-сервера и выдачу видеопотока.
- `services/camera_service.py` — содержит блок захвата кадров с Picamera2 и предоставляет текущий JPEG-кадр.
- `test_camera_app/` — отдельная папка с визуальным тестовым приложением, которое остаётся для локальной проверки камеры.

# Автозапуск видеопотока

Сервер видеопотока запускается командой:

```bash
cd /home/minilumi/Multimodal_Imaging_Platform_Software
python3 -m RaspberryPi.main
```

## Создание systemd-сервиса

1. Создайте файл сервиса, например `/etc/systemd/system/raspberrypi-camera.service`.
2. Вставьте в него:

```ini
[Unit]
Description=Raspberry Pi camera MJPEG stream
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/minilumi/Multimodal_Imaging_Platform_Software
ExecStart=/usr/bin/python3 -m RaspberryPi.main
Restart=on-failure
User=minilumi
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

3. Перезагрузите демон systemd:

```bash
sudo systemctl daemon-reload
```

4. Включите автозапуск:

```bash
sudo systemctl enable raspberrypi-camera.service
```

5. Запустите сервис:

```bash
sudo systemctl start raspberrypi-camera.service
```

6. Проверьте статус:

```bash
sudo systemctl status raspberrypi-camera.service
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
