from datetime import datetime, timezone
from typing import List
from pydantic import field_validator

class TimezoneAwareMixin:
    """
    Mixin to ensure specific datetime fields are timezone-aware (UTC).
    Usage: Add to Benie models and overide `__timezone_fields__ with field names
    """

    __timezone_fields__: List[str] = []

    @field_validator("*", mode="before")
    @classmethod
    def make_datetime_utc (cls, value, info):
        if not isinstance(value, datetime):
            return value
        
        if info.field_name in getattr(cls, "__timezone_fields__", []):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
        return value
    
    
    