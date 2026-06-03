import asyncio
import base64
import json as _json
import subprocess as _sp
import tempfile
import time
from datetime import datetime
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, Any, Union
import os
import logging
import numpy as np
import cv2

# Import config and services
from src.config.settings import config
from .database_service import db_service
from .camera_service import CameraService
from .light_switcher_service import light_switcher_service, SwitchState
from .spectrometer_service import SpectrometerService


# Setup logging
logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Device Settings API",
    description="API for managing camera, spectrometer and light switcher settings",
    version="1.0.0"
)

# Global service instances
camera_service = CameraService()
spectrometer_service = SpectrometerService()


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

    model_config = ConfigDict(json_schema_extra={
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
    })

    @field_validator('SettingsName', mode='before')
    @classmethod
    def convert_settings_name(cls, v):
        if isinstance(v, bool):
            return str(v).lower()
        return str(v) if v is not None else "Basic"

    @field_validator('PhotoResolution', 'VideoResolution', mode='before')
    @classmethod
    def convert_resolution(cls, v):
        if isinstance(v, bool):
            return str(v).lower()
        return str(v) if v is not None else "1920x1080"

    @field_validator('AeEnable', 'AwbEnable', mode='before')
    @classmethod
    def convert_boolean_input(cls, v):
        # Handle numpy.bool_ and other types on input
        if hasattr(v, 'item'):  # numpy scalar
            return bool(v.item())
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'on')
        return bool(v)

    @field_validator('AeEnable', 'AwbEnable')
    @classmethod
    def ensure_python_bool(cls, v):
        # Ensure output is always a Python bool, not numpy.bool_
        return bool(v)

    @field_validator('ExposureTime', mode='before')
    @classmethod
    def convert_exposure_time(cls, v):
        if isinstance(v, (str, bool)):
            return int(v) if v is not False else 0
        return int(v)

    @field_validator('AnalogueGain', 'ExposureValue', 'RedGain', 'BlueGain', mode='before')
    @classmethod
    def convert_float(cls, v):
        if isinstance(v, (str, bool)):
            return float(v) if v is not False else 0.0
        return float(v)


class ParameterUpdateRequest(BaseModel):
    table_name: str = Field(..., description="Name of the table to update")
    parameter: str = Field(..., description="Parameter name to update")
    value: Union[str, int, float, bool] = Field(..., description="New value for the parameter")

    @field_validator('table_name')
    @classmethod
    def validate_table_name(cls, v):
        allowed_tables = ['CameraSettings', 'SpectrometerSettings', 'PositionerSettings']
        if v not in allowed_tables:
            raise ValueError(f"Table name must be one of: {allowed_tables}")
        return v

    @field_validator('value', mode='before')
    @classmethod
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

    @field_validator('data', mode='before')
    @classmethod
    def convert_numpy_types(cls, v):
        """Convert numpy types to standard Python types for JSON serialization."""
        if v is None:
            return v
        
        def convert_value(val):
            if hasattr(val, 'item'):  # numpy scalar (bool_, int64, float64, etc.)
                return val.item()
            elif isinstance(val, dict):
                return {k: convert_value(vv) for k, vv in val.items()}
            elif isinstance(val, list):
                return [convert_value(item) for item in val]
            elif isinstance(val, tuple):
                return tuple(convert_value(item) for item in val)
            return val
        
        return convert_value(v)


class ErrorApiResponse(BaseModel):
    success: bool = False
    error: Union[str, Dict[str, Any]]
    details: Optional[Dict[str, Any]] = None


class LightSwitcherStatusResponse(BaseModel):
    connected: bool
    port: Optional[str] = None
    baudrate: int
    current_state: str
    arduino_responsive: bool


class LightSwitcherSwitchRequest(BaseModel):
    state: str = Field(..., description="Target state: 'state1' or 'state2'")

    @field_validator('state')
    @classmethod
    def validate_state(cls, v):
        allowed_states = ['state1', 'state2']
        if v not in allowed_states:
            raise ValueError(f"State must be one of: {allowed_states}")
        return v


class SpectrometerSettingsResponse(BaseModel):
    id: Optional[int] = Field(default=0, description="Settings slot ID")
    SettingsName: str = Field(default="Basic", description="Settings profile name")
    IntegralTime: int = Field(default=100, description="Integration time in milliseconds (1-99999)")
    UseDarkSpectrum: bool = Field(default=False, description="Use dark spectrum for correction")
    AutoDarkCorrection: bool = Field(default=True, description="Automatically apply dark correction")
    OverilluminationThreshold: int = Field(default=65535, description="Threshold for overillumination detection (0-65535)")
    LastUpdated: Optional[str] = Field(default=None, description="Last update timestamp")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": 0,
            "SettingsName": "Basic",
            "IntegralTime": 100,
            "UseDarkSpectrum": False,
            "AutoDarkCorrection": True,
            "OverilluminationThreshold": 65535,
            "LastUpdated": "2024-01-01T12:00:00"
        }
    })

    @field_validator('UseDarkSpectrum', 'AutoDarkCorrection', mode='before')
    @classmethod
    def convert_boolean_input(cls, v):
        if hasattr(v, 'item'):
            return bool(v.item())
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'on')
        return bool(v)

    @field_validator('IntegralTime', mode='before')
    @classmethod
    def convert_integral_time(cls, v):
        if isinstance(v, (str, bool)):
            return int(v) if v is not False else 0
        return int(v)


class SpectrometerInfoResponse(BaseModel):
    connected: bool = Field(..., description="Spectrometer hardware connection status")
    integral_time: int = Field(..., description="Current integration time")
    use_dark_spectrum: bool = Field(..., description="Dark spectrum usage enabled")
    dark_spectrum_loaded: bool = Field(..., description="Whether dark spectrum is loaded in memory")
    dark_spectrum_file_exists: bool = Field(..., description="Whether dark spectrum file exists")
    auto_dark_correction: bool = Field(..., description="Auto dark correction enabled")
    overillumination: bool = Field(..., description="Current overillumination status")
    overillumination_threshold: int = Field(..., description="Overillumination threshold")
    vendor: Optional[str] = Field(default=None, description="Spectrometer vendor")
    pn: Optional[str] = Field(default=None, description="Part number")
    sn: Optional[str] = Field(default=None, description="Serial number")
    module_version: Optional[str] = Field(default=None, description="Module firmware version")
    production_date: Optional[str] = Field(default=None, description="Production date")


class SpectrometerIntegralTimeRequest(BaseModel):
    integral_time: int = Field(..., description="Integration time in milliseconds (1-99999)", ge=1, le=99999)


class SpectrometerSpectrumResponse(BaseModel):
    timestamp: float = Field(..., description="Unix timestamp of the measurement")
    wavelength: list = Field(..., description="Wavelength array (nm)")
    spectrum: list = Field(..., description="Raw spectrum data")
    real_spectrum: list = Field(..., description="Dark-corrected spectrum data")
    overillumination: bool = Field(..., description="Overillumination flag")


class DarkSpectrumResponse(BaseModel):
    """Response model for dark spectrum data."""
    dark_spectrum: list = Field(..., description="Dark spectrum array")
    use_dark_spectrum: bool = Field(..., description="Whether dark spectrum is enabled")
    dark_spectrum_file_exists: bool = Field(..., description="Whether dark spectrum file exists")


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
            raise HTTPException(
                status_code=500,
                detail="Failed to connect to Arduino light switcher"
            )
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
    """Get camera settings for a specific slot (0-10).

    Slot 0: Current session (applied to camera, volatile)
    Slots 1-10: Saved presets (persistent)
    """
    try:
        if not 0 <= slot_id <= 10:
            raise HTTPException(status_code=400, detail="Slot ID must be between 0 and 10")

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
            data=settings.model_dump()
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
        "data": {
            "exposure_time_range": [config.MIN_EXPOSURE_TIME_US, config.MAX_EXPOSURE_TIME_US],
            "analog_gain_range": [config.MIN_ANALOG_GAIN, config.MAX_ANALOG_GAIN],
            "exposure_value_range": [config.MIN_EXPOSURE_VALUE, config.MAX_EXPOSURE_VALUE],
            "color_gain_range": [config.MIN_COLOR_GAIN, config.MAX_COLOR_GAIN],
            "available_resolutions": config.AVAILABLE_RESOLUTIONS
        }
    }


@app.post("/api/settings/camera/save-slot/{slot_id}", response_model=APIResponse)
async def save_camera_settings_to_slot(slot_id: int, settings: CameraSettingsResponse):
    """Save camera settings to a specific slot (0-10).

    Slot 0 is the current session (volatile, applied immediately to camera).
    Slots 1-10 are persistent saved presets.
    """
    try:
        if not 0 <= slot_id <= 10:
            raise HTTPException(status_code=400, detail="Slot ID must be between 0 and 10")

        success, message = db_service.save_camera_settings_to_slot(slot_id, settings.model_dump())

        if success:
            return APIResponse(
                success=True,
                message=f"Settings saved to slot {slot_id}",
                data={"slot_id": slot_id, "settings": settings.model_dump()}
            )
        else:
            raise HTTPException(status_code=400, detail=message)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post("/api/settings/camera/load-slot/{slot_id}", response_model=APIResponse)
async def load_camera_settings_from_slot(slot_id: int):
    """Load camera settings from a slot (1-10) into the current session (slot 0).

    This copies settings from the specified slot to slot 0 (current session)
    and restarts the camera to apply the settings immediately.

    Use this to load a saved preset and apply it to the camera.
    """
    try:
        if not 1 <= slot_id <= 10:
            raise HTTPException(status_code=400, detail="Slot ID must be between 1 and 10 (0 is current session)")

        # Copy settings from slot to session (slot 0)
        success, message, settings = db_service.copy_slot_to_session(slot_id)

        if not success:
            raise HTTPException(status_code=400, detail=message)

        return APIResponse(
            success=True,
            message=f"Settings loaded from slot {slot_id} to current session and applied to camera",
            data={"source_slot": slot_id, "settings": settings}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading slot to session: {str(e)}")



@app.post("/api/settings/camera/apply", response_model=APIResponse)
async def apply_camera_session_settings(settings: CameraSettingsResponse):
    """Apply camera settings to the camera without saving to database.

    This updates the camera's current operational parameters and restarts
    the camera stream to apply the new settings immediately. Settings are NOT
    persisted to the database - use /api/settings/camera/save-slot/{slot_id}
    to save settings to a slot.
    """
    try:
        # Convert settings to dictionary
        settings_dict = settings.model_dump()

        # Apply settings to camera without saving to database
        success = camera_service.apply_session_settings(settings_dict)

        if success:
            return APIResponse(
                success=True,
                message="Camera settings applied successfully (not saved to database).",
                data=settings_dict
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to apply camera settings")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error applying camera settings: {str(e)}")


@app.get("/api/camera/awb-gains")
async def get_current_awb_gains():
    """Read current ColourGains from camera using auto-AWB metadata.

    Useful for implementing a 'lock AWB' workflow: call this while AwbEnable=true
    to get the gains the camera chose, then store them as RedGain/BlueGain and
    switch to AwbEnable=false.
    """
    try:
        video_was_running = camera_service.running or camera_service._is_rpicam_vid_running()
        if video_was_running:
            camera_service._pause_video_stream()

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            tmp = f.name
        try:
            result = _sp.run(
                ['rpicam-still', '-n', '--width', '320', '--height', '240',
                 '--awb', 'auto', '--metadata', '-', '-o', tmp],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode != 0:
                raise HTTPException(status_code=500, detail="Failed to capture AWB frame")
            meta = _json.loads(result.stdout)
            gains = meta.get('ColourGains')
            if not gains or len(gains) < 2:
                raise HTTPException(status_code=500, detail="ColourGains not found in metadata")
            red_gain = round(float(gains[0]), 3)
            blue_gain = round(float(gains[1]), 3)
            return {"success": True, "data": {"red_gain": red_gain, "blue_gain": blue_gain}}
        finally:
            try:
                os.unlink(tmp)
            except Exception:
                pass
            if video_was_running:
                camera_service._resume_video_stream()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AWB gains error: {str(e)}")


@app.post("/api/camera/photo")
async def capture_photo(output_path: Optional[str] = None):
    """Capture a high-quality photo with all camera settings (PhotoResolution, ExposureTime, etc.).

    Args:
        output_path: Optional path to save the photo. If not provided, returns base64-encoded image.

    Returns:
        JSON response with success status, image data (base64) or file path, and metadata.
    """
    try:
        logger.info(f"Photo capture requested. output_path={output_path}, backend={camera_service.camera_backend}, use_real_camera={camera_service.use_real_camera}")
        logger.info(f"Current camera settings: photo_res={camera_service.photo_width}x{camera_service.photo_height}, "
                   f"exposure={camera_service.exposure_time}us, gain={camera_service.analogue_gain}, "
                   f"AE={camera_service.ae_enable}, AWB={camera_service.awb_enable}")

        # Capture photo
        success, result = camera_service.capture_photo(output_path=output_path)
        logger.info(f"Photo capture result: success={success}, result_type={type(result).__name__}")

        if not success:
            raise HTTPException(status_code=500, detail=f"Photo capture failed: {result}")

        if output_path:
            # Photo saved to file
            return APIResponse(
                success=True,
                message=f"Photo captured and saved to {output_path}",
                data={
                    "file_path": result,
                    "resolution": f"{camera_service.photo_width}x{camera_service.photo_height}",
                    "exposure_time_us": camera_service.exposure_time,
                    "analogue_gain": camera_service.analogue_gain,
                    "ae_enable": bool(camera_service.ae_enable),
                    "awb_enable": bool(camera_service.awb_enable)
                }
            )
        else:
            # Return as base64 encoded JPEG
            if isinstance(result, np.ndarray):
                # Encode numpy array to JPEG
                ret, jpeg_buffer = cv2.imencode('.jpg', result, [cv2.IMWRITE_JPEG_QUALITY, 95])
                if not ret:
                    raise HTTPException(status_code=500, detail="Failed to encode photo to JPEG")

                image_base64 = base64.b64encode(jpeg_buffer).decode('utf-8')

                return APIResponse(
                    success=True,
                    message="Photo captured successfully",
                    data={
                        "image_base64": image_base64,
                        "resolution": f"{camera_service.photo_width}x{camera_service.photo_height}",
                        "exposure_time_us": camera_service.exposure_time,
                        "analogue_gain": camera_service.analogue_gain,
                        "ae_enable": bool(camera_service.ae_enable),
                        "awb_enable": bool(camera_service.awb_enable),
                        "format": "jpeg",
                        "quality": 95
                    }
                )
            else:
                raise HTTPException(status_code=500, detail=f"Unexpected result type: {type(result)}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error capturing photo: {str(e)}")


# Spectrometer API Endpoints (FastAPI endpoints for DesktopApp integration)
# Additional streaming endpoints are served by SpectrumStreamServer (port 8081):
# SSE stream:          GET  /spectrum
# Single snapshot:     GET  /spectrum/single
# Info:                GET  /info
# Set integral time:   GET  /control/set_integral_time?time=N
# Set dark spectrum:   GET  /control/set_dark_spectrum
# Clear dark spectrum: GET  /control/clear_dark_spectrum

@app.get("/api/spectrometer/settings", response_model=SpectrometerSettingsResponse)
async def get_spectrometer_settings():
    """Get current spectrometer settings from database."""
    try:
        settings = db_service.get_spectrometer_settings()
        if not settings:
            raise HTTPException(status_code=404, detail="No spectrometer settings found")
        return SpectrometerSettingsResponse(**settings)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/api/spectrometer/settings", response_model=APIResponse)
async def update_spectrometer_settings(settings: SpectrometerSettingsResponse):
    """Update all spectrometer settings at once."""
    try:
        data = settings.model_dump()
        data['LastUpdated'] = datetime.now().isoformat()
        success, message = db_service.save_spectrometer_settings(data)
        if success:
            # Reload settings in the service
            spectrometer_service.reload_settings()
            return APIResponse(
                success=True,
                message="Spectrometer settings updated successfully",
                data=settings.model_dump()
            )
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating spectrometer settings: {str(e)}")


@app.get("/api/spectrometer/info", response_model=SpectrometerInfoResponse)
async def get_spectrometer_info():
    """Get spectrometer hardware information and status."""
    try:
        info = spectrometer_service.get_spectrometer_info()
        return SpectrometerInfoResponse(**info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting spectrometer info: {str(e)}")


@app.get("/api/spectrometer/spectrum", response_model=SpectrometerSpectrumResponse)
async def get_spectrometer_spectrum():
    """Get a single spectrum snapshot."""
    try:
        wavelength, spectrum, real_spectrum = spectrometer_service.get_spectrum_data()
        if wavelength is None or spectrum is None:
            raise HTTPException(status_code=503, detail="Spectrum data not available")

        response_data = {
            'timestamp': time.time(),
            'wavelength': wavelength.tolist() if wavelength is not None else [],
            'spectrum': spectrum.tolist() if spectrum is not None else [],
            'real_spectrum': real_spectrum.tolist() if real_spectrum is not None else [],
            'overillumination': bool(spectrometer_service.overillumination)
        }
        return SpectrometerSpectrumResponse(**response_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting spectrum: {str(e)}")


@app.post("/api/spectrometer/integral-time", response_model=APIResponse)
async def set_spectrometer_integral_time(request: SpectrometerIntegralTimeRequest):
    """Set spectrometer integration time."""
    try:
        success = spectrometer_service.set_integral_time(request.integral_time)
        if success:
            return APIResponse(
                success=True,
                message=f"Integration time set to {request.integral_time}ms",
                data={"integral_time": request.integral_time}
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to set integration time")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting integral time: {str(e)}")


@app.post("/api/spectrometer/dark-spectrum/capture", response_model=APIResponse)
async def capture_dark_spectrum():
    """Capture and save dark spectrum (ensure no light is entering the spectrometer).
    Saves to standard location and enables UseDarkSpectrum automatically."""
    try:
        success = spectrometer_service.set_dark_spectrum()
        if success:
            return APIResponse(
                success=True,
                message="Dark spectrum captured and saved successfully",
                data={
                    "dark_spectrum_loaded": spectrometer_service.dark_spectrum is not None,
                    "use_dark_spectrum": spectrometer_service.use_dark_spectrum
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to capture dark spectrum")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error capturing dark spectrum: {str(e)}")


@app.post("/api/spectrometer/dark-spectrum/clear", response_model=APIResponse)
async def clear_dark_spectrum():
    """Clear the current dark spectrum. Deletes the file and disables UseDarkSpectrum."""
    try:
        spectrometer_service.clear_dark_spectrum()
        return APIResponse(
            success=True,
            message="Dark spectrum cleared successfully",
            data={
                "dark_spectrum_loaded": False,
                "use_dark_spectrum": False
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing dark spectrum: {str(e)}")


@app.post("/api/spectrometer/dark-spectrum/load", response_model=APIResponse)
async def load_dark_spectrum():
    """Load dark spectrum from standard file location.
    Enables UseDarkSpectrum if file exists."""
    try:
        success = spectrometer_service.load_dark_spectrum_file()
        if success:
            return APIResponse(
                success=True,
                message="Dark spectrum loaded from standard location",
                data={
                    "dark_spectrum_loaded": spectrometer_service.dark_spectrum is not None,
                    "use_dark_spectrum": spectrometer_service.use_dark_spectrum
                }
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to load dark spectrum from standard location")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading dark spectrum: {str(e)}")


@app.post("/api/spectrometer/reconnect", response_model=APIResponse)
async def reconnect_spectrometer():
    """Reinitialize spectrometer connection (useful after hot-plug or startup failure)."""
    try:
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(None, spectrometer_service.reinitialize)
        info = spectrometer_service.get_spectrometer_info()
        if success:
            return APIResponse(
                success=True,
                message="Spectrometer reinitialized successfully",
                data=info
            )
        else:
            return APIResponse(
                success=False,
                message="Spectrometer not found or failed to initialize",
                data=info
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reinitializing spectrometer: {str(e)}")


@app.get("/api/spectrometer/dark-spectrum", response_model=DarkSpectrumResponse)
async def get_dark_spectrum():
    """Get the current dark spectrum data.
    Returns the stored dark spectrum array if available."""
    try:
        dark_spectrum, use_dark = spectrometer_service.get_dark_spectrum_data()
        dark_file_exists = os.path.exists(config.get_dark_spectrum_path())

        response_data = {
            'dark_spectrum': dark_spectrum.tolist() if dark_spectrum is not None else [],
            'use_dark_spectrum': use_dark,
            'dark_spectrum_file_exists': dark_file_exists
        }
        return DarkSpectrumResponse(**response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dark spectrum: {str(e)}")


@app.get("/api/spectrometer/validation-rules")
async def get_spectrometer_validation_rules():
    """Get validation rules for spectrometer parameters."""
    return {
        "success": True,
        "data": {
            "integral_time_range": [config.MIN_INTEGRAL_TIME, config.MAX_INTEGRAL_TIME],
            "overillumination_threshold_range": [config.MIN_OVERILLUMINATION_THRESHOLD, config.MAX_OVERILLUMINATION_THRESHOLD]
        }
    }


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorApiResponse(
            success=False,
            error=exc.detail,
            details={"status_code": exc.status_code}
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content=ErrorApiResponse(
            success=False,
            error="Internal server error",
            details={"exception": str(exc)}
        ).model_dump()
    )


if __name__ == "__main__":
    logger.info(f"Starting Device Settings FastAPI Server on {config.API_HOST}:{config.API_PORT}...")
    logger.info(f"Database path: {config.get_database_path()}")
    logger.info("Available endpoints:")
    logger.info("  GET  /api/health - Health check")
    logger.info("  Light Switcher:")
    logger.info("    GET  /api/light-switcher/status - Get connection status")
    logger.info("    POST /api/light-switcher/connect - Connect to Arduino")
    logger.info("    POST /api/light-switcher/switch - Switch to state1/state2")
    logger.info("    POST /api/light-switcher/disconnect - Disconnect from Arduino")
    logger.info("  Camera:")
    logger.info("    GET  /api/settings/camera - Get camera settings")
    logger.info("    GET  /api/settings/{table_name} - Get settings from any table")
    logger.info("    POST /api/settings/update - Update a single parameter")
    logger.info("    POST /api/settings/camera - Update all camera settings (saves to DB slot 0)")
    logger.info("    POST /api/settings/camera/apply - Apply settings to camera (no DB save)")
    logger.info("    POST /api/settings/camera/save-slot/{slot_id} - Save settings to slot")
    logger.info("    GET  /api/settings/camera/validation-rules - Get validation rules")
    logger.info("    POST /api/camera/photo - Capture high-quality photo with all settings")
    logger.info("  Spectrometer (Streaming on port %s):", config.SPECTRUM_STREAM_PORT)
    logger.info("    GET  /api/spectrometer/settings - Get spectrometer settings")
    logger.info("    POST /api/spectrometer/settings - Update spectrometer settings")
    logger.info("    GET  /api/spectrometer/info - Get spectrometer hardware info")
    logger.info("    GET  /api/spectrometer/spectrum - Get single spectrum snapshot")
    logger.info("    POST /api/spectrometer/integral-time - Set integration time")
    logger.info("    POST /api/spectrometer/dark-spectrum/capture - Capture dark spectrum")
    logger.info("    POST /api/spectrometer/dark-spectrum/clear - Clear dark spectrum")
    logger.info("    POST /api/spectrometer/dark-spectrum/load - Load dark spectrum from standard location")
    logger.info("    GET  /api/spectrometer/dark-spectrum - Get dark spectrum data")
    logger.info("    GET  /api/spectrometer/validation-rules - Get validation rules")
    logger.info("  Spectrometer Streaming (port %s):", config.SPECTRUM_STREAM_PORT)
    logger.info("    GET  /spectrum - SSE stream of spectrum data")
    logger.info("    GET  /spectrum/single - Single spectrum snapshot")
    logger.info("    GET  /info - Spectrometer info")
    logger.info("    GET  /control/set_integral_time?time=N - Set integral time")
    logger.info("    GET  /control/set_dark_spectrum - Capture dark spectrum")
    logger.info("    GET  /control/clear_dark_spectrum - Clear dark spectrum")

    uvicorn.run(
        app,
        host=config.API_HOST,
        port=config.API_PORT,
        reload=False,
        log_level=config.LOG_LEVEL.lower()
    )
