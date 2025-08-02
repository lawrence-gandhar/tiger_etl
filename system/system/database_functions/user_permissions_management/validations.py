"""Validation models and functions for user permissions management.

This module contains Pydantic models and validation functions for user permission data
validation in the user permissions management system.
"""

from pydantic import BaseModel, field_validator, Field
from typing import Optional, Any

from system.system.database_functions.exceptions import UserPermissionValidationError
from system.system.database_functions.user_permissions_management.user_permissions_management_constants import (
    PERMISSION_TYPES, 
    PERMISSION_LEVELS, 
    DEFAULT_PERMISSION_LEVEL,
    DEFAULT_PERMISSION_TYPE,
    DEFAULT_IS_ACTIVE
)


class UserPermissionCreate(BaseModel):
    """Model for validating user permission creation data.
    
    Attributes:
        user_id: ID of the user to assign permission to
        resource_id: ID of the resource for which permission is granted
        permission_type: Type of permission (read, write, delete, etc.)
        permission_level: Level of permission (1-4, low to critical)
        is_active: Whether the permission is currently active
        granted_by: ID of the user who granted this permission
        notes: Optional notes about the permission
        
    Example:
        >>> permission_data = UserPermissionCreate(
        ...     user_id=1,
        ...     resource_id=10,
        ...     permission_type="read",
        ...     permission_level=2,
        ...     granted_by=5
        ... )
        >>> print(permission_data.permission_type)
        read
    """
    user_id: int = Field(..., gt=0, description="User ID must be positive")
    resource_id: int = Field(..., gt=0, description="Resource ID must be positive")
    permission_type: str = Field(default=DEFAULT_PERMISSION_TYPE, description="Type of permission")
    permission_level: int = Field(default=DEFAULT_PERMISSION_LEVEL, ge=1, le=4, description="Permission level 1-4")
    is_active: bool = Field(default=DEFAULT_IS_ACTIVE, description="Whether permission is active")
    granted_by: int = Field(..., gt=0, description="ID of user who granted permission")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")
    
    @field_validator('permission_type')
    @classmethod
    def validate_permission_type(cls, v: str) -> str:
        """Validate that permission_type is one of the allowed types."""
        if v.lower() not in PERMISSION_TYPES:
            raise UserPermissionValidationError(
                f"Permission type must be one of: {', '.join(PERMISSION_TYPES)}"
            )
        return v.lower()


class UserPermissionUpdate(BaseModel):
    """Model for validating user permission update data.
    
    All fields are optional for partial updates. Only provided fields will be updated.
    
    Attributes:
        permission_type: Type of permission (read, write, delete, etc.)
        permission_level: Level of permission (1-4, low to critical)
        is_active: Whether the permission is currently active
        notes: Optional notes about the permission
        modified_by: ID of the user who modified this permission
        
    Example:
        >>> update_data = UserPermissionUpdate(
        ...     permission_level=3,
        ...     is_active=False,
        ...     modified_by=5
        ... )
        >>> print(update_data.permission_level)
        3
    """
    permission_type: Optional[str] = Field(None, description="Type of permission")
    permission_level: Optional[int] = Field(None, ge=1, le=4, description="Permission level 1-4")
    is_active: Optional[bool] = Field(None, description="Whether permission is active")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")
    modified_by: Optional[int] = Field(None, gt=0, description="ID of user who modified permission")
    
    @field_validator('permission_type')
    @classmethod
    def validate_permission_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate that permission_type is one of the allowed types."""
        if v is not None and v.lower() not in PERMISSION_TYPES:
            raise UserPermissionValidationError(
                f"Permission type must be one of: {', '.join(PERMISSION_TYPES)}"
            )
        return v.lower() if v is not None else None


def validate_user_permission_id(permission_id: Any) -> int:
    """Validate user permission ID.
    
    Args:
        permission_id: The permission ID to validate
        
    Returns:
        The validated permission ID as an integer
        
    Raises:
        UserPermissionValidationError: If permission ID is invalid
        
    Example:
        >>> validate_user_permission_id(123)
        123
        >>> validate_user_permission_id("456")
        456
        >>> validate_user_permission_id(-1)  # Raises exception
    """
    try:
        permission_id = int(permission_id)
        if permission_id <= 0:
            raise UserPermissionValidationError("Permission ID must be a positive integer")
        return permission_id
    except (ValueError, TypeError) as exc:
        raise UserPermissionValidationError("Permission ID must be a valid integer") from exc


def validate_permission_level_name(level_name: str) -> int:
    """Validate and convert permission level name to numeric value.
    
    Args:
        level_name: Permission level name (low, medium, high, critical)
        
    Returns:
        Numeric permission level (1-4)
        
    Raises:
        UserPermissionValidationError: If level name is invalid
        
    Example:
        >>> validate_permission_level_name("high")
        3
        >>> validate_permission_level_name("invalid")  # Raises exception
    """
    level_name = level_name.lower().strip()
    if level_name not in PERMISSION_LEVELS:
        raise UserPermissionValidationError(
            f"Permission level must be one of: {', '.join(PERMISSION_LEVELS.keys())}"
        )
    return PERMISSION_LEVELS[level_name]


class UserPermissionBulkCreate(BaseModel):
    """Model for validating bulk user permission creation.
    
    Attributes:
        permissions: List of user permission creation data
        granted_by: ID of the user who granted these permissions
        skip_duplicates: Whether to skip existing permissions instead of raising error
        
    Example:
        >>> bulk_data = UserPermissionBulkCreate(
        ...     permissions=[
        ...         {"user_id": 1, "resource_id": 10, "permission_type": "read"},
        ...         {"user_id": 2, "resource_id": 10, "permission_type": "write"}
        ...     ],
        ...     granted_by=5
        ... )
        >>> print(len(bulk_data.permissions))
        2
    """
    permissions: list[dict] = Field(..., min_items=1, max_items=100, description="List of permissions to create")
    granted_by: int = Field(..., gt=0, description="ID of user who granted permissions")
    skip_duplicates: bool = Field(default=False, description="Skip existing permissions")
    
    @field_validator('permissions')
    @classmethod
    def validate_permissions(cls, v: list) -> list:
        """Validate each permission in the list."""
        validated_permissions = []
        for i, perm in enumerate(v):
            try:
                # Add granted_by to each permission if not present
                if 'granted_by' not in perm:
                    perm['granted_by'] = None  # Will be set later
                validated_perm = UserPermissionCreate(**perm)
                validated_permissions.append(validated_perm.model_dump())
            except Exception as exc:
                raise UserPermissionValidationError(
                    f"Invalid permission data at index {i}: {str(exc)}"
                ) from exc
        return validated_permissions
