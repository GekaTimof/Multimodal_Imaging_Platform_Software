import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional, Union

import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.api.camera import router as camera_router
from src.api.common import APIResponse, ErrorApiResponse
from src.api.light_switcher import router as light_switcher_router
from src.api.positioner import router as positioner_router
from src.api.settings import router as settings_router
from src.config.settings import config
from src.services.database_service import db_service
from src.services.spectrometer_service import SpectrometerService

logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Device Settings API",
    description="API for managing camera, spectrometer and light switcher settings",
    version="1.0.0"
)

# Device routers (camera, positioner, light switcher, generic settings).
# Spectrometer endpoints are kept here so the spectrometer service code is not
# modified as requested.
app.include_router(camera_router, prefix="/api")
app.include_router(light_switcher_router, prefix="/api")
app.include_router(positioner_router, prefix="/api")
app.include_router(settings_router, prefix="/api")

# Spectrometer service instance - kept in this file to avoid changes to the
# spectrometer service module.
spectrometer_service = SpectrometerService()


# ---------------------------------------------------------------------------
# Shared / health endpoint
# ---------------------------------------------------------------------------

@app.get("/api/health", response_model=Dict[str, str])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "FastAPI server is running"}


# ---------------------------------------------------------------------------
# Spectrometer Pydantic models
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Spectrometer API endpoints
# ---------------------------------------------------------------------------

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
        raise HTTPException(status_code=500, detail=f"Error setting integration time: {str(e)}")


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
        import asyncio
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
        dark_file_exists = __import__('os').path.exists(config.get_dark_spectrum_path())

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
            "overillumination_threshold_range": [
                config.MIN_OVERILLUMINATION_THRESHOLD,
                config.MAX_OVERILLUMINATION_THRESHOLD
            ]
        }
    }


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

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
