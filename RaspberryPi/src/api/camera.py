import base64
import json as _json
import os
import subprocess as _sp
import tempfile
from typing import Any, Dict, Optional, Union

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.api.common import APIResponse
from src.config.settings import config
from src.services.camera_service import camera_service
from src.services.database_service import db_service

router = APIRouter()


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


@router.get("/settings/camera", response_model=CameraSettingsResponse)
async def get_camera_settings():
    """Get current camera settings (slot 0)."""
    try:
        settings = db_service.get_camera_settings()
        if not settings:
            raise HTTPException(status_code=404, detail="No camera settings found")
        return CameraSettingsResponse(**settings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/settings/camera/slot/{slot_id}", response_model=CameraSettingsResponse)
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

        return CameraSettingsResponse(**settings)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/settings/camera/slots", response_model=Dict[str, Any])
async def get_all_camera_settings_slots():
    """Get all camera settings slots (0-9)."""
    try:
        slots = db_service.get_all_camera_settings_slots()
        return {"success": True, "data": slots}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/settings/camera/validation-rules")
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


@router.post("/settings/camera", response_model=APIResponse)
async def update_camera_settings(settings: CameraSettingsResponse):
    """Update all camera settings at once."""
    try:
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


@router.post("/settings/camera/save-slot/{slot_id}", response_model=APIResponse)
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


@router.post("/settings/camera/load-slot/{slot_id}", response_model=APIResponse)
async def load_camera_settings_from_slot(slot_id: int):
    """Load camera settings from a slot (1-10) into the current session (slot 0).

    This copies settings from the specified slot to slot 0 (current session)
    and restarts the camera to apply the settings immediately.

    Use this to load a saved preset and apply it to the camera.
    """
    try:
        if not 1 <= slot_id <= 10:
            raise HTTPException(status_code=400, detail="Slot ID must be between 1 and 10 (0 is current session)")

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


@router.post("/settings/camera/apply", response_model=APIResponse)
async def apply_camera_session_settings(settings: CameraSettingsResponse):
    """Apply camera settings to the camera without saving to database.

    This updates the camera's current operational parameters and restarts
    the camera stream to apply the new settings immediately. Settings are NOT
    persisted to the database - use /api/settings/camera/save-slot/{slot_id}
    to save settings to a slot.
    """
    try:
        settings_dict = settings.model_dump()
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


@router.get("/camera/awb-gains")
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


@router.post("/camera/photo")
async def capture_photo(output_path: Optional[str] = None):
    """Capture a high-quality photo with all camera settings (PhotoResolution, ExposureTime, etc.).

    Args:
        output_path: Optional path to save the photo. If not provided, returns base64-encoded image.

    Returns:
        JSON response with success status, image data (base64) or file path, and metadata.
    """
    try:
        success, result = camera_service.capture_photo(output_path=output_path)

        if not success:
            raise HTTPException(status_code=500, detail=f"Photo capture failed: {result}")

        if output_path:
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
            if isinstance(result, np.ndarray):
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
