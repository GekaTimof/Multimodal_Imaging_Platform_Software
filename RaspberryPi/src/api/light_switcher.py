from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from src.api.common import APIResponse
from src.services.light_switcher_service import light_switcher_service

router = APIRouter()


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


@router.get("/light-switcher/status", response_model=LightSwitcherStatusResponse)
async def get_light_switcher_status():
    """Get light switcher connection and status information."""
    try:
        status = light_switcher_service.get_status()
        return LightSwitcherStatusResponse(**status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting light switcher status: {str(e)}")


@router.post("/light-switcher/connect", response_model=APIResponse)
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


@router.post("/light-switcher/switch", response_model=APIResponse)
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


@router.post("/light-switcher/disconnect", response_model=APIResponse)
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
