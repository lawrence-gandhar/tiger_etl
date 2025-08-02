"""Resource validation models using Pydantic.

This module contains Pydantic models for validating resource data including
creation, updates, responses, and search operations.
"""

from typing import Optional
import re
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, ConfigDict

# Resource validation constants
RESOURCE_UUID_EMPTY_ERROR = "Resource UUID cannot be empty"
RESOURCE_UUID_FORMAT_ERROR = "Resource UUID must be a valid UUID format or custom format"
RESOURCE_NAME_EMPTY_ERROR = "Resource name cannot be empty"
RESOURCE_NAME_FORMAT_ERROR = "Resource name can only contain letters, numbers, spaces, underscores, and hyphens"
RESOURCE_NAME_LENGTH_ERROR = "Resource name must be between 1 and 200 characters"
DESCRIPTION_LENGTH_ERROR = "Description cannot exceed 1000 characters"


class ResourceBase(BaseModel):
    """Base Pydantic model for Resource with common fields.
    
    This model contains the common fields and validations that are shared
    across different resource operations.
    
    Attributes:
        resource_uuid: Unique resource identifier (max 50 characters)
        resource_name: Human-readable resource name (max 200 characters)
        description: Optional resource description (max 1000 characters)
        is_active: Boolean flag for resource status (default: True)
    """
    
    resource_uuid: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique resource identifier (UUID or custom format)"
    )
    resource_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable resource name"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional resource description"
    )
    is_active: bool = Field(
        default=True,
        description="Resource active status"
    )

    @field_validator('resource_uuid')
    @classmethod
    def validate_resource_uuid(cls, v: str) -> str:
        """Validate resource UUID format and constraints.
        
        Args:
            v: The resource UUID string to validate
            
        Returns:
            str: Validated resource UUID
            
        Raises:
            ValueError: If resource UUID is empty or contains invalid characters
        """
        if not v:
            raise ValueError(RESOURCE_UUID_EMPTY_ERROR)
        
        v = v.strip()
        
        # Allow standard UUID format or custom alphanumeric format with hyphens/underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError(RESOURCE_UUID_FORMAT_ERROR)
            
        return v.lower()  # Convert to lowercase for consistency

    @field_validator('resource_name')
    @classmethod
    def validate_resource_name(cls, v: str) -> str:
        """Validate resource name format and constraints.
        
        Args:
            v: The resource name string to validate
            
        Returns:
            str: Validated and normalized resource name
            
        Raises:
            ValueError: If resource name is empty or contains invalid characters
        """
        if not v:
            raise ValueError(RESOURCE_NAME_EMPTY_ERROR)
        
        v = v.strip()
        
        if len(v) == 0:
            raise ValueError(RESOURCE_NAME_EMPTY_ERROR)
        
        if len(v) > 200:
            raise ValueError(RESOURCE_NAME_LENGTH_ERROR)
        
        # Resource names can contain letters, numbers, spaces, underscores, and hyphens
        if not re.match(r'^[a-zA-Z0-9\s_-]+$', v):
            raise ValueError(RESOURCE_NAME_FORMAT_ERROR)
            
        return v.strip()  # Return trimmed name

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate description field.
        
        Args:
            v: The description string to validate (can be None)
            
        Returns:
            Optional[str]: Validated description or None
            
        Raises:
            ValueError: If description exceeds maximum length
        """
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None  # Convert empty strings to None
            
            if len(v) > 1000:
                raise ValueError(DESCRIPTION_LENGTH_ERROR)
                
            return v
        return v


class ResourceCreate(ResourceBase):
    """Pydantic model for creating a new resource.
    
    Extends ResourceBase with all required fields for resource creation.
    No additional fields needed as ResourceBase contains all creation requirements.
    """
    pass


class ResourceUpdate(BaseModel):
    """Pydantic model for updating an existing resource.
    
    All fields are optional to allow partial updates.
    
    Attributes:
        resource_uuid: Optional resource UUID update
        resource_name: Optional resource name update
        description: Optional description update
        is_active: Optional active status update
    """
    
    resource_uuid: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="Unique resource identifier"
    )
    resource_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Human-readable resource name"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional resource description"
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Resource active status"
    )
    
    @field_validator('resource_uuid')
    @classmethod
    def validate_resource_uuid(cls, v: Optional[str]) -> Optional[str]:
        """Validate resource UUID format for updates.
        
        Args:
            v: The resource UUID string to validate (can be None)
            
        Returns:
            Optional[str]: Validated resource UUID or None
            
        Raises:
            ValueError: If resource UUID is provided but invalid
        """
        if v is not None:
            if not v:
                raise ValueError(RESOURCE_UUID_EMPTY_ERROR)
            
            v = v.strip()
            
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError(RESOURCE_UUID_FORMAT_ERROR)
                
            return v.lower()
        return v
    
    @field_validator('resource_name')
    @classmethod
    def validate_resource_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate resource name for updates.
        
        Args:
            v: The resource name string to validate (can be None)
            
        Returns:
            Optional[str]: Validated resource name or None
            
        Raises:
            ValueError: If resource name is provided but invalid
        """
        if v is not None:
            if not v:
                raise ValueError(RESOURCE_NAME_EMPTY_ERROR)
            
            v = v.strip()
            
            if len(v) == 0:
                raise ValueError(RESOURCE_NAME_EMPTY_ERROR)
            
            if len(v) > 200:
                raise ValueError(RESOURCE_NAME_LENGTH_ERROR)
            
            if not re.match(r'^[a-zA-Z0-9\s_-]+$', v):
                raise ValueError(RESOURCE_NAME_FORMAT_ERROR)
                
            return v.strip()
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate description field for updates.
        
        Args:
            v: The description string to validate (can be None)
            
        Returns:
            Optional[str]: Validated description or None
            
        Raises:
            ValueError: If description is provided but exceeds maximum length
        """
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
            
            if len(v) > 1000:
                raise ValueError(DESCRIPTION_LENGTH_ERROR)
                
            return v
        return v


class ResourceResponse(ResourceBase):
    """Pydantic model for resource response data.
    
    Used for API responses, includes all resource data with timestamps.
    
    Attributes:
        id: Resource's unique identifier
        created_on: Resource creation timestamp
        updated_on: Resource last update timestamp
        Inherits all fields from ResourceBase
    """
    
    id: int = Field(..., description="Resource's unique identifier")
    created_on: Optional[datetime] = Field(
        default=None,
        description="Resource creation timestamp"
    )
    updated_on: Optional[datetime] = Field(
        default=None,
        description="Resource last update timestamp"
    )
    
    model_config = ConfigDict(from_attributes=True)


class ResourceSearch(BaseModel):
    """Pydantic model for resource search operations.
    
    Used for filtering and searching resources with various criteria.
    
    Attributes:
        resource_uuid: Optional UUID filter
        resource_name: Optional name filter (partial match)
        description: Optional description filter (partial match)
        is_active: Optional active status filter
        created_after: Optional filter for resources created after this date
        created_before: Optional filter for resources created before this date
        limit: Maximum number of results to return
        offset: Number of results to skip (for pagination)
    """
    
    resource_uuid: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Filter by resource UUID"
    )
    resource_name: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Filter by resource name (partial match)"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Filter by description (partial match)"
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Filter by active status"
    )
    created_after: Optional[datetime] = Field(
        default=None,
        description="Filter resources created after this date"
    )
    created_before: Optional[datetime] = Field(
        default=None,
        description="Filter resources created before this date"
    )
    limit: Optional[int] = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of results (1-1000)"
    )
    offset: Optional[int] = Field(
        default=0,
        ge=0,
        description="Number of results to skip"
    )


def validate_resource_id(resource_id: any) -> int:
    """Validate and convert resource ID to integer.
    
    Args:
        resource_id: The resource ID to validate (can be int, str, etc.)
        
    Returns:
        int: Validated resource ID
        
    Raises:
        ValueError: If resource ID is invalid
    """
    try:
        resource_id = int(resource_id)
        if resource_id <= 0:
            raise ValueError("Resource ID must be a positive integer")
        return resource_id
    except (ValueError, TypeError):
        raise ValueError("Resource ID must be a valid positive integer")


def generate_resource_uuid(prefix: str = "res") -> str:
    """Generate a unique resource UUID with optional prefix.
    
    Args:
        prefix: Optional prefix for the UUID (default: "res")
        
    Returns:
        str: Generated resource UUID in format "prefix-uuid"
    """
    unique_id = str(uuid.uuid4()).replace('-', '')[:12]  # Use first 12 chars
    return f"{prefix}-{unique_id}"
