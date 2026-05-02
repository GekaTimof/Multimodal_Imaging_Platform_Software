# DesktopApp

Это графический интерфейс, с которым работает пользователь.

## Что делает

- Показывает вкладки `Spectrometer`, `Camera` и `Wells`.
- При переключении вкладок будет отправлять команды на Raspberry Pi.
- Получает от Raspberry Pi данные: видео или спектры.

## Как запустить

1. Перейдите в папку приложения:

```bash
cd DesktopApp
```

2. Установите зависимости:

```bash
pip install -r requirements.txt
```

3. Запустите приложение:

```bash
python main.py
```

## Где добавить логику смены режима

- `DesktopApp/services/raspberry_mode.py` — здесь будут пустые функции для отправки команд.
- `DesktopApp/threads/main_window_thread.py` — здесь происходит переключение вкладок.
