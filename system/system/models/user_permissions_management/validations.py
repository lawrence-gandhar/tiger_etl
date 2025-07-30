"""User permissions validation models using Pydantic.

This module contains Pydantic models for validating user permissions data including
creation, updates, responses, and permission management operations.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict

try:
    from system.system.constants.model_constants.user_permissions_management_constants import (
        VALID_PERMISSION_TYPES,
        PERMISSION_TYPE_ERROR,
        USER_ID_ERROR,
        DUPLICATE_PERMISSIONS_ERROR,
        DEFAULT_PERMISSION_VALUE,
        USER_ID_MIN_VALUE,
    )
except ImportError:
    # Fallback constants if import fails
    VALID_PERMISSION_TYPES = {
        'full_access', 'read_access', 'write_access', 'create_access',
        'edit_access', 'delete_access', 'execute_access', 'drop_access', 
        'view_access', 'insert_access', 'update_access'
    }
    PERMISSION_TYPE_ERROR = "Invalid permission type. Must be one of: {types}"
    USER_ID_ERROR = "User ID must be a positive integer"
    DUPLICATE_PERMISSIONS_ERROR = "Duplicate permission types are not allowed in bulk update"
    DEFAULT_PERMISSION_VALUE = False
    USER_ID_MIN_VALUE = 1


class UserPermissionsBase(BaseModel):
    """Base Pydantic model for UserPermissions with common fields.
    
    This model contains the common fields and validations that are shared
    across different user permissions operations.
    
    Attributes:
        user_id: Reference to User ID (positive integer)
        full_access: Boolean flag for full system access
        read_access: Boolean flag for read operations
        write_access: Boolean flag for write operations
        create_access: Boolean flag for create operations
        edit_access: Boolean flag for edit operations
        delete_access: Boolean flag for delete operations
        execute_access: Boolean flag for execute operations
        drop_access: Boolean flag for drop operations
        view_access: Boolean flag for view operations
        insert_access: Boolean flag for insert operations
        update_access: Boolean flag for update operations
    """
    
    user_id: int = Field(
        ...,
        gt=USER_ID_MIN_VALUE-1,
        description="User ID reference (must be positive integer)"
    )
    full_access: bool = Field(
        default=DEFAULT_PERMISSION_VALUE,
        description="Full system access permission"
    )
    read_access: bool = Field(
        default=DEFAULT_PERMISSION_VALUE,
        description="Read operations permission"
    )
    write_access: bool = Field(
        default=DEFAULT_PERMISSION_VALUE,
        description="Write operations permission"
    )
    create_access: bool = Field(
        default=DEFAULT_PERMISSION_VALUE,
        description="Create operations permission"
    )
    edit_access: bool = Field(
        default=DEFAULT_PERMISSION_VALUE,
        description="Edit operations permission"
    )
    delete_access: bool = Field(
        default=DEFAULT_PERMISSION_VALUE,
        description="Delete operations permission"
    )
    execute_access: bool = Field(
        default=DEFAULT_PERMISSION_VALUE,
        description="Execute operations permission"
    )
    drop_access: bool = Field(
        default=DEFAULT_PERMISSION_VALUE,
        description="Drop operations permission"
    )
    view_access: bool = Field(
        default=DEFAULT_PERMISSION_VALUE,
        description="View operations permission"
    )
    insert_access: bool = Field(
        default=DEFAULT_PERMISSION_VALUE,
        description="Insert operations permission"
    )
    update_access: bool = Field(
        default=DEFAULT_PERMISSION_VALUE,
        description="Update operations permission"
    )

    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v: int) -> int:
        """Validate user_id is a positive integer.
        
        Args:
            v: The user_id to validate
            
        Returns:
            int: Validated user_id
            
        Raises:
            ValueError: If user_id is not positive
        """
        if v <= 0:
            raise ValueError(USER_ID_ERROR)
        return v

    @field_validator(
        'full_access', 'read_access', 'write_access', 'create_access',
        'edit_access', 'delete_access', 'execute_access', 
        'drop_access', 'view_access', 'insert_access', 'update_access'
    )
    @classmethod
    def validate_permissions(cls, v: bool) -> bool:
        """Validate permission fields are boolean.
        
        Args:
            v: The permission value to validate
            
        Returns:
            bool: Validated permission value
        """
        return bool(v)


class UserPermissionsCreate(UserPermissionsBase):
    """Pydantic model for creating new user permissions.
    
    Extends UserPermissionsBase for user permissions creation.
    All permission fields default to False for security.
    """
    
    def get_permission_summary(self) -> Dict[str, bool]:
        """Get a summary of all permissions.
        
        Returns:
            Dict[str, bool]: Dictionary of all permission states
        """
        return {
            'full_access': self.full_access,
            'read_access': self.read_access,
            'write_access': self.write_access,
            'create_access': self.create_access,
            'edit_access': self.edit_access,
            'delete_access': self.delete_access,
            'execute_access': self.execute_access,
            'drop_access': self.drop_access,
            'view_access': self.view_access,
            'insert_access': self.insert_access,
            'update_access': self.update_access
        }
    
    def has_any_permissions(self) -> bool:
        """Check if user has any permissions granted.
        
        Returns:
            bool: True if any permission is granted, False otherwise
        """
        permissions = self.get_permission_summary()
        return any(permissions.values())


class UserPermissionsUpdate(BaseModel):
    """Pydantic model for updating existing user permissions.
    
    All fields are optional to allow partial updates.
    
    Attributes:
        user_id: Optional user ID update
        full_access: Optional full access update
        read_access: Optional read access update
        write_access: Optional write access update
        create_access: Optional create access update
        edit_access: Optional edit access update
        delete_access: Optional delete access update
        execute_access: Optional execute access update
        drop_access: Optional drop access update
        view_access: Optional view access update
        insert_access: Optional insert access update
        update_access: Optional update access update
    """
    
    user_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="User ID reference (must be positive integer)"
    )
    full_access: Optional[bool] = Field(
        default=None,
        description="Full system access permission"
    )
    read_access: Optional[bool] = Field(
        default=None,
        description="Read operations permission"
    )
    write_access: Optional[bool] = Field(
        default=None,
        description="Write operations permission"
    )
    create_access: Optional[bool] = Field(
        default=None,
        description="Create operations permission"
    )
    edit_access: Optional[bool] = Field(
        default=None,
        description="Edit operations permission"
    )
    delete_access: Optional[bool] = Field(
        default=None,
        description="Delete operations permission"
    )
    execute_access: Optional[bool] = Field(
        default=None,
        description="Execute operations permission"
    )
    drop_access: Optional[bool] = Field(
        default=None,
        description="Drop operations permission"
    )
    view_access: Optional[bool] = Field(
        default=None,
        description="View operations permission"
    )
    insert_access: Optional[bool] = Field(
        default=None,
        description="Insert operations permission"
    )
    update_access: Optional[bool] = Field(
        default=None,
        description="Update operations permission"
    )

    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v: Optional[int]) -> Optional[int]:
        """Validate user_id for updates.
        
        Args:
            v: The user_id to validate (can be None)
            
        Returns:
            Optional[int]: Validated user_id or None
            
        Raises:
            ValueError: If user_id is provided but not positive
        """
        if v is not None and v <= 0:
            raise ValueError(USER_ID_ERROR)
        return v

    def get_updated_fields(self) -> Dict[str, Any]:
        """Get only the fields that are being updated.
        
        Returns:
            Dict[str, Any]: Dictionary of fields with non-None values
        """
        return {
            field: value for field, value in self.model_dump().items()
            if value is not None
        }


class UserPermissionsResponse(UserPermissionsBase):
    """Pydantic model for user permissions response data.
    
    Used for API responses, includes the permission ID.
    
    Attributes:
        id: Permission record's unique identifier
        Inherits all fields from UserPermissionsBase
    """
    
    id: int = Field(..., description="Permission record's unique identifier")
    
    model_config = ConfigDict(from_attributes=True)
    
    def get_granted_permissions(self) -> List[str]:
        """Get list of permission types that are granted.
        
        Returns:
            List[str]: List of permission types that are True
        """
        permissions = self.get_permission_summary()
        return [perm_type for perm_type, granted in permissions.items() if granted]
    
    def get_permission_summary(self) -> Dict[str, bool]:
        """Get a summary of all permissions.
        
        Returns:
            Dict[str, bool]: Dictionary of all permission states
        """
        return {
            'full_access': self.full_access,
            'read_access': self.read_access,
            'write_access': self.write_access,
            'create_access': self.create_access,
            'edit_access': self.edit_access,
            'delete_access': self.delete_access,
            'execute_access': self.execute_access,
            'drop_access': self.drop_access,
            'view_access': self.view_access,
            'insert_access': self.insert_access,
            'update_access': self.update_access
        }


class SinglePermissionUpdate(BaseModel):
    """Pydantic model for updating a single permission.
    
    Used for granting or revoking specific permissions.
    
    Attributes:
        permission_type: The type of permission to update
        granted: Whether the permission should be granted or revoked
    """
    
    permission_type: str = Field(
        ...,
        description="Type of permission to update"
    )
    granted: bool = Field(
        ...,
        description="Whether to grant (True) or revoke (False) the permission"
    )
    
    @field_validator('permission_type')
    @classmethod
    def validate_permission_type(cls, v: str) -> str:
        """Validate permission type is valid.
        
        Args:
            v: The permission type to validate
            
        Returns:
            str: Validated permission type
            
        Raises:
            ValueError: If permission type is not valid
        """
        if v not in VALID_PERMISSION_TYPES:
            raise ValueError(
                PERMISSION_TYPE_ERROR.format(types=', '.join(sorted(VALID_PERMISSION_TYPES)))
            )
        return v


class BulkPermissionUpdate(BaseModel):
    """Pydantic model for bulk permission updates.
    
    Used for updating multiple permissions at once.
    
    Attributes:
        user_id: User ID for the permissions
        permissions: List of permission updates
    """
    
    user_id: int = Field(
        ...,
        gt=0,
        description="User ID for the permissions"
    )
    permissions: List[SinglePermissionUpdate] = Field(
        ...,
        min_length=1,
        description="List of permission updates"
    )
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v: int) -> int:
        """Validate user_id is a positive integer.
        
        Args:
            v: The user_id to validate
            
        Returns:
            int: Validated user_id
            
        Raises:
            ValueError: If user_id is not positive
        """
        if v <= 0:
            raise ValueError(USER_ID_ERROR)
        return v
    
    @field_validator('permissions')
    @classmethod
    def validate_permissions_list(cls, v: List[SinglePermissionUpdate]) -> List[SinglePermissionUpdate]:
        """Validate permissions list.
        
        Args:
            v: List of permission updates to validate
            
        Returns:
            List[SinglePermissionUpdate]: Validated permissions list
            
        Raises:
            ValueError: If there are duplicate permission types
        """
        permission_types = [perm.permission_type for perm in v]
        if len(permission_types) != len(set(permission_types)):
            raise ValueError(DUPLICATE_PERMISSIONS_ERROR)
        return v


class UserPermissionQuery(BaseModel):
    """Pydantic model for querying user permissions.
    
    Used for filtering and searching permissions.
    
    Attributes:
        user_id: Optional user ID filter
        permission_type: Optional permission type filter
        granted_only: Whether to return only granted permissions
    """
    
    user_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Filter by user ID"
    )
    permission_type: Optional[str] = Field(
        default=None,
        description="Filter by permission type"
    )
    granted_only: bool = Field(
        default=False,
        description="Return only granted permissions"
    )
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v: Optional[int]) -> Optional[int]:
        """Validate user_id filter.
        
        Args:
            v: The user_id to validate (can be None)
            
        Returns:
            Optional[int]: Validated user_id or None
            
        Raises:
            ValueError: If user_id is provided but not positive
        """
        if v is not None and v <= 0:
            raise ValueError(USER_ID_ERROR)
        return v
    
    @field_validator('permission_type')
    @classmethod
    def validate_permission_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate permission type filter.
        
        Args:
            v: The permission type to validate (can be None)
            
        Returns:
            Optional[str]: Validated permission type or None
            
        Raises:
            ValueError: If permission type is provided but not valid
        """
        if v is not None and v not in VALID_PERMISSION_TYPES:
            raise ValueError(
                PERMISSION_TYPE_ERROR.format(types=', '.join(sorted(VALID_PERMISSION_TYPES)))
            )
        return v