# Multimodal Imaging Platform - Architecture

## Overview

The platform is divided into two main components that communicate via API:

### DesktopApp (Computer)
- **Purpose**: User interface and control panel
- **Location**: Runs on user's computer
- **Responsibilities**:
  - PyQt5 GUI for camera controls
  - Video streaming display
  - Settings management interface
  - Image capture and saving
  - API client for Raspberry Pi communication

### RaspberryPi (Raspberry Pi 5)
- **Purpose**: Hardware control and data processing
- **Location**: Runs on Raspberry Pi 5
- **Responsibilities**:
  - Camera hardware control
  - Spectrometer control
  - Database management (single source of truth)
  - FastAPI server for remote control
  - Video streaming server

## Database Architecture

### Single Database Principle
- **Only one database exists**: `/RaspberryPi/DevicesSettings.db`
- **Location**: Exclusively on Raspberry Pi
- **Access**: Through FastAPI endpoints only

### Database Tables
- `CameraSettings`: Camera parameters and configurations
- `SpectrometerSettings`: Spectrometer parameters
- `PositionerSettings`: Positioner device settings

## API Communication

### Base URL
```
http://10.43.70.189:8000/api
```

### Key Endpoints

#### Camera Settings
- `GET /api/settings/camera` - Get current camera settings (slot 0)
- `GET /api/settings/camera/slot/{slot_id}` - Get settings for specific slot (0-9)
- `GET /api/settings/camera/slots` - Get all camera settings slots
- `POST /api/settings/update` - Update single parameter
- `POST /api/settings/camera` - Update all camera settings
- `POST /api/settings/camera/save-slot/{slot_id}` - Save settings to slot
- `GET /api/settings/camera/validation-rules` - Get parameter validation rules

#### General Settings
- `GET /api/settings/{table_name}` - Get settings from any table
- `GET /api/health` - Health check

## Code Organization

### DesktopApp Structure
```
DesktopApp/
├── widgets/
│   └── device_settings_widget/
│       └── device_settings_widgets.py  # UI components, API client
├── threads/
│   ├── camera_thread.py               # Camera streaming, API client
│   └── simple_camera_thread.py       # Simple camera implementation
├── tabs/
│   └── camera_tab.py                 # Main camera interface
└── services/
    └── save_photo.py                 # Photo saving utility
```

### RaspberryPi Structure
```
RaspberryPi/
├── database_service.py               # Database operations (ONLY DB HERE)
├── services/
│   ├── fastapi_server.py            # API endpoints
│   ├── camera_service.py            # Camera hardware control
│   └── database_ini.py             # Database initialization
├── streaming.py                     # Video streaming
└── DevicesSettings.db               # SINGLE DATABASE FILE
```

## Separation Rules

### DesktopApp MUST NOT:
- Access database files directly
- Import from RaspberryPi modules
- Have local database instances
- Control hardware directly

### RaspberryPi MUST:
- Host the single database
- Provide complete API for all operations
- Handle all hardware interactions
- Validate all parameters and operations

### API Communication Rules:
- All settings changes go through API
- DesktopApp is API client only
- RaspberryPi is API server only
- No direct database access from DesktopApp

## Testing Strategy

### Valid Tests:
- Unit tests for individual components
- API integration tests
- UI component tests
- Mock API responses for testing

### Invalid Tests (Removed):
- Tests mixing DesktopApp and RaspberryPi code
- Direct database access from DesktopApp tests
- Tests violating separation principles

## Deployment

### DesktopApp Deployment:
1. Install on user's computer
2. Configure Raspberry Pi IP address
3. Run PyQt5 application

### RaspberryPi Deployment:
1. Deploy to Raspberry Pi 5
2. Start FastAPI server
3. Initialize database if needed
4. Start camera and streaming services

## Configuration

### DesktopApp Configuration:
- Raspberry Pi IP address in API calls
- Camera stream URL
- Save directories

### RaspberryPi Configuration:
- Database file location
- Camera hardware settings
- API server port

## Benefits of This Architecture

1. **Clear Separation**: Desktop and hardware concerns are completely separated
2. **Single Source of Truth**: Only one database eliminates synchronization issues
3. **Scalability**: Multiple DesktopApps can connect to one RaspberryPi
4. **Maintainability**: Changes to hardware don't affect UI code
5. **Testability**: Each component can be tested independently
6. **Remote Access**: API enables remote control capabilities

## Migration Notes

- Removed duplicate database from project root
- Deleted tests violating separation principles
- Ensured all DesktopApp database access goes through API
- Verified API provides complete functionality for all operations
