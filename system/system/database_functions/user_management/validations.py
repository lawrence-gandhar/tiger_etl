from typing import Optional
import re
from pydantic import BaseModel, Field, field_validator, ConfigDict, ValidationInfo

from system.system.database_functions.user_management.user_management_constants import (
    EMAIL_PATTERN,
    USERNAME_EMPTY_ERROR,
    USERNAME_FORMAT_ERROR,
    PASSWORD_LENGTH_ERROR,
    PASSWORD_UPPERCASE_ERROR,
    PASSWORD_LOWERCASE_ERROR,
    PASSWORD_DIGIT_ERROR,
    PASSWORD_SPECIAL_ERROR,
    PASSWORD_EMPTY_ERROR,
    NAME_FORMAT_ERROR,
    PASSWORD_MIN_LENGTH,
    PASSWORD_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
    USERNAME_MAX_LENGTH,
    NAME_MAX_LENGTH,
    NAME_PATTERN,
    PASSWORD_UPPERCASE_PATTERN,
    PASSWORD_LOWERCASE_PATTERN,
    PASSWORD_DIGIT_PATTERN,
    PASSWORD_SPECIAL_PATTERN,
)


class UserBase(BaseModel):
    """Base Pydantic model with common fields."""

    username: str = Field(
        ...,
        min_length=USERNAME_MIN_LENGTH,
        max_length=USERNAME_MAX_LENGTH,
        description="Email address used as username"
    )
    first_name: Optional[str] = Field(
        default=None,
        max_length=NAME_MAX_LENGTH,
        description="First name (optional)"
    )
    last_name: Optional[str] = Field(
        default=None,
        max_length=NAME_MAX_LENGTH,
        description="Last name (optional)"
    )
    is_active: bool = Field(default=True)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError(USERNAME_EMPTY_ERROR)
        v = v.strip().lower()
        if not re.match(EMAIL_PATTERN, v):
            raise ValueError(USERNAME_FORMAT_ERROR)
        return v

    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_names(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                return None
            if not re.match(NAME_PATTERN, v):
                raise ValueError(NAME_FORMAT_ERROR)
            return v.title()
        return v


class UserCreate(UserBase):
    """Model for creating new user with password + confirm_password validation."""

    passwd: str = Field(
        ...,
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
        description="Password"
    )
    confirm_passwd: str = Field(
        ...,
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
        description="Password confirmation"
    )

    # @field_validator('passwd')
    # @classmethod
    # def validate_password(cls, v: str) -> str:
    #     v = v.strip()
    #     if len(v) < PASSWORD_MIN_LENGTH:
    #         raise ValueError(PASSWORD_LENGTH_ERROR)
    #     if not re.search(PASSWORD_UPPERCASE_PATTERN, v):
    #         raise ValueError(PASSWORD_UPPERCASE_ERROR)
    #     if not re.search(PASSWORD_LOWERCASE_PATTERN, v):
    #         raise ValueError(PASSWORD_LOWERCASE_ERROR)
    #     if not re.search(PASSWORD_DIGIT_PATTERN, v):
    #         raise ValueError(PASSWORD_DIGIT_ERROR)
    #     if not re.search(PASSWORD_SPECIAL_PATTERN, v):
    #         raise ValueError(PASSWORD_SPECIAL_ERROR)
    #     return v

    # @field_validator('confirm_passwd')
    # @classmethod
    # def validate_confirm_password(cls, v: str, info: ValidationInfo) -> str:
    #     passwd = info.data.get("passwd")   # ✅ correct way in Pydantic v2
    #     if passwd and v.strip() != passwd:
    #         raise ValueError("Passwords do not match")
    #     return v.strip()


class UserUpdate(BaseModel):
    """Partial update model (all fields optional)."""

    username: Optional[str] = Field(None, min_length=USERNAME_MIN_LENGTH, max_length=USERNAME_MAX_LENGTH)
    passwd: Optional[str] = Field(None, min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
    first_name: Optional[str] = Field(None, max_length=NAME_MAX_LENGTH)
    last_name: Optional[str] = Field(None, max_length=NAME_MAX_LENGTH)
    is_active: Optional[bool] = None

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip().lower()
            if not re.match(EMAIL_PATTERN, v):
                raise ValueError(USERNAME_FORMAT_ERROR)
        return v

    @field_validator('passwd')
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if len(v) < PASSWORD_MIN_LENGTH:
                raise ValueError(PASSWORD_LENGTH_ERROR)
            if not re.search(PASSWORD_UPPERCASE_PATTERN, v):
                raise ValueError(PASSWORD_UPPERCASE_ERROR)
            if not re.search(PASSWORD_LOWERCASE_PATTERN, v):
                raise ValueError(PASSWORD_LOWERCASE_ERROR)
            if not re.search(PASSWORD_DIGIT_PATTERN, v):
                raise ValueError(PASSWORD_DIGIT_ERROR)
            if not re.search(PASSWORD_SPECIAL_PATTERN, v):
                raise ValueError(PASSWORD_SPECIAL_ERROR)
        return v

    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_names(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                return None
            if not re.match(NAME_PATTERN, v):
                raise ValueError(NAME_FORMAT_ERROR)
            return v.title()
        return v


class UserResponse(UserBase):
    """Response model (excludes password)."""
    id: int
    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """Model for login validation."""

    username: str = Field(..., min_length=USERNAME_MIN_LENGTH, max_length=USERNAME_MAX_LENGTH)
    passwd: str = Field(..., min_length=1)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError(USERNAME_EMPTY_ERROR)
        v = v.strip().lower()
        if not re.match(EMAIL_PATTERN, v):
            raise ValueError(USERNAME_FORMAT_ERROR)
        return v

    @field_validator('passwd')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError(PASSWORD_EMPTY_ERROR)
        return v.strip()
