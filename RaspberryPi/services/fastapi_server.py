from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, Union
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Always import from the correct RaspberryPi directory
raspberry_pi_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if raspberry_pi_dir not in sys.path:
    sys.path.insert(0, raspberry_pi_dir)

from database_service import db_service
from services.camera_service import CameraService
from services.light_switcher_service import light_switcher_service, SwitchState

app = FastAPI(
    title="Device Settings API",
    description="API for managing camera, spectrometer and light switcher settings",
    version="1.0.0"
)

# Global camera service instance
camera_service = CameraService()


# Pydantic Models for Request/Response
class CameraSettingsResponse(BaseModel):
    id: Optional[int] = None
    SettingsName: Optional[Union[str, bool]] = Field(default="Basic", description="Settings profile name")
    PhotoResolution: Union[str, bool] = Field(default="3280x2464", description="Photo resolution")
    VideoResolution: Union[str, bool] = Field(default="1920x1080", description="Video resolution")
    AeEnable: Union[bool, str, int] = Field(default=True, description="Auto Exposure enabled")
    AwbEnable: Union[bool, str, int] = Field(default=True, description="Auto White Balance enabled")
    ExposureTime: Union[int, str] = Field(default=10000, description="Exposure time in microseconds")
    AnalogueGain: Union[float, str, int] = Field(default=1.0, description="Camera analog gain")
    ExposureValue: Union[float, str, int] = Field(default=0.0, description="Exposure compensation")
    RedGain: Union[float, str, int] = Field(default=1.0, description="Red channel gain")
    BlueGain: Union[float, str, int] = Field(default=1.0, description="Blue channel gain")

    @validator('SettingsName', pre=True)
    def convert_settings_name(cls, v):
        if isinstance(v, bool):
            return str(v).lower()
        return str(v) if v is not None else "Basic"

    @validator('PhotoResolution', 'VideoResolution', pre=True)
    def convert_resolution(cls, v):
        if isinstance(v, bool):
            return str(v).lower()
        return str(v) if v is not None else "1920x1080"

    @validator('AeEnable', 'AwbEnable', pre=True)
    def convert_boolean(cls, v):
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'on')
        elif isinstance(v, int):
            return bool(v)
        return bool(v)

    @validator('ExposureTime', pre=True)
    def convert_exposure_time(cls, v):
        if isinstance(v, (str, bool)):
            return int(v) if v != False else 0
        return int(v)

    @validator('AnalogueGain', 'ExposureValue', 'RedGain', 'BlueGain', pre=True)
    def convert_float(cls, v):
        if isinstance(v, (str, bool)):
            return float(v) if v != False else 0.0
        return float(v)

    class Config:
        schema_extra = {
            "example": {
                "SettingsName": "Basic",
                "PhotoResolution": "3280x2464",
                "VideoResolution": "1920x1080",
                "AeEnable": True,
                "AwbEnable": True,
                "ExposureTime": 10000,
                "AnalogueGain": 1.0,
                "ExposureValue": 0.0,
                "RedGain": 1.0,
                "BlueGain": 1.0
            }
        }


class ParameterUpdateRequest(BaseModel):
    table_name: str = Field(..., description="Name of the table to update")
    parameter: str = Field(..., description="Parameter name to update")
    value: Union[str, int, float, bool] = Field(..., description="New value for the parameter")

    @validator('table_name')
    def validate_table_name(cls, v):
        allowed_tables = ['CameraSettings', 'SpectrometerSettings', 'PositionerSettings']
        if v not in allowed_tables:
            raise ValueError(f"Table name must be one of: {allowed_tables}")
        return v

    @validator('value', pre=True)
    def convert_value(cls, v):
        """Convert string values to appropriate types"""
        if isinstance(v, str):
            # Try to convert to boolean first
            if v.lower() in ('true', '1', 'on'):
                return True
            elif v.lower() in ('false', '0', 'off'):
                return False
            # Try to convert to int
            try:
                return int(v)
            except ValueError:
                pass
            # Try to convert to float
            try:
                return float(v)
            except ValueError:
                pass
        return v


class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorApiResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None


class LightSwitcherStatusResponse(BaseModel):
    connected: bool
    port: str
    baudrate: int
    current_state: str
    arduino_responsive: bool


class LightSwitcherSwitchRequest(BaseModel):
    state: str = Field(..., description="Target state: 'state1' or 'state2'")

    @validator('state')
    def validate_state(cls, v):
        allowed_states = ['state1', 'state2']
        if v not in allowed_states:
            raise ValueError(f"State must be one of: {allowed_states}")
        return v


# API Endpoints
@app.get("/api/health", response_model=Dict[str, str])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "FastAPI server is running"}


# Light Switcher API Endpoints
@app.get("/api/light-switcher/status", response_model=LightSwitcherStatusResponse)
async def get_light_switcher_status():
    """Get light switcher connection and status information."""
    try:
        status = light_switcher_service.get_status()
        return LightSwitcherStatusResponse(**status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting light switcher status: {str(e)}")


@app.post("/api/light-switcher/connect", response_model=APIResponse)
async def connect_light_switcher():
    """Connect to Arduino light switcher."""
    try:
        success = light_switcher_service.connect()
        if success:
            return APIResponse(
                success=True,
                message="Successfully connected to Arduino light switcher",
                data=light_switcher_service.get_status()
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to connect to Arduino light switcher")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to light switcher: {str(e)}")


@app.post("/api/light-switcher/switch", response_model=APIResponse)
async def switch_light_switcher(request: LightSwitcherSwitchRequest):
    """Switch light switcher to specified state."""
    try:
        if request.state == "state1":
            success, message = light_switcher_service.switch_to_state_1()
        elif request.state == "state2":
            success, message = light_switcher_service.switch_to_state_2()
        else:
            raise HTTPException(status_code=400, detail="Invalid state specified")
        
        if success:
            return APIResponse(
                success=True,
                message=message,
                data={
                    "target_state": request.state,
                    "current_state": light_switcher_service.current_state.value,
                    "status": light_switcher_service.get_status()
                }
            )
        else:
            raise HTTPException(status_code=500, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error switching light switcher: {str(e)}")


@app.post("/api/light-switcher/disconnect", response_model=APIResponse)
async def disconnect_light_switcher():
    """Disconnect from Arduino light switcher."""
    try:
        light_switcher_service.disconnect()
        return APIResponse(
            success=True,
            message="Successfully disconnected from Arduino light switcher"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error disconnecting light switcher: {str(e)}")


@app.get("/api/settings/camera", response_model=CameraSettingsResponse)
async def get_camera_settings():
    """Get current camera settings (slot 0)."""
    try:
        settings = db_service.get_camera_settings()
        if not settings:
            raise HTTPException(status_code=404, detail="No camera settings found")
        
        # Convert database values to proper types
        return CameraSettingsResponse(**settings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/settings/camera/slot/{slot_id}", response_model=CameraSettingsResponse)
async def get_camera_settings_by_slot(slot_id: int):
    """Get camera settings for a specific slot (0-9)."""
    try:
        if not 0 <= slot_id <= 9:
            raise HTTPException(status_code=400, detail="Slot ID must be between 0 and 9")
        
        settings = db_service.get_camera_settings_by_slot(slot_id)
        if not settings:
            raise HTTPException(status_code=404, detail=f"No camera settings found for slot {slot_id}")
        
        # Convert database values to proper types
        return CameraSettingsResponse(**settings)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/settings/camera/slots", response_model=Dict[str, Any])
async def get_all_camera_settings_slots():
    """Get all camera settings slots (0-9)."""
    try:
        slots = db_service.get_all_camera_settings_slots()
        return {"success": True, "data": slots}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/settings/{table_name}", response_model=Dict[str, Any])
async def get_settings(table_name: str):
    """Get all settings from the specified table."""
    try:
        settings = db_service.get_all_settings(table_name)
        if not settings:
            raise HTTPException(status_code=404, detail=f"No settings found for table: {table_name}")
        
        return {"success": True, "data": settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/api/settings/update", response_model=APIResponse)
async def update_parameter(request: ParameterUpdateRequest):
    """Update a single parameter in the specified table."""
    try:
        success, message = db_service.update_parameter(
            request.table_name, 
            request.parameter, 
            request.value
        )
        
        if success:
            # Check if camera resolution parameter was updated and reload camera if needed
            if (request.table_name == "CameraSettings" and 
                request.parameter in ["PhotoResolution", "VideoResolution"]):
                try:
                    camera_service.reload_settings()
                    message += " Camera reinitialized with new resolution."
                except Exception as reload_error:
                    message += f" Warning: Camera reload failed: {reload_error}"
            
            return APIResponse(
                success=True, 
                message=message,
                data={"table": request.table_name, "parameter": request.parameter, "value": request.value}
            )
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post("/api/settings/camera", response_model=APIResponse)
async def update_camera_settings(settings: CameraSettingsResponse):
    """Update all camera settings at once."""
    try:
        # Update all parameters sequentially
        updates = [
            ("CameraSettings", "SettingsName", settings.SettingsName),
            ("CameraSettings", "PhotoResolution", settings.PhotoResolution),
            ("CameraSettings", "VideoResolution", settings.VideoResolution),
            ("CameraSettings", "AeEnable", int(settings.AeEnable)),
            ("CameraSettings", "AwbEnable", int(settings.AwbEnable)),
            ("CameraSettings", "ExposureTime", settings.ExposureTime),
            ("CameraSettings", "AnalogueGain", settings.AnalogueGain),
            ("CameraSettings", "ExposureValue", settings.ExposureValue),
            ("CameraSettings", "RedGain", settings.RedGain),
            ("CameraSettings", "BlueGain", settings.BlueGain),
        ]
        
        failed_updates = []
        resolution_updated = False
        
        for table_name, parameter, value in updates:
            success, message = db_service.update_parameter(table_name, parameter, value)
            if not success:
                failed_updates.append(f"{parameter}: {message}")
            elif parameter in ["PhotoResolution", "VideoResolution"]:
                resolution_updated = True
        
        if failed_updates:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to update some parameters: {'; '.join(failed_updates)}"
            )
        
        # Reload camera if resolution was updated
        if resolution_updated:
            try:
                camera_service.reload_settings()
                return APIResponse(
                    success=True,
                    message="All camera settings updated successfully. Camera reinitialized with new resolution.",
                    data=settings.dict()
                )
            except Exception as reload_error:
                return APIResponse(
                    success=True,
                    message=f"All camera settings updated but camera reload failed: {reload_error}",
                    data=settings.dict()
                )
        else:
            return APIResponse(
                success=True,
                message="All camera settings updated successfully",
                data=settings.dict()
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.get("/api/settings/camera/validation-rules")
async def get_camera_validation_rules():
    """Get validation rules for camera parameters."""
    return {
        "success": True,
        "data": db_service.CAMERA_VALIDATION_RULES
    }


@app.post("/api/settings/camera/save-slot/{slot_id}", response_model=APIResponse)
async def save_camera_settings_to_slot(slot_id: int, settings: CameraSettingsResponse):
    """Save camera settings to a specific slot (0-9)."""
    try:
        if not 0 <= slot_id <= 9:
            raise HTTPException(status_code=400, detail="Slot ID must be between 0 and 9")
        
        success, message = db_service.save_camera_settings_to_slot(slot_id, settings.dict())
        
        if success:
            return APIResponse(
                success=True,
                message=f"Settings saved to slot {slot_id}",
                data={"slot_id": slot_id, "settings": settings.dict()}
            )
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post("/api/settings/camera/reload", response_model=APIResponse)
async def reload_camera_settings():
    """Reload camera settings and reinitialize camera if resolution changed."""
    try:
        # Reload settings from database and reinitialize camera if needed
        camera_service.reload_settings()
        
        return APIResponse(
            success=True,
            message="Camera settings reloaded successfully. Camera reinitialized if resolution changed.",
            data={"action": "reloaded"}
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reloading camera settings: {str(e)}")


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorApiResponse(
            success=False,
            error=exc.detail,
            details={"status_code": exc.status_code}
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content=ErrorApiResponse(
            success=False,
            error="Internal server error",
            details={"exception": str(exc)}
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    
    print("Starting Device Settings FastAPI Server...")
    print("Available endpoints:")
    print("  GET  /api/health - Health check")
    print("  Light Switcher:")
    print("    GET  /api/light-switcher/status - Get connection status")
    print("    POST /api/light-switcher/connect - Connect to Arduino")
    print("    POST /api/light-switcher/switch - Switch to state1/state2")
    print("    POST /api/light-switcher/disconnect - Disconnect from Arduino")
    print("  Camera:")
    print("    GET  /api/settings/camera - Get camera settings")
    print("    GET  /api/settings/{table_name} - Get settings from any table")
    print("    POST /api/settings/update - Update a single parameter")
    print("    POST /api/settings/camera - Update all camera settings")
    print("    GET  /api/settings/camera/validation-rules - Get validation rules")
    print("\nExample usage:")
    print("  curl -X GET http://localhost:8000/api/light-switcher/status")
    print("  curl -X POST http://localhost:8000/api/light-switcher/connect")
    print("  curl -X POST http://localhost:8000/api/light-switcher/switch \\")
    print("       -H 'Content-Type: application/json' \\")
    print("       -d '{\"state\":\"state1\"}'")
    print("  curl -X GET http://localhost:8000/api/settings/camera")
    print("  curl -X POST http://localhost:8000/api/settings/update \\")
    print("       -H 'Content-Type: application/json' \\")
    print("       -d '{\"table_name\":\"CameraSettings\",\"parameter\":\"ExposureTime\",\"value\":15000}'")
    print("  curl -X POST http://localhost:8000/api/settings/camera \\")
    print("       -H 'Content-Type: application/json' \\")
    print("       -d '{\"AeEnable\":true,\"AwbEnable\":true,\"ExposureTime\":15000,\"AnalogueGain\":1.5,\"ExposureValue\":0.0,\"RedGain\":1.2,\"BlueGain\":1.1}'")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
