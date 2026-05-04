# FastAPI Conversion Summary

## Overview

Successfully converted the Flask API to FastAPI with enhanced validation and database constraints. The system now provides better type safety, automatic documentation, and improved error handling.

## Key Changes Made

### 1. Database Schema with Constraints

**Updated `database_ini.py`:**
```sql
CREATE TABLE IF NOT EXISTS CameraSettings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    AeEnable INTEGER NOT NULL DEFAULT 1 CHECK(AeEnable IN (0, 1)),
    AwbEnable INTEGER NOT NULL DEFAULT 1 CHECK(AwbEnable IN (0, 1)),
    ExposureTime INTEGER NOT NULL DEFAULT 10000 CHECK(ExposureTime BETWEEN 100 AND 3000000),
    AnalogueGain REAL NOT NULL DEFAULT 1.0 CHECK(AnalogueGain BETWEEN 0.0 AND 32.0),
    ExposureValue REAL NOT NULL DEFAULT 0.0 CHECK(ExposureValue BETWEEN -10.0 AND 10.0),
    RedGain REAL NOT NULL DEFAULT 1.0 CHECK(RedGain BETWEEN 0.0 AND 8.0),
    BlueGain REAL NOT NULL DEFAULT 1.0 CHECK(BlueGain BETWEEN 0.0 AND 8.0)
)
```

**Database Constraints:**
- Boolean fields: `CHECK(field IN (0, 1))`
- Integer ranges: `CHECK(field BETWEEN min AND max)`
- Float ranges: `CHECK(field BETWEEN min AND max)`

### 2. FastAPI Server (`fastapi_server.py`)

**Pydantic Models with Validation:**
```python
class CameraSettingsResponse(BaseModel):
    AeEnable: bool = Field(default=True, description="Auto Exposure enabled")
    ExposureTime: int = Field(default=10000, ge=100, le=3000000, description="Exposure time in microseconds")
    AnalogueGain: float = Field(default=1.0, ge=0.0, le=32.0, description="Camera analog gain")
    # ... other fields with validation
```

**Enhanced Endpoints:**
- `GET /api/health` - Health check
- `GET /api/settings/camera` - Get camera settings (returns Pydantic model)
- `GET /api/settings/{table_name}` - Get settings from any table
- `POST /api/settings/update` - Update single parameter with validation
- `POST /api/settings/camera` - Update all camera settings at once
- `GET /api/settings/camera/validation-rules` - Get validation rules

**Validation Features:**
- Automatic type conversion (string to bool/int/float)
- Pydantic field validation with `ge`/`le` constraints
- Custom validators for table names and value conversion
- Detailed error messages for validation failures

### 3. Dependencies Updated

**requirements.txt changes:**
```
# Removed:
flask==2.3.3
flask-cors==4.0.0

# Added:
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
```

### 4. UI Client Updates

**Updated for FastAPI compatibility:**
- Changed API URL from `localhost:5000` to `localhost:8000`
- Enhanced error handling for FastAPI's 422 validation errors
- Support for both direct Pydantic responses and wrapped responses
- Better error message parsing

## API Usage Examples

### Get Camera Settings
```bash
curl -X GET http://localhost:8000/api/settings/camera
```
Returns:
```json
{
  "id": 1,
  "AeEnable": true,
  "AwbEnable": true,
  "ExposureTime": 10000,
  "AnalogueGain": 1.0,
  "ExposureValue": 0.0,
  "RedGain": 1.0,
  "BlueGain": 1.0
}
```

### Update Single Parameter
```bash
curl -X POST http://localhost:8000/api/settings/update \
     -H 'Content-Type: application/json' \
     -d '{"table_name":"CameraSettings","parameter":"ExposureTime","value":15000}'
```

### Update All Camera Settings
```bash
curl -X POST http://localhost:8000/api/settings/camera \
     -H 'Content-Type: application/json' \
     -d '{
       "AeEnable": true,
       "AwbEnable": true,
       "ExposureTime": 15000,
       "AnalogueGain": 1.5,
       "ExposureValue": 0.0,
       "RedGain": 1.2,
       "BlueGain": 1.1
     }'
```

### Get Validation Rules
```bash
curl -X GET http://localhost:8000/api/settings/camera/validation-rules
```

## FastAPI Advantages

### 1. **Automatic Documentation**
- Interactive API docs at `http://localhost:8000/docs`
- OpenAPI/Swagger specification automatically generated
- Schema validation documentation

### 2. **Enhanced Validation**
- Pydantic models provide automatic type checking
- Field-level validation with custom error messages
- Request/response validation

### 3. **Better Error Handling**
- Structured error responses with detail
- HTTP status code handling
- Validation error details (422 responses)

### 4. **Performance**
- ASGI support with Uvicorn
- Async request handling
- Better performance than Flask

### 5. **Type Safety**
- Full type hints throughout
- IDE autocompletion support
- Runtime type checking

## Running the Server

```bash
cd RaspberryPi/services
python fastapi_server.py
```

Or with uvicorn directly:
```bash
uvicorn fastapi_server:app --host 0.0.0.0 --port 8000 --reload
```

## Database Constraints Enforcement

The database now enforces constraints at the SQLite level:

```sql
-- These will fail:
INSERT INTO CameraSettings (ExposureTime) VALUES (50);  -- Below minimum
INSERT INTO CameraSettings (ExposureTime) VALUES (4000000);  -- Above maximum
INSERT INTO CameraSettings (AeEnable) VALUES (2);  -- Not 0 or 1
INSERT INTO CameraSettings (AnalogueGain) VALUES (-1.0);  -- Negative value
```

## Error Handling Improvements

### FastAPI Validation Errors (422)
```json
{
  "detail": [
    {
      "loc": ["body", "ExposureTime"],
      "msg": "ensure this value is greater than or equal to 100",
      "type": "value_error.number.not_ge",
      "ctx": {"limit_value": 100}
    }
  ]
}
```

### Database Constraint Violations
```json
{
  "success": false,
  "error": "Database error: CHECK constraint failed: CameraSettings.ExposureTime"
}
```

## Migration Notes

1. **Port Change**: API server now runs on port 8000 instead of 5000
2. **Response Format**: Some endpoints return direct Pydantic models instead of wrapped responses
3. **Error Format**: FastAPI uses structured error responses with `detail` field
4. **Validation**: Enhanced validation with automatic type conversion

## Future Enhancements

The FastAPI foundation enables easy addition of:
- Authentication middleware
- Rate limiting
- Request logging
- Background tasks for camera control
- WebSocket support for real-time updates
- Async database operations

This conversion provides a more robust, type-safe, and well-documented API foundation for the device settings system.
