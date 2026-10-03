from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from src.api.common import APIResponse, ParameterUpdateRequest
from src.services.database_service import db_service

router = APIRouter()


@router.get("/settings/{table_name}")
async def get_settings(table_name: str):
    """Get all settings from the specified table."""
    try:
        settings = db_service.get_all_settings(table_name)
        if not settings:
            raise HTTPException(status_code=404, detail=f"No settings found for table: {table_name}")

        return {"success": True, "data": settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/settings/update", response_model=APIResponse)
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
