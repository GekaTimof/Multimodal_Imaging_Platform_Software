# Device Settings System Implementation

## Overview

I've implemented a comprehensive device settings system with minimal hard-coding and following proper programming practices. The system includes:

1. **Database schema** with proper camera parameters
2. **RESTful API** with validation for parameter updates
3. **Tabbed UI widget** for device configuration
4. **Integration** into the existing camera tab

## Architecture

### 1. Database Layer (`RaspberryPi/services/`)

#### `database_ini.py`
- Updated `CameraSettings` table with proper parameters:
  - `AeEnable` (boolean) - Auto Exposure
  - `AwbEnable` (boolean) - Auto White Balance
  - `ExposureTime` (integer, 100-3000000 μs)
  - `AnalogueGain` (float, 0.0-32.0)
  - `ExposureValue` (float, -10.0 to 10.0)
  - `RedGain` (float, 0.0-8.0)
  - `BlueGain` (float, 0.0-8.0)

#### `database_service.py`
- **Validation Engine**: Type and range validation for all parameters
- **API Methods**: `get_camera_settings()`, `update_parameter()`, `get_all_settings()`
- **Error Handling**: Comprehensive error messages and validation feedback

### 2. API Layer (`RaspberryPi/services/api_server.py`)

**RESTful Endpoints:**
- `GET /api/settings/camera` - Get current camera settings
- `GET /api/settings/<table_name>` - Get settings from any table
- `POST /api/settings/update` - Update a single parameter
- `GET /api/health` - Health check

**Validation Features:**
- Type checking (bool, int, float)
- Range validation
- Parameter existence verification
- Table existence verification

### 3. UI Layer (`DesktopApp/widgets/device_settings_widget/`)

#### `device_settings_widgets.py`
- **APIClientThread**: Non-blocking API calls
- **CameraSettingsWidget**: Full camera parameter control
- **SpectrometerSettingsWidget**: Placeholder for future implementation
- **FileSettingsWidget**: Placeholder for file saving settings
- **DeviceSettingsWidget**: Main tabbed container

## Key Features

### Smart Control Logic
- Auto exposure controls enable/disable manual exposure settings
- Auto white balance controls enable/disable manual gain settings
- Real-time parameter validation

### Minimal Hard-Coding
- Parameter validation rules defined in dictionaries
- API endpoints generated dynamically
- UI controls created from validation rules
- Extensible for future device types

### Error Handling
- Network timeout handling
- API error response handling
- User-friendly error messages
- Graceful degradation

## Usage

### Starting the API Server
```bash
cd RaspberryPi/services
python api_server.py
```

The server will start on `http://localhost:5000` with the following endpoints:
- Camera settings: `http://localhost:5000/api/settings/camera`
- Update parameter: `http://localhost:5000/api/settings/update`

### Using the UI
1. The device settings widget is integrated into the camera tab
2. Right column is split into:
   - **Upper part**: Basic camera controls (1/3 space)
   - **Lower part**: Tabbed device settings (2/3 space)
3. Tabs available:
   - **Camera**: Full camera parameter control
   - **Spectrometer**: Placeholder for future implementation
   - **File Settings**: Placeholder for file saving configuration

### API Usage Examples

**Get camera settings:**
```bash
curl -X GET http://localhost:5000/api/settings/camera
```

**Update a parameter:**
```bash
curl -X POST http://localhost:5000/api/settings/update \
     -H 'Content-Type: application/json' \
     -d '{"table_name":"CameraSettings","parameter":"ExposureTime","value":"15000"}'
```

## Validation Rules

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| AeEnable | boolean | N/A | Auto Exposure enable |
| AwbEnable | boolean | N/A | Auto White Balance enable |
| ExposureTime | integer | 100-3000000 | Exposure time in microseconds |
| AnalogueGain | float | 0.0-32.0 | Camera analog gain |
| ExposureValue | float | -10.0-10.0 | Exposure compensation |
| RedGain | float | 0.0-8.0 | Red channel gain |
| BlueGain | float | 0.0-8.0 | Blue channel gain |

## Extending the System

### Adding New Device Types
1. Add validation rules to `DATABASE_VALIDATION_RULES`
2. Create corresponding database table
3. Implement widget class following the pattern
4. Add tab to `DeviceSettingsWidget`

### Adding New Parameters
1. Update database schema
2. Add validation rules
3. Update UI controls in the widget
4. No API changes needed - it's dynamic!

## Dependencies

Added to `RaspberryPi/requirements.txt`:
- `flask==2.3.3` - Web framework
- `flask-cors==4.0.0` - Cross-origin requests
- `requests==2.31.0` - HTTP client for UI

## Design Principles

1. **Separation of Concerns**: Database, API, and UI layers are separate
2. **Validation at Source**: All validation happens in the database service
3. **Async Operations**: UI never blocks on API calls
4. **Extensibility**: Easy to add new devices and parameters
5. **Error Resilience**: Comprehensive error handling throughout
6. **Type Safety**: Strong typing with validation

This implementation provides a robust, scalable foundation for device configuration that follows modern software engineering practices.
