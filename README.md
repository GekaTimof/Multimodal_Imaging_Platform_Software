# Multimodal Imaging Platform Software

A comprehensive platform for controlling scientific instruments through desktop application and Raspberry Pi.

## Overview

Software for managing spectrometer, camera, and wells analysis through an intuitive graphical interface with multilingual support.

## Project Structure

```
Multimodal_Imaging_Platform_Software/
├── README.md                    # This file
├── .gitignore                  # Git ignore patterns
├── requirements-base.txt       # Base dependencies
├── DesktopApp/                 # Desktop GUI application
│   ├── main.py                 # Application entry point
│   ├── README.md               # Desktop app documentation
│   ├── settings.json           # Application settings
│   ├── threads/                # Main window and threading
│   ├── tabs/                   # Device control tabs
│   ├── objects/                # Core classes and models
│   ├── services/               # Utility services
│   ├── widgets/                # UI components
│   └── language_variations/    # Internationalization
├── RaspberryPi/                # Raspberry Pi server code
│   ├── main.py                 # Server entry point
│   ├── README.md               # Pi server documentation
│   ├── services/               # Device control services
│   └── Spectrometer/           # Spectrometer control
├── tests/                     # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── fixtures/               # Test data and mocks
├── docs/                      # Documentation
│   └── reports/                # Development reports
└── Assets/                    # Static assets
```

## Quick Start

1. Create virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements-base.txt
```

3. Run desktop application:

```bash
cd DesktopApp
python main.py
```

4. Run Raspberry Pi server:

```bash
cd RaspberryPi
python main.py
```

## Features

### Camera Control
- IP camera video streaming
- Start/stop recording
- Image capture and saving
- Camera parameter configuration

### Spectrometer
- Spectral data acquisition
- Integration time adjustment
- Dark spectrum calibration
- Spectrum data export

### Wells Analysis
- Wells data visualization
- Analysis parameter settings

### User Interface
- Three-tab interface for different modes
- Multilingual support (English/Russian)
- Configurable device parameters
- Save directory management

## Testing

Run tests with:

```bash
# Unit tests
python -m pytest tests/unit/

# Integration tests
python -m pytest tests/integration/

# All tests
python -m pytest tests/
```

## Development

### Desktop Application
- **Framework**: PyQt5
- **Architecture**: MVC pattern with modular design
- **Internationalization**: JSON-based translation files
- **Configuration**: JSON settings file

### Raspberry Pi Server
- **Device Control**: GPIO and USB interfaces
- **Network**: RESTful API communication
- **Data Processing**: Real-time sensor data handling

## Documentation

- `DesktopApp/README.md` - Desktop application details
- `RaspberryPi/README.md` - Server implementation details
- `docs/reports/` - Development reports and analysis
