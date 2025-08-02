"""User validation models using Pydantic.

This module contains Pydantic models for validating user data including
creation, updates, responses, and authentication.
"""

from typing import Optional
import re

from pydantic import BaseModel, Field, field_validator, ConfigDict

# Import constants from the constants module
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'constants'))

try:
    from constants import (
        USERNAME_EMPTY_ERROR,
        USERNAME_FORMAT_ERROR,
        USERNAME_START_ERROR,
        PASSWORD_LENGTH_ERROR,
        PASSWORD_UPPERCASE_ERROR,
        PASSWORD_LOWERCASE_ERROR,
        PASSWORD_DIGIT_ERROR,
        PASSWORD_SPECIAL_ERROR,
        PASSWORD_EMPTY_ERROR,
        NAME_FORMAT_ERROR,
    )
except ImportError:
    # Fallback constants if import fails
    USERNAME_EMPTY_ERROR = "Username cannot be empty"
    USERNAME_FORMAT_ERROR = "Username can only contain letters, numbers, underscores, and hyphens"
    USERNAME_START_ERROR = "Username cannot start with a number"
    PASSWORD_LENGTH_ERROR = "Password must be at least 8 characters long"
    PASSWORD_UPPERCASE_ERROR = "Password must contain at least one uppercase letter"
    PASSWORD_LOWERCASE_ERROR = "Password must contain at least one lowercase letter"
    PASSWORD_DIGIT_ERROR = "Password must contain at least one digit"
    PASSWORD_SPECIAL_ERROR = "Password must contain at least one special character"
    PASSWORD_EMPTY_ERROR = "Password cannot be empty"
    NAME_FORMAT_ERROR = "Names can only contain letters, spaces, hyphens, and apostrophes"


class UserBase(BaseModel):
    """Base Pydantic model for User with common fields.
    
    This model contains the common fields and validations that are shared
    across different user operations.
    
    Attributes:
        username: Unique username (3-50 characters)
        first_name: Optional first name (max 50 characters)
        last_name: Optional last name (max 50 characters)
        is_active: Boolean flag for user status (default: True)
    """
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username must be 3-50 characters"
    )
    first_name: Optional[str] = Field(
        default=None,
        max_length=50,
        description="First name (optional)"
    )
    last_name: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Last name (optional)"
    )
    is_active: bool = Field(
        default=True,
        description="User active status"
    )

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format and constraints.
        
        Args:
            v: The username string to validate
            
        Returns:
            str: Validated and normalized username (lowercase)
            
        Raises:
            ValueError: If username is empty, contains invalid characters,
                       or starts with a number
        """
        if not v:
            raise ValueError(USERNAME_EMPTY_ERROR)
        
        # Username should contain only alphanumeric characters, underscores, and hyphens
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError(USERNAME_FORMAT_ERROR)
        
        # Username should not start with a number
        if v[0].isdigit():
            raise ValueError(USERNAME_START_ERROR)
            
        return v.lower()  # Convert to lowercase for consistency

    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_names(cls, v: Optional[str]) -> Optional[str]:
        """Validate first_name and last_name fields.
        
        Args:
            v: The name string to validate (can be None)
            
        Returns:
            Optional[str]: Validated and normalized name (title case) or None
            
        Raises:
            ValueError: If name contains invalid characters
        """
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None  # Convert empty strings to None
            
            # Names should contain only letters, spaces, hyphens, and apostrophes
            if not re.match(r"^[a-zA-Z\s\-']+$", v):
                raise ValueError(NAME_FORMAT_ERROR)
                
            return v.title()  # Convert to title case
        return v


class UserCreate(UserBase):
    """Pydantic model for creating a new user.
    
    Extends UserBase with password field and validation for user creation.
    
    Attributes:
        passwd: Password field with strength validation
    """
    
    passwd: str = Field(
        ...,
        min_length=8,
        max_length=255,
        description="Password must be at least 8 characters"
    )

    @field_validator('passwd')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength requirements.
        
        Password must contain:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        
        Args:
            v: The password string to validate
            
        Returns:
            str: The validated password
            
        Raises:
            ValueError: If password doesn't meet strength requirements
        """
        if len(v) < 8:
            raise ValueError(PASSWORD_LENGTH_ERROR)
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', v):
            raise ValueError(PASSWORD_UPPERCASE_ERROR)
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', v):
            raise ValueError(PASSWORD_LOWERCASE_ERROR)
        
        # Check for at least one digit
        if not re.search(r'\d', v):
            raise ValueError(PASSWORD_DIGIT_ERROR)
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>\/?]', v):
            raise ValueError(PASSWORD_SPECIAL_ERROR)
        
        return v


class UserUpdate(BaseModel):
    """Pydantic model for updating an existing user.
    
    All fields are optional to allow partial updates.
    
    Attributes:
        username: Optional username update
        passwd: Optional password update
        first_name: Optional first name update
        last_name: Optional last name update
        is_active: Optional active status update
    """
    
    username: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=50,
        description="Username must be 3-50 characters"
    )
    passwd: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=255,
        description="Password must be at least 8 characters"
    )
    first_name: Optional[str] = Field(
        default=None,
        max_length=50,
        description="First name (optional)"
    )
    last_name: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Last name (optional)"
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="User active status"
    )
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        """Validate username format for updates.
        
        Args:
            v: The username string to validate (can be None)
            
        Returns:
            Optional[str]: Validated and normalized username or None
            
        Raises:
            ValueError: If username is provided but invalid
        """
        if v is not None:
            if not v:
                raise ValueError(USERNAME_EMPTY_ERROR)
            
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError(USERNAME_FORMAT_ERROR)
            
            if v[0].isdigit():
                raise ValueError(USERNAME_START_ERROR)
                
            return v.lower()
        return v
    
    @field_validator('passwd')
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        """Validate password strength for updates.
        
        Args:
            v: The password string to validate (can be None)
            
        Returns:
            Optional[str]: The validated password or None
            
        Raises:
            ValueError: If password is provided but doesn't meet requirements
        """
        if v is not None:
            if len(v) < 8:
                raise ValueError(PASSWORD_LENGTH_ERROR)
            
            if not re.search(r'[A-Z]', v):
                raise ValueError(PASSWORD_UPPERCASE_ERROR)
            
            if not re.search(r'[a-z]', v):
                raise ValueError(PASSWORD_LOWERCASE_ERROR)
            
            if not re.search(r'\d', v):
                raise ValueError(PASSWORD_DIGIT_ERROR)
            
            if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>\/?]', v):
                raise ValueError(PASSWORD_SPECIAL_ERROR)
        
        return v
    
    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_names(cls, v: Optional[str]) -> Optional[str]:
        """Validate name fields for updates.
        
        Args:
            v: The name string to validate (can be None)
            
        Returns:
            Optional[str]: Validated and normalized name or None
            
        Raises:
            ValueError: If name is provided but contains invalid characters
        """
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
            
            if not re.match(r"^[a-zA-Z\s\-']+$", v):
                raise ValueError(NAME_FORMAT_ERROR)
                
            return v.title()
        return v


class UserResponse(UserBase):
    """Pydantic model for user response data.
    
    Used for API responses, excludes sensitive data like passwords.
    
    Attributes:
        id: User's unique identifier
        Inherits all fields from UserBase
    """
    
    id: int = Field(..., description="User's unique identifier")
    
    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """Pydantic model for user authentication.
    
    Simple model for login credentials validation.
    
    Attributes:
        username: Username for authentication
        passwd: Password for authentication
    """
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username for authentication"
    )
    passwd: str = Field(
        ...,
        min_length=1,
        description="Password for authentication"
    )

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username for login.
        
        Args:
            v: The username string to validate
            
        Returns:
            str: Normalized username (lowercase)
            
        Raises:
            ValueError: If username is empty
        """
        if not v:
            raise ValueError(USERNAME_EMPTY_ERROR)
        return v.lower()

    @field_validator('passwd')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password for login.
        
        Args:
            v: The password string to validate
            
        Returns:
            str: The password (unchanged)
            
        Raises:
            ValueError: If password is empty
        """
        if not v:
            raise ValueError(PASSWORD_EMPTY_ERROR)
        return v
