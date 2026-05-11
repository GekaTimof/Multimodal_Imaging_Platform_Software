# Spectrometer Integration

This document describes the integration of the Optosky spectrometer into the Multimodal Imaging Platform.

## Overview

The spectrometer module has been successfully integrated following the same patterns as the camera service:

- **Service Layer**: `src/services/spectrometer_service.py`
- **Streaming Server**: `src/core/spectrum_streaming.py`
- **Database Integration**: Extended `src/services/database_service.py`
- **Main Application**: Updated `main.py` to run both services

## Features Implemented

### 1. Spectrometer Service (`SpectrometerService`)

**Core Functionality:**
- Real-time spectrum data capture from Optosky spectrometer
- Test data generation when spectrometer is not available
- Thread-safe data access with locks
- Automatic fallback to test mode on connection failure

**Parameter Management:**
- Integration time control (1-99999)
- Dark spectrum capture and correction
- Overillumination detection
- Settings persistence to database

**Dark Spectrum Handling:**
- Capture dark spectrum from spectrometer
- Save dark spectrum files to Raspberry Pi (`data/dark_spectra/`)
- Load dark spectrum from files
- Automatic dark correction of spectrum data

### 2. Database Integration

**New Table: `SpectrometerSettings`**
```sql
CREATE TABLE SpectrometerSettings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    SettingsName TEXT NOT NULL DEFAULT 'Basic',
    IntegralTime INTEGER NOT NULL DEFAULT 100,
    DarkSpectrumPath TEXT DEFAULT '',
    AutoDarkCorrection INTEGER NOT NULL DEFAULT 1,
    OverilluminationThreshold INTEGER NOT NULL DEFAULT 65535,
    LastUpdated TEXT DEFAULT CURRENT_TIMESTAMP
);
```

**Database Methods:**
- `get_spectrometer_settings()` - Load settings from database
- `save_spectrometer_settings(settings)` - Save settings to database
- Parameter validation with proper bounds checking

### 3. Streaming Server (`SpectrumStreamServer`)

**Endpoints:**
- `GET /spectrum` - Server-Sent Events stream of real-time spectrum data
- `GET /spectrum/single` - Single spectrum snapshot as JSON
- `GET /info` - Spectrometer information as JSON
- `GET /status` - Health check

**Control Endpoints:**
- `GET /control/set_integral_time?time=<value>` - Set integration time
- `GET /control/set_dark_spectrum` - Capture and set dark spectrum
- `GET /control/clear_dark_spectrum` - Clear dark spectrum
- `GET /control/reload_settings` - Reload settings from database
- `POST /control/load_dark_spectrum` - Upload dark spectrum file

**Data Format:**
```json
{
    "timestamp": 1234567890.123,
    "wavelength": [200.1, 200.2, ...],
    "spectrum": [1000, 1050, ...],
    "real_spectrum": [950, 1000, ...],
    "overillumination": false
}
```

### 4. Main Application Integration

**Multi-Server Architecture:**
- Camera streaming server on port 8080
- Spectrometer streaming server on port 8081
- Both run in separate daemon threads
- Graceful shutdown on Ctrl+C

## Usage

### Starting the Application

```bash
cd /home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi
python3 main.py
```

**Output:**
```
Starting Multimodal Imaging Platform...
Camera stream will be available at http://0.0.0.0:8080/video
Spectrum stream will be available at http://0.0.0.0:8081/spectrum
Press Ctrl+C to stop both servers
```

### Testing the Spectrometer Service

```bash
python3 test_spectrometer.py
```

### Accessing Spectrum Data

**Real-time Stream (Server-Sent Events):**
```javascript
const eventSource = new EventSource('http://raspberry-pi-ip:8081/spectrum');
eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Spectrum data:', data);
    // Process wavelength, spectrum, real_spectrum arrays
};
```

**Single Snapshot:**
```bash
curl http://raspberry-pi-ip:8081/spectrum/single
```

**Spectrometer Info:**
```bash
curl http://raspberry-pi-ip:8081/info
```

**Control Integration Time:**
```bash
curl "http://raspberry-pi-ip:8081/control/set_integral_time?time=500"
```

## File Structure

```
RaspberryPi/
├── src/
│   ├── services/
│   │   ├── spectrometer_service.py    # Main spectrometer service
│   │   ├── database_service.py        # Extended with spectrometer support
│   │   └── camera_service.py        # Original camera service
│   ├── core/
│   │   ├── spectrum_streaming.py     # Spectrum streaming server
│   │   └── streaming.py            # Camera streaming server
│   └── config/
│       └── settings.py              # Configuration with DATA_DIR
├── data/
│   └── dark_spectra/               # Dark spectrum files
├── Spectrometer/                  # Original spectrometer module
│   ├── Get_data/                  # Optosky C implementation
│   └── Visualization/             # PyQt5 GUI application
├── main.py                       # Updated main application
└── test_spectrometer.py           # Test script
```

## Configuration

**Environment Variables:**
- `DATA_DIR` - Directory for data storage (default: `../data`)
- `DEFAULT_FPS` - Default FPS for spectrum capture (default: 20)

**Database Settings:**
- Integration time range: 1-99999
- Overillumination threshold: 0-65535
- Auto dark correction: boolean

## Error Handling

**Graceful Degradation:**
- Falls back to test data if spectrometer is not available
- Continues operation if spectrometer connection is lost
- Thread-safe error handling

**Logging:**
- Comprehensive logging for debugging
- Error messages for connection issues
- Status information for monitoring

## Dependencies

**Required:**
- NumPy (for data processing)
- Existing spectrometer module (Optosky)
- Database service integration

**Optional:**
- Real spectrometer hardware (falls back to test data)

## Future Enhancements

1. **Spectrum Analysis**: Add peak detection and analysis features
2. **Calibration**: Implement wavelength calibration routines
3. **Data Export**: Add spectrum data export in various formats
4. **Web Interface**: Create web-based control interface
5. **Multiple Spectrometers**: Support for multiple spectrometer devices

## Troubleshooting

**Common Issues:**

1. **Spectrometer not found:**
   - Check spectrometer hardware connection
   - Verify OptoskyDemo executable permissions
   - Check system logs for USB device errors

2. **Database errors:**
   - Run database initialization: `python3 -c "from src.services import database_ini; database_ini.main()"`
   - Check file permissions for database directory

3. **Streaming issues:**
   - Verify port availability (8080, 8081)
   - Check firewall settings
   - Test with curl commands

4. **Dark spectrum issues:**
   - Ensure proper dark conditions when capturing
   - Check file permissions for data directory
   - Verify disk space availability

**Debug Mode:**
Enable debug logging by setting environment variable:
```bash
export LOG_LEVEL=DEBUG
python3 main.py
```
