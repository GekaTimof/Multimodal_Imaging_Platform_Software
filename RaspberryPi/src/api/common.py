from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field, field_validator


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
