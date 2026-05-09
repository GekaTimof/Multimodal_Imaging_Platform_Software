from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, Union
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from RaspberryPi.database_service import db_service

app = FastAPI(
    title="Device Settings API",
    description="API for managing camera and spectrometer settings",
    version="1.0.0"
)


# Pydantic Models for Request/Response
class CameraSettingsResponse(BaseModel):
    id: Optional[int] = None
    SettingsName: Optional[str] = Field(default="Basic", description="Settings profile name")
    PhotoResolution: str = Field(default="3280x2464", description="Photo resolution")
    VideoResolution: str = Field(default="1920x1080", description="Video resolution")
    AeEnable: bool = Field(default=True, description="Auto Exposure enabled")
    AwbEnable: bool = Field(default=True, description="Auto White Balance enabled")
    ExposureTime: int = Field(default=10000, ge=100, le=3000000, description="Exposure time in microseconds")
    AnalogueGain: float = Field(default=1.0, ge=0.0, le=32.0, description="Camera analog gain")
    ExposureValue: float = Field(default=0.0, ge=-10.0, le=10.0, description="Exposure compensation")
    RedGain: float = Field(default=1.0, ge=0.0, le=8.0, description="Red channel gain")
    BlueGain: float = Field(default=1.0, ge=0.0, le=8.0, description="Blue channel gain")

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


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None


# API Endpoints
@app.get("/api/health", response_model=Dict[str, str])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "FastAPI server is running"}


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
            ("CameraSettings", "AeEnable", int(settings.AeEnable)),
            ("CameraSettings", "AwbEnable", int(settings.AwbEnable)),
            ("CameraSettings", "ExposureTime", settings.ExposureTime),
            ("CameraSettings", "AnalogueGain", settings.AnalogueGain),
            ("CameraSettings", "ExposureValue", settings.ExposureValue),
            ("CameraSettings", "RedGain", settings.RedGain),
            ("CameraSettings", "BlueGain", settings.BlueGain),
        ]
        
        failed_updates = []
        for table_name, parameter, value in updates:
            success, message = db_service.update_parameter(table_name, parameter, value)
            if not success:
                failed_updates.append(f"{parameter}: {message}")
        
        if failed_updates:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to update some parameters: {'; '.join(failed_updates)}"
            )
        
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
    """Signal that camera settings need to be reloaded."""
    try:
        # For now, just return success - the actual reload will happen 
        # when the camera service is restarted or settings are reloaded
        return APIResponse(
            success=True,
            message="Camera reload signal sent. Restart camera service to apply new resolution.",
            data={"action": "restart_required"}
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error signaling camera reload: {str(e)}")


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return ErrorResponse(
        success=False,
        error=exc.detail,
        details={"status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return ErrorResponse(
        success=False,
        error="Internal server error",
        details={"exception": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    
    print("Starting Device Settings FastAPI Server...")
    print("Available endpoints:")
    print("  GET  /api/health - Health check")
    print("  GET  /api/settings/camera - Get camera settings")
    print("  GET  /api/settings/{table_name} - Get settings from any table")
    print("  POST /api/settings/update - Update a single parameter")
    print("  POST /api/settings/camera - Update all camera settings")
    print("  GET  /api/settings/camera/validation-rules - Get validation rules")
    print("\nExample usage:")
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
