import asyncio
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from src.api.common import APIResponse
from src.services.positioner_service import positioner_service

router = APIRouter()


class PositionerSettingsResponse(BaseModel):
    id: Optional[int] = 0
    SettingsName: str = "Basic"
    XPosition: float = Field(default=0.0, ge=-5000.0, le=15000.0)
    YPosition: float = Field(default=0.0, ge=-5000.0, le=15000.0)
    ZPosition: float = Field(default=0.0, ge=-5000.0, le=15000.0)
    MovementSpeed: float = Field(default=2000.0, ge=1.0, le=10000.0)
    Acceleration: float = Field(default=100.0, ge=0.1, le=1000.0)
    XMin: float = Field(default=0.0)
    XMax: float = Field(default=0.0)
    YMin: float = Field(default=0.0)
    YMax: float = Field(default=0.0)
    ZMin: float = Field(default=0.0)
    ZMax: float = Field(default=0.0)
    XHomeAtMin: int = Field(default=1)
    YHomeAtMin: int = Field(default=1)
    ZHomeAtMin: int = Field(default=1)


class PositionerSettingsUpdate(BaseModel):
    model_config = {"extra": "forbid"}

    SettingsName: str = "Basic"
    MovementSpeed: float = Field(default=2000.0, ge=1.0, le=10000.0)
    Acceleration: float = Field(default=100.0, ge=0.1, le=1000.0)


class PositionerMoveRequest(BaseModel):
    x: float = Field(..., ge=-5000.0, le=15000.0)
    y: float = Field(..., ge=-5000.0, le=15000.0)
    z: float = Field(..., ge=-5000.0, le=15000.0)
    speed: Optional[float] = Field(default=None, ge=1.0, le=10000.0)


class PositionerAxisRequest(BaseModel):
    axis: str = Field(..., pattern=r"^[xXyYzZ]$")


class PositionerCalibrateResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


@router.get("/positioner/settings", response_model=PositionerSettingsResponse)
async def get_positioner_settings():
    from src.services.database_service import db_service
    return PositionerSettingsResponse(**db_service.get_positioner_settings())


@router.get("/positioner/settings/slots", response_model=APIResponse)
async def get_all_positioner_settings_slots():
    from src.services.database_service import db_service
    try:
        slots = db_service.get_all_positioner_settings_slots()
        return APIResponse(
            success=True,
            message="Positioner settings slots received",
            data={str(slot_id): settings for slot_id, settings in slots.items()},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@router.get("/positioner/settings/{slot_id}", response_model=PositionerSettingsResponse)
async def get_positioner_settings_by_slot(slot_id: int):
    from src.services.database_service import db_service
    if not 0 <= slot_id <= 10:
        raise HTTPException(status_code=400, detail="Slot ID must be between 0 and 10")
    try:
        settings = db_service.get_positioner_settings_by_slot(slot_id)
        if not settings:
            raise HTTPException(status_code=404, detail=f"No positioner settings found for slot {slot_id}")
        return PositionerSettingsResponse(**settings)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@router.post("/positioner/settings", response_model=APIResponse)
async def update_positioner_settings(settings: PositionerSettingsUpdate):
    try:
        data = await asyncio.to_thread(positioner_service.apply_settings, settings.model_dump())
        return APIResponse(success=True, message="Positioner settings applied", data=data)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/positioner/settings/{slot_id}", response_model=APIResponse)
async def save_positioner_settings_to_slot(slot_id: int, settings: PositionerSettingsUpdate):
    from src.services.database_service import db_service
    if not 0 <= slot_id <= 10:
        raise HTTPException(status_code=400, detail="Slot ID must be between 0 and 10")
    try:
        success, message = await asyncio.to_thread(
            db_service.save_positioner_settings_to_slot, slot_id, settings.model_dump()
        )
        if success:
            return APIResponse(success=True, message=message)
        raise HTTPException(status_code=400, detail=message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@router.post("/positioner/settings/load/{slot_id}", response_model=APIResponse)
async def load_positioner_settings_from_slot(slot_id: int):
    from src.services.database_service import db_service
    if not 1 <= slot_id <= 10:
        raise HTTPException(status_code=400, detail="Slot ID must be between 1 and 10")
    try:
        success, message, settings = await asyncio.to_thread(
            db_service.copy_positioner_slot_to_session, slot_id
        )
        if success:
            return APIResponse(success=True, message=message, data=settings)
        raise HTTPException(status_code=400, detail=message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@router.get("/positioner/limits", response_model=APIResponse)
async def get_positioner_limits():
    try:
        limits = await asyncio.to_thread(positioner_service.get_axis_limits)
        return APIResponse(success=True, message="Positioner axis limits", data=limits)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting positioner limits: {e}")


@router.get("/positioner/status", response_model=APIResponse)
async def get_positioner_status():
    try:
        status = await asyncio.to_thread(positioner_service.refresh_status)
        return APIResponse(success=True, message="Positioner status received", data=status)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/positioner/connect", response_model=APIResponse)
async def connect_positioner():
    connected = await asyncio.to_thread(positioner_service.connect)
    if not connected:
        raise HTTPException(status_code=503, detail=f"Positioner not available on {positioner_service.port}")
    return APIResponse(success=True, message="Positioner connected", data=positioner_service.get_status())


@router.post("/positioner/move", response_model=APIResponse)
async def move_positioner(request: PositionerMoveRequest):
    try:
        status = await asyncio.to_thread(positioner_service.move_to, request.x, request.y, request.z, request.speed)
        return APIResponse(success=True, message="Positioner movement completed", data=status)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except (ValueError, RuntimeError, TimeoutError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/positioner/home", response_model=APIResponse)
async def home_positioner():
    try:
        status = await asyncio.to_thread(positioner_service.home)
        return APIResponse(success=True, message="Positioner homing completed", data=status)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except (RuntimeError, TimeoutError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/positioner/stop", response_model=APIResponse)
async def stop_positioner():
    await asyncio.to_thread(positioner_service.stop)
    return APIResponse(success=True, message="Positioner feed hold requested", data=positioner_service.get_status())


@router.get("/positioner/busy", response_model=APIResponse)
async def is_positioner_busy():
    busy = await asyncio.to_thread(positioner_service.is_busy)
    return APIResponse(success=True, message="Positioner busy state", data={"busy": busy})


@router.post("/positioner/calibrate/{axis}", response_model=PositionerCalibrateResponse)
async def calibrate_positioner_axis(axis: str):
    try:
        result = await asyncio.to_thread(positioner_service.calibrate_axis, axis)
        return PositionerCalibrateResponse(
            success=True,
            message=f"Axis {axis.upper()} calibrated successfully",
            data=result,
        )
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except (ValueError, RuntimeError, TimeoutError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/positioner/calibrate", response_model=APIResponse)
async def calibrate_positioner_all():
    try:
        results = await asyncio.to_thread(positioner_service.calibrate_all)
        return APIResponse(success=True, message="All axes calibrated", data={"axes": results})
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except (ValueError, RuntimeError, TimeoutError) as e:
        raise HTTPException(status_code=400, detail=str(e))
