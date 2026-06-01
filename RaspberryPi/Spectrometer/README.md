# Spectrometer / Спектрометр

**[English](#english) | [Русский](#русский)**

---

<a name="english"></a>
## English

Spectrometer service for Raspberry Pi with streaming API and hardware integration.

### Quick Start

```bash
# Check spectrometer connection
cd /home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi
./spectrometer_daemon.sh check

# Start spectrometer service
./spectrometer_daemon.sh start

# Test spectrum capture
./spectrometer_daemon.sh test
```

### Service Management

The spectrometer can run as part of the main service or independently:

**Option 1: Main Service (recommended)**
```bash
# Start all services (API + Camera + Spectrometer)
sudo systemctl start raspberrypi-settings

# Check status
sudo systemctl status raspberrypi-settings
```

**Option 2: Independent Spectrometer Service**
```bash
# Install spectrometer service
./spectrometer_daemon.sh install

# Start/stop/restart
./spectrometer_daemon.sh start
./spectrometer_daemon.sh stop
./spectrometer_daemon.sh restart

# Check status and logs
./spectrometer_daemon.sh status
./spectrometer_daemon.sh logs
```

### API Endpoints

**FastAPI Endpoints (Port 8000):**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/spectrometer/settings` | GET | Get spectrometer settings from DB |
| `/api/spectrometer/settings` | POST | Update spectrometer settings |
| `/api/spectrometer/info` | GET | Get hardware info and status |
| `/api/spectrometer/spectrum` | GET | Get single spectrum snapshot |
| `/api/spectrometer/integral-time` | POST | Set integration time (1-99999 ms) |
| `/api/spectrometer/dark-spectrum/capture` | POST | Capture dark spectrum |
| `/api/spectrometer/dark-spectrum/clear` | POST | Clear dark spectrum |
| `/api/spectrometer/dark-spectrum/load` | POST | Load dark spectrum from file |
| `/api/spectrometer/validation-rules` | GET | Get parameter validation rules |

**Streaming Endpoints (Port 8081):**

| Endpoint | Description |
|----------|-------------|
| `/spectrum` | SSE stream of continuous spectrum data |
| `/spectrum/single` | Single spectrum snapshot (JSON) |
| `/info` | Spectrometer hardware info |
| `/control/set_integral_time?time=N` | Set integration time |
| `/control/set_dark_spectrum` | Capture dark spectrum |
| `/control/clear_dark_spectrum` | Clear dark spectrum |

### Database Schema

**SpectrometerSettings table:**
- `id` - Primary key (0 = current session)
- `SettingsName` - Profile name
- `IntegralTime` - Integration time in ms (1-99999)
- `DarkSpectrumPath` - Path to dark spectrum file
- `AutoDarkCorrection` - Auto apply dark correction (0/1)
- `OverilluminationThreshold` - Threshold for overillumination (0-65535)
- `LastUpdated` - Timestamp

### Dark Spectrum

The dark spectrum (background noise) is stored on Raspberry Pi and automatically applied:

```bash
# Capture dark spectrum (cover the spectrometer input!)
curl -X POST http://raspberry-pi-ip:8000/api/spectrometer/dark-spectrum/capture

# Check if dark spectrum is loaded
curl http://raspberry-pi-ip:8000/api/spectrometer/info

# Clear dark spectrum
curl -X POST http://raspberry-pi-ip:8000/api/spectrometer/dark-spectrum/clear
```

Dark spectrum files are saved to: `/home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi/data/dark_spectra/`

### Settings Slots

Spectrometer settings use the same slot system as the camera:
- Slot 0: Current session (volatile, applied immediately)
- Slots 1-10: Saved presets (persistent)

```bash
# Get current settings
curl http://raspberry-pi-ip:8000/api/spectrometer/settings

# Update settings
curl -X POST http://raspberry-pi-ip:8000/api/spectrometer/settings \
  -H "Content-Type: application/json" \
  -d '{"IntegralTime": 200, "AutoDarkCorrection": true}'
```

### Troubleshooting

```bash
# Check hardware connection
./spectrometer_daemon.sh check

# Test spectrum capture
./spectrometer_daemon.sh test

# View logs
./spectrometer_daemon.sh logs

# Check USB devices
lsusb | grep -i stm32

# Check kernel modules
lsmod | grep cdc
```

### Standalone Visualization

For standalone GUI visualization (not part of main service):

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
