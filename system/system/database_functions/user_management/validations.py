"""Validation models and functions for user management.

This module contains Pydantic models and validation functions for user data
validation in the user management system.
"""

from pydantic import BaseModel, EmailStr, field_validator, Field
from typing import Optional

from system.system.database_functions.exceptions import UserValidationError


class UserCreate(BaseModel):
    """Model for validating user creation data.
    
    Attributes:
        email: User's email address (must be valid email format)
        name: User's display name (minimum 1 character)
        
    Example:
        >>> user_data = UserCreate(
        ...     email="john.doe@example.com",
        ...     name="John Doe"
        ... )
        >>> print(user_data.email)
        john.doe@example.com
    """
    email: EmailStr
    name: str = Field(..., min_length=1, description="User's display name")


class UserUpdate(BaseModel):
    """Model for validating user update data.
    
    All fields are optional for partial updates. Only provided fields will be updated.
    
    Attributes:
        name: User's display name (minimum 1 character if provided)
        password: User's password (minimum 8 characters if provided)
        
    Example:
        >>> update_data = UserUpdate(name="Jane Doe")
        >>> print(update_data.name)
        Jane Doe
        
        >>> update_data = UserUpdate(password="newpassword123")
        >>> print(len(update_data.password) >= 8)
        True
    """
    name: Optional[str] = Field(None, min_length=1, description="User's display name")
    password: Optional[str] = Field(None, min_length=8, description="User's password")

    @field_validator('name', 'password', mode='before')
    @classmethod
    def not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Validate that string fields are not empty or whitespace-only.
        
        Args:
            v: The value to validate
            
        Returns:
            The validated value or None
            
        Raises:
            ValueError: If the value is empty or contains only whitespace
        """
        if v is not None and not v.strip():
            raise ValueError('Field cannot be empty or contain only whitespace')
        return v


def validate_user_id(user_id: int) -> int:
    """Validate that a user ID is a positive integer.
    
    Args:
        user_id: The user ID to validate
        
    Returns:
        The validated user ID
        
    Raises:
        UserValidationError: If the user ID is not a positive integer
        
    Example:
        >>> validate_user_id(123)
        123
        >>> validate_user_id(-1)  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        UserValidationError: User ID must be a positive integer
    """
    if not isinstance(user_id, int) or user_id <= 0:
        raise UserValidationError("User ID must be a positive integer")
    return user_id
