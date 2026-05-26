# Spectrometer / Спектрометр

**[English](#english) | [Русский](#русский)**

---

<a name="english"></a>
## English

Standalone spectrometer visualization application for Raspberry Pi.

### Installation

```bash
# Install dependencies
pip3 install --user -r requirements.txt
```

### Configuration

Edit `run.sh`:
```bash
#!/bin/bash
sudo python3 /path/to/Visualization/main.py
```

### Running

```bash
./run.sh
```

### Customization

Edit `Visualization/SpectrometerApplication/Constants.py`:

| Parameter | Description |
|-----------|-------------|
| `BASE_FILES_DIR` | Default save/load directory |
| `DARK_THEME` | `True` = dark, `False` = light |
| `FONT_SIZE` | Button text size |
| `FONT` | Font family name |
| `WARNING_FONT_SIZE` | Saturation warning text size |
| `COORDINATES_FONT_SIZE` | Mouse coordinates text size |

### Desktop Shortcut

```bash
nano ~/.local/share/applications/spectrometer.desktop
```

```ini
[Desktop Entry]
Name=Spectrometer
Comment=Spectrometer Visualization Tool
Exec=/path/to/run.sh
Icon=/path/to/Visualization/Assets/icon.png
Terminal=false
Type=Application
Categories=Utility;
```

---

<a name="русский"></a>
## Русский

Автономное приложение визуализации спектрометра для Raspberry Pi.

### Установка

```bash
# Установка зависимостей
pip3 install --user -r requirements.txt
```

### Конфигурация

Отредактируйте `run.sh`:
```bash
#!/bin/bash
sudo python3 /path/to/Visualization/main.py
```

### Запуск

```bash
./run.sh
```

### Настройка

Отредактируйте `Visualization/SpectrometerApplication/Constants.py`:

| Параметр | Описание |
|----------|----------|
| `BASE_FILES_DIR` | Директория сохранения/загрузки по умолчанию |
| `DARK_THEME` | `True` = тёмная тема, `False` = светлая |
| `FONT_SIZE` | Размер текста кнопок |
| `FONT` | Название шрифта |
| `WARNING_FONT_SIZE` | Размер текста предупреждения о пересвете |
| `COORDINATES_FONT_SIZE` | Размер текста координат мыши |

### Ярлык на рабочем столе

```bash
nano ~/.local/share/applications/spectrometer.desktop
```

```ini
[Desktop Entry]
Name=Spectrometer
Comment=Spectrometer Visualization Tool
Exec=/путь/к/run.sh
Icon=/путь/к/Visualization/Assets/icon.png
Terminal=false
Type=Application
Categories=Utility;
``` 
