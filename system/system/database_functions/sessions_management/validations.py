"""Pydantic validation models for session management operations.

This module provides comprehensive validation models for all session management
operations including creation, updates, responses, and search functionality.
All models include proper field validation, constraints, and error handling.

Example:
    Basic usage of validation models:
    
    >>> from system.system.models.sessions_management.validations import SessionCreate
    >>> 
    >>> # Validate session creation data
    >>> session_data = {
    ...     "user_id": 123,
    ...     "session_id": "unique-session-token-12345",
    ...     "ip_address": "192.168.1.100",
    ...     "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    ... }
    >>> validated_session = SessionCreate(**session_data)
    >>> print(validated_session.user_id)
    123
    
    >>> # Validate session update data
    >>> update_data = {"last_activity": "2024-01-01T12:00:00Z"}
    >>> validated_update = SessionUpdate(**update_data)
    >>> print(validated_update.last_activity)
    2024-01-01 12:00:00+00:00
"""

from datetime import datetime
from ipaddress import AddressValueError, ip_address
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field, field_validator, model_validator

from system.system.database_functions.sessions_management.sessions_management_constants import (
    DESCRIPTION_DEVICE_INFORMATION,
    DESCRIPTION_CLIENT_USER_AGENT_STRING,
    DESCRIPTION_UNIQUE_SESSION_IDENTIFIER,
    ERROR_INVALID_IP_ADDRESS_FORMAT,
    ERROR_SESSION_ID_EMPTY,
    ERROR_SESSION_ID_INVALID_CHARACTERS,
    EXAMPLE_DATETIME_ISO,
    EXAMPLE_WINDOWS_CHROME_DEVICE,
)


class SessionBase(BaseModel):
    """Base model for session data with common fields and validations."""
    
    user_id: int = Field(
        ...,
        gt=0,
        description="User ID - must be a positive integer",
        example=123
    )
    
    session_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description=DESCRIPTION_UNIQUE_SESSION_IDENTIFIER,
        example="sess-1234567890abcdef"
    )
    
    ip_address: Optional[str] = Field(
        None,
        max_length=45,  # IPv6 addresses can be up to 45 characters
        description="Client IP address (IPv4 or IPv6)",
        example="192.168.1.100"
    )
    
    user_agent: Optional[str] = Field(
        None,
        max_length=1000,
        description=DESCRIPTION_CLIENT_USER_AGENT_STRING,
        example="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    
    device_info: Optional[str] = Field(
        None,
        max_length=500,
        description=DESCRIPTION_DEVICE_INFORMATION,
        example=EXAMPLE_WINDOWS_CHROME_DEVICE
    )
    
    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v):
        """Validate session ID format and content."""
        if not v or not v.strip():
            raise ValueError(ERROR_SESSION_ID_EMPTY)
        
        # Remove whitespace
        v = v.strip()
        
        # Check for basic format (alphanumeric, hyphens, underscores)
        if not all(c.isalnum() or c in '-_' for c in v):
            raise ValueError(ERROR_SESSION_ID_INVALID_CHARACTERS)
        
        return v
    
    @field_validator('ip_address')
    @classmethod
    def validate_ip_address(cls, v):
        """Validate IP address format."""
        if v is not None and v.strip():
            try:
                ip_address(v.strip())
                return v.strip()
            except AddressValueError:
                raise ValueError(ERROR_INVALID_IP_ADDRESS_FORMAT)
        return v
    
    @field_validator('user_agent')
    @classmethod
    def validate_user_agent(cls, v):
        """Validate and clean user agent string."""
        if v is not None:
            # Remove excessive whitespace and control characters
            cleaned = ' '.join(v.split())
            return cleaned if cleaned else None
        return v
    
    @field_validator('device_info')
    @classmethod
    def validate_device_info(cls, v):
        """Validate and clean device info string."""
        if v is not None:
            # Remove excessive whitespace and control characters
            cleaned = ' '.join(v.split())
            return cleaned if cleaned else None
        return v


class SessionCreate(SessionBase):
    """Validation model for creating new sessions."""
    
    login_datetime: Optional[datetime] = Field(
        None,
        description="Login timestamp - defaults to current time if not provided",
        example=EXAMPLE_DATETIME_ISO
    )
    
    is_active: Optional[bool] = Field(
        True,
        description="Whether the session is active - defaults to True",
        example=True
    )
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "user_id": 123,
                "session_id": "sess-1234567890abcdef",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "device_info": EXAMPLE_WINDOWS_CHROME_DEVICE,
                "login_datetime": EXAMPLE_DATETIME_ISO,
                "is_active": True
            }
        }


class SessionUpdate(BaseModel):
    """Validation model for updating existing sessions."""
    
    user_id: Optional[int] = Field(
        None,
        gt=0,
        description="User ID - must be a positive integer"
    )
    
    session_id: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description=DESCRIPTION_UNIQUE_SESSION_IDENTIFIER
    )
    
    ip_address: Optional[str] = Field(
        None,
        max_length=45,
        description="Client IP address"
    )
    
    user_agent: Optional[str] = Field(
        None,
        max_length=1000,
        description=DESCRIPTION_CLIENT_USER_AGENT_STRING
    )
    
    device_info: Optional[str] = Field(
        None,
        max_length=500,
        description=DESCRIPTION_DEVICE_INFORMATION
    )
    
    login_datetime: Optional[datetime] = Field(
        None,
        description="Login timestamp"
    )
    
    logout_datetime: Optional[datetime] = Field(
        None,
        description="Logout timestamp"
    )
    
    last_activity: Optional[datetime] = Field(
        None,
        description="Last activity timestamp"
    )
    
    is_active: Optional[bool] = Field(
        None,
        description="Whether the session is active"
    )
    
    session_duration: Optional[int] = Field(
        None,
        ge=0,
        description="Session duration in seconds"
    )
    
    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v):
        """Validate session ID format if provided."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError(ERROR_SESSION_ID_EMPTY)
            
            v = v.strip()
            if not all(c.isalnum() or c in '-_' for c in v):
                raise ValueError(ERROR_SESSION_ID_INVALID_CHARACTERS)
        return v
    
    @field_validator('ip_address')
    @classmethod
    def validate_ip_address(cls, v):
        """Validate IP address format if provided."""
        if v is not None and v.strip():
            try:
                ip_address(v.strip())
                return v.strip()
            except AddressValueError:
                raise ValueError(ERROR_INVALID_IP_ADDRESS_FORMAT)
        return v
    
    @field_validator('logout_datetime')
    @classmethod
    def validate_logout_after_login(cls, v, info):
        """Validate that logout time is after login time."""
        if v is not None and info.data.get('login_datetime') is not None:
            if v <= info.data['login_datetime']:
                raise ValueError("Logout datetime must be after login datetime")
        return v
    
    @model_validator(mode='after')
    def validate_at_least_one_field(self):
        """Ensure at least one field is provided for update."""
        provided_fields = {k: v for k, v in self.__dict__.items() if v is not None}
        if not provided_fields:
            raise ValueError("At least one field must be provided for update")
        return self
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "last_activity": "2024-01-01T12:30:00Z",
                "is_active": True
            }
        }


class SessionResponse(BaseModel):
    """Validation model for session response data."""
    
    id: int = Field(
        ...,
        description="Database primary key ID",
        example=1
    )
    
    user_id: int = Field(
        ...,
        description="User ID",
        example=123
    )
    
    session_id: str = Field(
        ...,
        description="Unique session identifier",
        example="sess-1234567890abcdef"
    )
    
    ip_address: Optional[str] = Field(
        None,
        description="Client IP address",
        example="192.168.1.100"
    )
    
    user_agent: Optional[str] = Field(
        None,
        description="Client user agent string"
    )
    
    device_info: Optional[str] = Field(
        None,
        description="Device information"
    )
    
    login_datetime: datetime = Field(
        ...,
        description="Login timestamp",
        example=EXAMPLE_DATETIME_ISO
    )
    
    logout_datetime: Optional[datetime] = Field(
        None,
        description="Logout timestamp",
        example="2024-01-01T14:00:00Z"
    )
    
    last_activity: datetime = Field(
        ...,
        description="Last activity timestamp",
        example="2024-01-01T13:45:00Z"
    )
    
    is_active: bool = Field(
        ...,
        description="Whether the session is active",
        example=True
    )
    
    session_duration: Optional[int] = Field(
        None,
        description="Session duration in seconds",
        example=7200
    )
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "id": 1,
                "user_id": 123,
                "session_id": "sess-1234567890abcdef",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "device_info": EXAMPLE_WINDOWS_CHROME_DEVICE,
                "login_datetime": EXAMPLE_DATETIME_ISO,
                "logout_datetime": None,
                "last_activity": "2024-01-01T13:45:00Z",
                "is_active": True,
                "session_duration": None
            }
        }


class SessionSearch(BaseModel):
    """Validation model for session search and filtering operations."""
    
    user_id: Optional[int] = Field(
        None,
        gt=0,
        description="Filter by user ID"
    )
    
    session_id: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Filter by session ID"
    )
    
    ip_address: Optional[str] = Field(
        None,
        max_length=45,
        description="Filter by IP address"
    )
    
    is_active: Optional[bool] = Field(
        None,
        description="Filter by active status"
    )
    
    login_datetime_from: Optional[datetime] = Field(
        None,
        description="Filter sessions created after this datetime"
    )
    
    login_datetime_to: Optional[datetime] = Field(
        None,
        description="Filter sessions created before this datetime"
    )
    
    last_activity_from: Optional[datetime] = Field(
        None,
        description="Filter sessions with activity after this datetime"
    )
    
    last_activity_to: Optional[datetime] = Field(
        None,
        description="Filter sessions with activity before this datetime"
    )
    
    limit: Optional[int] = Field(
        100,
        ge=1,
        le=1000,
        description="Maximum number of results to return"
    )
    
    offset: Optional[int] = Field(
        0,
        ge=0,
        description="Number of results to skip"
    )
    
    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v):
        """Validate session ID format if provided."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError(ERROR_SESSION_ID_EMPTY)
            return v.strip()
        return v
    
    @field_validator('ip_address')
    @classmethod
    def validate_ip_address(cls, v):
        """Validate IP address format if provided."""
        if v is not None and v.strip():
            try:
                ip_address(v.strip())
                return v.strip()
            except AddressValueError:
                raise ValueError(ERROR_INVALID_IP_ADDRESS_FORMAT)
        return v
    
    @field_validator('login_datetime_to')
    @classmethod
    def validate_login_datetime_range(cls, v, info):
        """Validate that end date is after start date."""
        if v is not None and info.data.get('login_datetime_from') is not None:
            if v <= info.data['login_datetime_from']:
                raise ValueError("login_datetime_to must be after login_datetime_from")
        return v
    
    @field_validator('last_activity_to')
    @classmethod
    def validate_activity_datetime_range(cls, v, info):
        """Validate that end date is after start date."""
        if v is not None and info.data.get('last_activity_from') is not None:
            if v <= info.data['last_activity_from']:
                raise ValueError("last_activity_to must be after last_activity_from")
        return v
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "user_id": 123,
                "is_active": True,
                "login_datetime_from": "2024-01-01T00:00:00Z",
                "login_datetime_to": "2024-01-02T00:00:00Z",
                "limit": 50,
                "offset": 0
            }
        }


class SessionActivityUpdate(BaseModel):
    """Validation model for session activity updates."""
    
    session_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Session ID to update activity for"
    )
    
    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v):
        """Validate session ID format."""
        if not v or not v.strip():
            raise ValueError(ERROR_SESSION_ID_EMPTY)
        
        v = v.strip()
        if not all(c.isalnum() or c in '-_' for c in v):
            raise ValueError(ERROR_SESSION_ID_INVALID_CHARACTERS)
        return v
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "session_id": "sess-1234567890abcdef"
            }
        }


class SessionLogout(BaseModel):
    """Validation model for session logout operations."""
    
    session_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Session ID to logout"
    )
    
    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v):
        """Validate session ID format."""
        if not v or not v.strip():
            raise ValueError(ERROR_SESSION_ID_EMPTY)
        
        v = v.strip()
        if not all(c.isalnum() or c in '-_' for c in v):
            raise ValueError(ERROR_SESSION_ID_INVALID_CHARACTERS)
        return v
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "session_id": "sess-1234567890abcdef"
            }
        }


class SessionCleanup(BaseModel):
    """Validation model for session cleanup operations."""
    
    hours_inactive: int = Field(
        24,
        ge=1,
        le=8760,  # Max 1 year
        description="Hours of inactivity before considering session expired"
    )
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "hours_inactive": 24
            }
        }


class BulkSessionOperation(BaseModel):
    """Validation model for bulk session operations."""
    
    user_id: int = Field(
        ...,
        gt=0,
        description="User ID for bulk operations"
    )
    
    keep_active: Optional[bool] = Field(
        False,
        description="Whether to keep active sessions during bulk delete"
    )
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "user_id": 123,
                "keep_active": True
            }
        }


class SessionValidationError(BaseModel):
    """Model for validation error responses."""
    
    field: str = Field(
        ...,
        description="Field that failed validation"
    )
    
    message: str = Field(
        ...,
        description="Validation error message"
    )
    
    value: Any = Field(
        None,
        description="Value that failed validation"
    )
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "field": "session_id",
                "message": ERROR_SESSION_ID_EMPTY,
                "value": ""
            }
        }


class SessionListResponse(BaseModel):
    """Model for paginated session list responses."""
    
    sessions: List[SessionResponse] = Field(
        ...,
        description="List of session objects"
    )
    
    total: int = Field(
        ...,
        ge=0,
        description="Total number of sessions matching criteria"
    )
    
    limit: int = Field(
        ...,
        ge=1,
        description="Number of sessions requested"
    )
    
    offset: int = Field(
        ...,
        ge=0,
        description="Number of sessions skipped"
    )
    
    has_more: bool = Field(
        ...,
        description="Whether there are more sessions available"
    )
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "sessions": [
                    {
                        "id": 1,
                        "user_id": 123,
                        "session_id": "sess-1234567890abcdef",
                        "ip_address": "192.168.1.100",
                        "login_datetime": EXAMPLE_DATETIME_ISO,
                        "is_active": True
                    }
                ],
                "total": 150,
                "limit": 50,
                "offset": 0,
                "has_more": True
            }
        }


# Utility functions for validation
def validate_session_data(data: Dict[str, Any], operation: str = "create") -> Dict[str, Any]:
    """Validate session data based on operation type.
    
    Args:
        data: Dictionary containing session data
        operation: Type of operation ('create', 'update', 'search')
        
    Returns:
        Validated data dictionary
        
    Raises:
        ValidationError: If validation fails
    """
    if operation == "create":
        validated = SessionCreate(**data)
    elif operation == "update":
        validated = SessionUpdate(**data)
    elif operation == "search":
        validated = SessionSearch(**data)
    else:
        raise ValueError(f"Unknown operation type: {operation}")
    
    return validated.dict(exclude_unset=True)


def generate_session_token(prefix: str = "sess") -> str:
    """Generate a valid session token.
    
    Args:
        prefix: Prefix for the session token
        
    Returns:
        Generated session token
    """
    unique_id = str(uuid.uuid4()).replace('-', '')
    return f"{prefix}-{unique_id}"