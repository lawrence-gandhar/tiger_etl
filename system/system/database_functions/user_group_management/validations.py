"""Pydantic validation models for user group management.

This module contains Pydantic models for validating input data for user group
management operations, including user groups, user-group mappings, and related
operations with comprehensive field validation and business rules.
"""

from typing import Any, Dict, List, Optional, Annotated
from datetime import datetime
from pydantic import (
    BaseModel, 
    Field, 
    field_validator, 
    model_validator,
    ValidationError as PydanticValidationError,
    ConfigDict
)

from system.system.database_functions.exceptions import UserGroupValidationError


# ============================================================================
# Base Models and Common Validators
# ============================================================================

class BaseUserGroupModel(BaseModel):
    """Base model with common configuration for user group models."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        populate_by_name=True,
        str_strip_whitespace=True
    )


class PositiveInt(BaseModel):
    """Model for validating positive integers."""
    value: Annotated[int, Field(gt=0, description="Must be a positive integer")]
    
    @classmethod
    def validate_id(cls, value: Any, field_name: str = "ID") -> int:
        """Validate and return a positive integer ID.
        
        Args:
            value: Value to validate
            field_name: Name of the field for error messages
            
        Returns:
            int: Validated positive integer
            
        Raises:
            UserGroupValidationError: If validation fails
        """
        try:
            validated = cls(value=value)
            return validated.value
        except PydanticValidationError as e:
            error_details = e.errors()[0]
            error_msg = error_details.get('msg', str(e))
            raise UserGroupValidationError(f"{field_name} {error_msg}: {value}")


# ============================================================================
# User Group Models
# ============================================================================

class UserGroupCreateModel(BaseUserGroupModel):
    """Model for validating user group creation data."""
    
    group_name: Annotated[str, Field(min_length=2, max_length=100, description="Group name (2-100 characters)")]
    description: Annotated[str, Field(description="Group description")]
    is_active: bool = Field(default=True, description="Whether the group is active")
    created_by: Optional[str] = Field(default=None, description="User who created the group")
    
    @field_validator('group_name')
    @classmethod
    def validate_group_name(cls, v: str) -> str:
        """Validate group name format and content."""
        if not v or v.isspace():
            raise ValueError("Group name cannot be empty or only whitespace")
        
        # Check for invalid characters (example business rule)
        invalid_chars = ['<', '>', '"', "'", '&', '%']
        if any(char in v for char in invalid_chars):
            raise ValueError(f"Group name contains invalid characters: {invalid_chars}")
        
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate group description."""
        if not v or v.isspace():
            raise ValueError("Description cannot be empty or only whitespace")
        
        if len(v) > 500:
            raise ValueError("Description cannot exceed 500 characters")
        
        return v.strip()


class UserGroupUpdateModel(BaseUserGroupModel):
    """Model for validating user group update data."""
    
    group_name: Optional[Annotated[str, Field(min_length=2, max_length=100)]] = Field(
        default=None, description="Group name (2-100 characters)"
    )
    description: Optional[str] = Field(default=None, description="Group description")
    is_active: Optional[bool] = Field(default=None, description="Whether the group is active")
    updated_by: Optional[str] = Field(default=None, description="User who updated the group")
    
    @field_validator('group_name')
    @classmethod
    def validate_group_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate group name format and content."""
        if v is not None:
            if not v or v.isspace():
                raise ValueError("Group name cannot be empty or only whitespace")
            
            # Check for invalid characters
            invalid_chars = ['<', '>', '"', "'", '&', '%']
            if any(char in v for char in invalid_chars):
                raise ValueError(f"Group name contains invalid characters: {invalid_chars}")
            
            return v.strip()
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate group description."""
        if v is not None:
            if not v or v.isspace():
                raise ValueError("Description cannot be empty or only whitespace")
            
            if len(v) > 500:
                raise ValueError("Description cannot exceed 500 characters")
            
            return v.strip()
        return v
    
    @model_validator(mode='after')
    def validate_at_least_one_field(self) -> 'UserGroupUpdateModel':
        """Ensure at least one field is provided for update."""
        if not any([self.group_name, self.description, self.is_active is not None, self.updated_by]):
            raise ValueError("At least one field must be provided for update")
        return self


class UserGroupFiltersModel(BaseUserGroupModel):
    """Model for validating user group search/filter parameters."""
    
    group_name: Optional[str] = Field(default=None, description="Filter by group name (partial match)")
    description: Optional[str] = Field(default=None, description="Filter by description (partial match)")
    is_active: Optional[bool] = Field(default=None, description="Filter by active status")
    created_by: Optional[str] = Field(default=None, description="Filter by creator")
    created_after: Optional[datetime] = Field(default=None, description="Filter by creation date (after this date)")
    created_before: Optional[datetime] = Field(default=None, description="Filter by creation date (before this date)")
    
    @model_validator(mode='after')
    def validate_date_range(self) -> 'UserGroupFiltersModel':
        """Validate that created_after is before created_before."""
        if self.created_after and self.created_before and self.created_after >= self.created_before:
            raise ValueError("created_after must be before created_before")
        return self


class PaginationModel(BaseUserGroupModel):
    """Model for validating pagination parameters."""
    
    limit: Optional[Annotated[int, Field(ge=1, le=1000)]] = Field(
        default=None, description="Maximum number of records to return (1-1000)"
    )
    offset: Annotated[int, Field(ge=0)] = Field(default=0, description="Number of records to skip")


class SearchModel(BaseUserGroupModel):
    """Model for validating search parameters."""
    
    search_term: Annotated[str, Field(min_length=1)] = Field(..., description="Search term (minimum 1 character)")
    search_fields: List[str] = Field(
        default=['group_name', 'description'], 
        description="Fields to search in"
    )
    limit: Annotated[int, Field(ge=1, le=1000)] = Field(default=50, description="Maximum number of results (1-1000)")
    
    @field_validator('search_fields')
    @classmethod
    def validate_search_fields(cls, v: List[str]) -> List[str]:
        """Validate search fields are allowed."""
        allowed_fields = {'group_name', 'description', 'created_by'}
        invalid_fields = set(v) - allowed_fields
        
        if invalid_fields:
            raise ValueError(
                f"Invalid search fields: {invalid_fields}. "
                f"Allowed fields: {allowed_fields}"
            )
        
        if not v:
            raise ValueError("At least one search field must be specified")
        
        return v


# ============================================================================
# User Group Mapper Models
# ============================================================================

class UserGroupMappingCreateModel(BaseUserGroupModel):
    """Model for validating user-group mapping creation data."""
    
    user_id: Annotated[int, Field(gt=0)] = Field(..., description="User ID (must be positive integer)")
    group_id: Annotated[int, Field(gt=0)] = Field(..., description="Group ID (must be positive integer)")
    is_active: bool = Field(default=True, description="Whether the mapping is active")
    created_by: Optional[str] = Field(default=None, description="User who created the mapping")
    notes: Optional[Annotated[str, Field(max_length=500)]] = Field(
        default=None, description="Optional notes about the mapping"
    )


class UserGroupMappingUpdateModel(BaseUserGroupModel):
    """Model for validating user-group mapping update data."""
    
    is_active: Optional[bool] = Field(default=None, description="Whether the mapping is active")
    updated_by: Optional[str] = Field(default=None, description="User who updated the mapping")
    notes: Optional[Annotated[str, Field(max_length=500)]] = Field(
        default=None, description="Optional notes about the mapping"
    )
    
    @model_validator(mode='after')
    def validate_at_least_one_field(self) -> 'UserGroupMappingUpdateModel':
        """Ensure at least one field is provided for update."""
        if not any([self.is_active is not None, self.updated_by, self.notes]):
            raise ValueError("At least one field must be provided for update")
        return self


class UserGroupMappingFiltersModel(BaseUserGroupModel):
    """Model for validating user-group mapping filter parameters."""
    
    user_id: Optional[Annotated[int, Field(gt=0)]] = Field(default=None, description="Filter by user ID")
    group_id: Optional[Annotated[int, Field(gt=0)]] = Field(default=None, description="Filter by group ID")
    is_active: Optional[bool] = Field(default=None, description="Filter by active status")
    created_by: Optional[str] = Field(default=None, description="Filter by creator")
    updated_by: Optional[str] = Field(default=None, description="Filter by last updater")
    created_after: Optional[datetime] = Field(default=None, description="Filter by creation date (after this date)")
    created_before: Optional[datetime] = Field(default=None, description="Filter by creation date (before this date)")
    
    @model_validator(mode='after')
    def validate_date_range(self) -> 'UserGroupMappingFiltersModel':
        """Validate that created_after is before created_before."""
        if self.created_after and self.created_before and self.created_after >= self.created_before:
            raise ValueError("created_after must be before created_before")
        return self


class BulkMappingCreateModel(BaseUserGroupModel):
    """Model for validating bulk user-group mapping creation."""
    
    mappings: Annotated[List[UserGroupMappingCreateModel], Field(min_length=1, max_length=1000)] = Field(
        ..., description="List of mappings to create (1-1000 items)"
    )
    
    @field_validator('mappings')
    @classmethod
    def validate_unique_mappings(cls, v: List[UserGroupMappingCreateModel]) -> List[UserGroupMappingCreateModel]:
        """Ensure no duplicate user-group combinations."""
        seen_combinations = set()
        duplicates = []
        
        for i, mapping in enumerate(v):
            combination = (mapping.user_id, mapping.group_id)
            if combination in seen_combinations:
                duplicates.append(f"Position {i}: User {mapping.user_id} -> Group {mapping.group_id}")
            else:
                seen_combinations.add(combination)
        
        if duplicates:
            raise ValueError(f"Duplicate user-group combinations found: {duplicates}")
        
        return v


class BulkMappingUpdateModel(BaseUserGroupModel):
    """Model for validating bulk user-group mapping updates."""
    
    mapping_id: Annotated[int, Field(gt=0)] = Field(..., description="Mapping ID to update")
    data: UserGroupMappingUpdateModel = Field(..., description="Update data for the mapping")


class BulkMappingUpdatesModel(BaseUserGroupModel):
    """Model for validating bulk user-group mapping updates."""
    
    updates: Annotated[List[BulkMappingUpdateModel], Field(min_length=1, max_length=100)] = Field(
        ..., description="List of mapping updates (1-100 items)"
    )
    
    @field_validator('updates')
    @classmethod
    def validate_unique_mapping_ids(cls, v: List[BulkMappingUpdateModel]) -> List[BulkMappingUpdateModel]:
        """Ensure no duplicate mapping IDs."""
        seen_ids = set()
        duplicates = []
        
        for i, update in enumerate(v):
            mapping_id = update.mapping_id
            if mapping_id in seen_ids:
                duplicates.append(f"Position {i}: Mapping ID {mapping_id}")
            else:
                seen_ids.add(mapping_id)
        
        if duplicates:
            raise ValueError(f"Duplicate mapping IDs found: {duplicates}")
        
        return v


# ============================================================================
# Utility Models
# ============================================================================

class UserGroupActivationModel(BaseUserGroupModel):
    """Model for user-group activation/deactivation operations."""
    
    user_id: Annotated[int, Field(gt=0)] = Field(..., description="User ID (must be positive integer)")
    group_id: Annotated[int, Field(gt=0)] = Field(..., description="Group ID (must be positive integer)")


# ============================================================================
# Validation Helper Functions
# ============================================================================

def validate_group_create_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user group creation data using Pydantic.
    
    Args:
        data: Raw group creation data
        
    Returns:
        Dict[str, Any]: Validated and processed data
        
    Raises:
        UserGroupValidationError: If validation fails
    """
    try:
        model = UserGroupCreateModel(**data)
        return model.model_dump(exclude_none=True)
    except PydanticValidationError as e:
        error_messages = []
        for error in e.errors():
            field = " -> ".join(str(x) for x in error['loc'])
            msg = error['msg']
            error_messages.append(f"{field}: {msg}")
        
        raise UserGroupValidationError(
            f"Group creation validation failed: {'; '.join(error_messages)}"
        )


def validate_group_update_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user group update data using Pydantic.
    
    Args:
        data: Raw group update data
        
    Returns:
        Dict[str, Any]: Validated and processed data
        
    Raises:
        UserGroupValidationError: If validation fails
    """
    try:
        model = UserGroupUpdateModel(**data)
        return model.model_dump(exclude_none=True)
    except PydanticValidationError as e:
        error_messages = []
        for error in e.errors():
            field = " -> ".join(str(x) for x in error['loc'])
            msg = error['msg']
            error_messages.append(f"{field}: {msg}")
        
        raise UserGroupValidationError(
            f"Group update validation failed: {'; '.join(error_messages)}"
        )


def validate_group_filters(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user group filter parameters using Pydantic.
    
    Args:
        data: Raw filter data
        
    Returns:
        Dict[str, Any]: Validated and processed filters
        
    Raises:
        UserGroupValidationError: If validation fails
    """
    try:
        model = UserGroupFiltersModel(**data)
        return model.model_dump(exclude_none=True)
    except PydanticValidationError as e:
        error_messages = []
        for error in e.errors():
            field = " -> ".join(str(x) for x in error['loc'])
            msg = error['msg']
            error_messages.append(f"{field}: {msg}")
        
        raise UserGroupValidationError(
            f"Filter validation failed: {'; '.join(error_messages)}"
        )


def validate_pagination_params(limit: Optional[int] = None, offset: int = 0) -> Dict[str, Any]:
    """Validate pagination parameters using Pydantic.
    
    Args:
        limit: Maximum number of records
        offset: Number of records to skip
        
    Returns:
        Dict[str, Any]: Validated pagination parameters
        
    Raises:
        UserGroupValidationError: If validation fails
    """
    try:
        model = PaginationModel(limit=limit, offset=offset)
        return model.model_dump(exclude_none=True)
    except PydanticValidationError as e:
        error_messages = []
        for error in e.errors():
            field = " -> ".join(str(x) for x in error['loc'])
            msg = error['msg']
            error_messages.append(f"{field}: {msg}")
        
        raise UserGroupValidationError(
            f"Pagination validation failed: {'; '.join(error_messages)}"
        )


def validate_search_params(search_term: str, search_fields: List[str], limit: int) -> Dict[str, Any]:
    """Validate search parameters using Pydantic.
    
    Args:
        search_term: Search term
        search_fields: Fields to search in
        limit: Maximum number of results
        
    Returns:
        Dict[str, Any]: Validated search parameters
        
    Raises:
        UserGroupValidationError: If validation fails
    """
    try:
        model = SearchModel(
            search_term=search_term,
            search_fields=search_fields,
            limit=limit
        )
        return model.model_dump()
    except PydanticValidationError as e:
        error_messages = []
        for error in e.errors():
            field = " -> ".join(str(x) for x in error['loc'])
            msg = error['msg']
            error_messages.append(f"{field}: {msg}")
        
        raise UserGroupValidationError(
            f"Search validation failed: {'; '.join(error_messages)}"
        )


def validate_mapping_create_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user-group mapping creation data using Pydantic.
    
    Args:
        data: Raw mapping creation data
        
    Returns:
        Dict[str, Any]: Validated and processed data
        
    Raises:
        UserGroupValidationError: If validation fails
    """
    try:
        model = UserGroupMappingCreateModel(**data)
        return model.model_dump(exclude_none=True)
    except PydanticValidationError as e:
        error_messages = []
        for error in e.errors():
            field = " -> ".join(str(x) for x in error['loc'])
            msg = error['msg']
            error_messages.append(f"{field}: {msg}")
        
        raise UserGroupValidationError(
            f"Mapping creation validation failed: {'; '.join(error_messages)}"
        )


def validate_mapping_update_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user-group mapping update data using Pydantic.
    
    Args:
        data: Raw mapping update data
        
    Returns:
        Dict[str, Any]: Validated and processed data
        
    Raises:
        UserGroupValidationError: If validation fails
    """
    try:
        model = UserGroupMappingUpdateModel(**data)
        return model.model_dump(exclude_none=True)
    except PydanticValidationError as e:
        error_messages = []
        for error in e.errors():
            field = " -> ".join(str(x) for x in error['loc'])
            msg = error['msg']
            error_messages.append(f"{field}: {msg}")
        
        raise UserGroupValidationError(
            f"Mapping update validation failed: {'; '.join(error_messages)}"
        )


def validate_mapping_filters(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user-group mapping filter parameters using Pydantic.
    
    Args:
        data: Raw filter data
        
    Returns:
        Dict[str, Any]: Validated and processed filters
        
    Raises:
        UserGroupValidationError: If validation fails
    """
    try:
        model = UserGroupMappingFiltersModel(**data)
        return model.model_dump(exclude_none=True)
    except PydanticValidationError as e:
        error_messages = []
        for error in e.errors():
            field = " -> ".join(str(x) for x in error['loc'])
            msg = error['msg']
            error_messages.append(f"{field}: {msg}")
        
        raise UserGroupValidationError(
            f"Mapping filter validation failed: {'; '.join(error_messages)}"
        )


def validate_bulk_mapping_create_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate bulk user-group mapping creation data using Pydantic.
    
    Args:
        data: List of raw mapping creation data
        
    Returns:
        List[Dict[str, Any]]: Validated and processed data
        
    Raises:
        UserGroupValidationError: If validation fails
    """
    try:
        model = BulkMappingCreateModel(mappings=data)
        return [mapping.model_dump(exclude_none=True) for mapping in model.mappings]
    except PydanticValidationError as e:
        error_messages = []
        for error in e.errors():
            field = " -> ".join(str(x) for x in error['loc'])
            msg = error['msg']
            error_messages.append(f"{field}: {msg}")
        
        raise UserGroupValidationError(
            f"Bulk mapping creation validation failed: {'; '.join(error_messages)}"
        )


def validate_bulk_mapping_update_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate bulk user-group mapping update data using Pydantic.
    
    Args:
        data: List of raw mapping update data
        
    Returns:
        List[Dict[str, Any]]: Validated and processed data
        
    Raises:
        UserGroupValidationError: If validation fails
    """
    try:
        model = BulkMappingUpdatesModel(updates=data)
        return [
            {
                'mapping_id': update.mapping_id,
                'data': update.data.model_dump(exclude_none=True)
            }
            for update in model.updates
        ]
    except PydanticValidationError as e:
        error_messages = []
        for error in e.errors():
            field = " -> ".join(str(x) for x in error['loc'])
            msg = error['msg']
            error_messages.append(f"{field}: {msg}")
        
        raise UserGroupValidationError(
            f"Bulk mapping update validation failed: {'; '.join(error_messages)}"
        )


def validate_user_group_activation(user_id: Any, group_id: Any) -> Dict[str, Any]:
    """Validate user-group activation/deactivation parameters using Pydantic.
    
    Args:
        user_id: User ID
        group_id: Group ID
        
    Returns:
        Dict[str, Any]: Validated parameters
        
    Raises:
        UserGroupValidationError: If validation fails
    """
    try:
        model = UserGroupActivationModel(user_id=user_id, group_id=group_id)
        return model.model_dump()
    except PydanticValidationError as e:
        error_messages = []
        for error in e.errors():
            field = " -> ".join(str(x) for x in error['loc'])
            msg = error['msg']
            error_messages.append(f"{field}: {msg}")
        
        raise UserGroupValidationError(
            f"User-group activation validation failed: {'; '.join(error_messages)}"
        )


def validate_positive_integer(value: Any, field_name: str = "ID") -> int:
    """Validate that a value is a positive integer.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        
    Returns:
        int: Validated positive integer
        
    Raises:
        UserGroupValidationError: If validation fails
    """
    return PositiveInt.validate_id(value, field_name)
