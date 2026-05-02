# Multimodal Imaging Platform Software

Простой проект для работы с приборами через Desktop App и Raspberry Pi.

## Структура проекта

- `DesktopApp/` — графический интерфейс на Python для управления устройствами.
- `RaspberryPi/` — код, который запускается на Raspberry Pi и обрабатывает команды.
- `requirements-base.txt` — базовые зависимости для всего проекта.

## Быстрый старт

1. Создайте виртуальное окружение и активируйте его:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Установите зависимости для корня проекта:

```bash
pip install -r requirements-base.txt
```

3. Запустите приложение на рабочей станции:

```bash
cd DesktopApp
python main.py
```

4. Запустите Raspberry Pi код на устройстве Raspberry Pi:

```bash
cd RaspberryPi
python main.py
```

## Что делает проект

- Desktop App отправляет команды на Raspberry Pi через сеть.
- Raspberry Pi отвечает данными от приборов: видео, спектры и другие измерения.
- Пользователь переключается между вкладками `Spectrometer`, `Camera`, `Wells`.

## Примечания

- Пока команды на Raspberry Pi можно добавить в `DesktopApp/services/raspberry_mode.py`.
- Основной GUI находится в `DesktopApp/threads/main_window_thread.py`.
