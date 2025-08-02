"""User Group validation models using Pydantic.

This module contains Pydantic models for validating user group data including
group creation, updates, responses, and user-group mapping operations.
"""

from typing import Optional, List
import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, ConfigDict

# User Group validation constants
GROUP_NAME_EMPTY_ERROR = "Group name cannot be empty"
GROUP_NAME_FORMAT_ERROR = "Group name can only contain letters, numbers, spaces, underscores, and hyphens"
GROUP_NAME_LENGTH_ERROR = "Group name must be between 1 and 100 characters"
USER_ID_INVALID_ERROR = "User ID must be a positive integer"
GROUP_ID_INVALID_ERROR = "Group ID must be a positive integer"


class UserGroupBase(BaseModel):
    """Base Pydantic model for UserGroup with common fields.
    
    This model contains the common fields and validations that are shared
    across different user group operations.
    
    Attributes:
        group_name: Unique group name (max 100 characters)
        is_active: Boolean flag for group status (default: True)
    """
    
    group_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique group name (1-100 characters)"
    )
    is_active: bool = Field(
        default=True,
        description="Group active status"
    )

    @field_validator('group_name')
    @classmethod
    def validate_group_name(cls, v: str) -> str:
        """Validate group name format and constraints.
        
        Args:
            v: The group name string to validate
            
        Returns:
            str: Validated and normalized group name
            
        Raises:
            ValueError: If group name is empty or contains invalid characters
        """
        if not v:
            raise ValueError(GROUP_NAME_EMPTY_ERROR)
        
        v = v.strip()
        
        if len(v) == 0:
            raise ValueError(GROUP_NAME_EMPTY_ERROR)
        
        if len(v) > 100:
            raise ValueError(GROUP_NAME_LENGTH_ERROR)
        
        # Group names can contain letters, numbers, spaces, underscores, and hyphens
        if not re.match(r'^[a-zA-Z0-9\s_-]+$', v):
            raise ValueError(GROUP_NAME_FORMAT_ERROR)
            
        return v.strip()  # Return trimmed name


class UserGroupCreate(UserGroupBase):
    """Pydantic model for creating a new user group.
    
    Extends UserGroupBase with all required fields for group creation.
    No additional fields needed as UserGroupBase contains all creation requirements.
    """
    pass


class UserGroupUpdate(BaseModel):
    """Pydantic model for updating an existing user group.
    
    All fields are optional to allow partial updates.
    
    Attributes:
        group_name: Optional group name update
        is_active: Optional active status update
    """
    
    group_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Unique group name"
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Group active status"
    )
    
    @field_validator('group_name')
    @classmethod
    def validate_group_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate group name format for updates.
        
        Args:
            v: The group name string to validate (can be None)
            
        Returns:
            Optional[str]: Validated group name or None
            
        Raises:
            ValueError: If group name is provided but invalid
        """
        if v is not None:
            if not v:
                raise ValueError(GROUP_NAME_EMPTY_ERROR)
            
            v = v.strip()
            
            if len(v) == 0:
                raise ValueError(GROUP_NAME_EMPTY_ERROR)
            
            if len(v) > 100:
                raise ValueError(GROUP_NAME_LENGTH_ERROR)
            
            if not re.match(r'^[a-zA-Z0-9\s_-]+$', v):
                raise ValueError(GROUP_NAME_FORMAT_ERROR)
                
            return v.strip()
        return v


class UserGroupResponse(UserGroupBase):
    """Pydantic model for user group response data.
    
    Used for API responses, includes all group data with timestamps and statistics.
    
    Attributes:
        id: Group's unique identifier
        created_on: Group creation timestamp
        updated_on: Group last update timestamp
        status: Human-readable status string
        age_in_days: Number of days since creation
        active_user_count: Number of active users in the group
        Inherits all fields from UserGroupBase
    """
    
    id: int = Field(..., description="Group's unique identifier")
    created_on: Optional[datetime] = Field(
        default=None,
        description="Group creation timestamp"
    )
    updated_on: Optional[datetime] = Field(
        default=None,
        description="Group last update timestamp"
    )
    status: Optional[str] = Field(
        default=None,
        description="Human-readable status (Active/Inactive)"
    )
    age_in_days: Optional[int] = Field(
        default=None,
        description="Number of days since group creation"
    )
    active_user_count: Optional[int] = Field(
        default=None,
        description="Number of active users in the group"
    )
    
    model_config = ConfigDict(from_attributes=True)


class UserGroupMapperBase(BaseModel):
    """Base Pydantic model for UserGroupMapper with common fields.
    
    This model contains the common fields and validations for user-group mappings.
    
    Attributes:
        group_id: Foreign key reference to UserGroups.id
        user_id: Foreign key reference to User.id
        is_active: Boolean flag for mapping status (default: True)
    """
    
    group_id: int = Field(
        ...,
        gt=0,
        description="Group ID (positive integer)"
    )
    user_id: int = Field(
        ...,
        gt=0,
        description="User ID (positive integer)"
    )
    is_active: bool = Field(
        default=True,
        description="Mapping active status"
    )

    @field_validator('group_id')
    @classmethod
    def validate_group_id(cls, v: int) -> int:
        """Validate group ID.
        
        Args:
            v: The group ID to validate
            
        Returns:
            int: Validated group ID
            
        Raises:
            ValueError: If group ID is not a positive integer
        """
        if not isinstance(v, int) or v <= 0:
            raise ValueError(GROUP_ID_INVALID_ERROR)
        return v

    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v: int) -> int:
        """Validate user ID.
        
        Args:
            v: The user ID to validate
            
        Returns:
            int: Validated user ID
            
        Raises:
            ValueError: If user ID is not a positive integer
        """
        if not isinstance(v, int) or v <= 0:
            raise ValueError(USER_ID_INVALID_ERROR)
        return v


class UserGroupMapperCreate(UserGroupMapperBase):
    """Pydantic model for creating a new user-group mapping.
    
    Extends UserGroupMapperBase with all required fields for mapping creation.
    """
    pass


class UserGroupMapperUpdate(BaseModel):
    """Pydantic model for updating an existing user-group mapping.
    
    All fields are optional to allow partial updates.
    
    Attributes:
        group_id: Optional group ID update
        user_id: Optional user ID update
        is_active: Optional active status update
    """
    
    group_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Group ID (positive integer)"
    )
    user_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="User ID (positive integer)"
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Mapping active status"
    )
    
    @field_validator('group_id')
    @classmethod
    def validate_group_id(cls, v: Optional[int]) -> Optional[int]:
        """Validate group ID for updates.
        
        Args:
            v: The group ID to validate (can be None)
            
        Returns:
            Optional[int]: Validated group ID or None
            
        Raises:
            ValueError: If group ID is provided but invalid
        """
        if v is not None and (not isinstance(v, int) or v <= 0):
            raise ValueError(GROUP_ID_INVALID_ERROR)
        return v

    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v: Optional[int]) -> Optional[int]:
        """Validate user ID for updates.
        
        Args:
            v: The user ID to validate (can be None)
            
        Returns:
            Optional[int]: Validated user ID or None
            
        Raises:
            ValueError: If user ID is provided but invalid
        """
        if v is not None and (not isinstance(v, int) or v <= 0):
            raise ValueError(USER_ID_INVALID_ERROR)
        return v


class UserGroupMapperResponse(UserGroupMapperBase):
    """Pydantic model for user-group mapping response data.
    
    Used for API responses, includes all mapping data with timestamps.
    
    Attributes:
        id: Mapping's unique identifier
        created_on: Mapping creation timestamp
        status: Human-readable status string
        Inherits all fields from UserGroupMapperBase
    """
    
    id: int = Field(..., description="Mapping's unique identifier")
    created_on: Optional[datetime] = Field(
        default=None,
        description="Mapping creation timestamp"
    )
    status: Optional[str] = Field(
        default=None,
        description="Human-readable status (Active/Inactive)"
    )
    
    model_config = ConfigDict(from_attributes=True)


class UserGroupSearch(BaseModel):
    """Pydantic model for user group search operations.
    
    Used for filtering and searching user groups with various criteria.
    
    Attributes:
        group_name: Optional name filter (partial match)
        is_active: Optional active status filter
        created_after: Optional filter for groups created after this date
        created_before: Optional filter for groups created before this date
        has_users: Optional filter for groups with/without users
        min_user_count: Optional minimum user count filter
        max_user_count: Optional maximum user count filter
        limit: Maximum number of results to return
        offset: Number of results to skip (for pagination)
    """
    
    group_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Filter by group name (partial match)"
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Filter by active status"
    )
    created_after: Optional[datetime] = Field(
        default=None,
        description="Filter groups created after this date"
    )
    created_before: Optional[datetime] = Field(
        default=None,
        description="Filter groups created before this date"
    )
    has_users: Optional[bool] = Field(
        default=None,
        description="Filter groups with (True) or without (False) users"
    )
    min_user_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Minimum number of users in group"
    )
    max_user_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Maximum number of users in group"
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


class BulkUserGroupOperation(BaseModel):
    """Pydantic model for bulk user-group operations.
    
    Used for adding/removing multiple users to/from groups efficiently.
    
    Attributes:
        group_id: Target group ID
        user_ids: List of user IDs to operate on
        operation: Type of operation ('add' or 'remove')
        is_active: Status for new mappings (only used for 'add' operations)
    """
    
    group_id: int = Field(
        ...,
        gt=0,
        description="Target group ID"
    )
    user_ids: List[int] = Field(
        ...,
        min_length=1,
        description="List of user IDs (at least 1 required)"
    )
    operation: str = Field(
        ...,
        description="Operation type: 'add' or 'remove'"
    )
    is_active: bool = Field(
        default=True,
        description="Status for new mappings (add operations only)"
    )

    @field_validator('operation')
    @classmethod
    def validate_operation(cls, v: str) -> str:
        """Validate operation type.
        
        Args:
            v: The operation string to validate
            
        Returns:
            str: Validated operation (lowercase)
            
        Raises:
            ValueError: If operation is not 'add' or 'remove'
        """
        v = v.lower().strip()
        if v not in ['add', 'remove']:
            raise ValueError("Operation must be 'add' or 'remove'")
        return v

    @field_validator('user_ids')
    @classmethod
    def validate_user_ids(cls, v: List[int]) -> List[int]:
        """Validate user IDs list.
        
        Args:
            v: The list of user IDs to validate
            
        Returns:
            List[int]: Validated list of unique user IDs
            
        Raises:
            ValueError: If any user ID is invalid or list is empty
        """
        if not v:
            raise ValueError("At least one user ID is required")
        
        # Validate each user ID
        for user_id in v:
            if not isinstance(user_id, int) or user_id <= 0:
                raise ValueError(f"Invalid user ID: {user_id}. Must be a positive integer.")
        
        # Remove duplicates while preserving order
        unique_ids = list(dict.fromkeys(v))
        return unique_ids


def validate_group_id(group_id: any) -> int:
    """Validate and convert group ID to integer.
    
    Args:
        group_id: The group ID to validate (can be int, str, etc.)
        
    Returns:
        int: Validated group ID
        
    Raises:
        ValueError: If group ID is invalid
    """
    try:
        group_id = int(group_id)
        if group_id <= 0:
            raise ValueError("Group ID must be a positive integer")
        return group_id
    except (ValueError, TypeError):
        raise ValueError("Group ID must be a valid positive integer")


def validate_user_id(user_id: any) -> int:
    """Validate and convert user ID to integer.
    
    Args:
        user_id: The user ID to validate (can be int, str, etc.)
        
    Returns:
        int: Validated user ID
        
    Raises:
        ValueError: If user ID is invalid
    """
    try:
        user_id = int(user_id)
        if user_id <= 0:
            raise ValueError("User ID must be a positive integer")
        return user_id
    except (ValueError, TypeError):
        raise ValueError("User ID must be a valid positive integer")
