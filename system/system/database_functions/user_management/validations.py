from pydantic import BaseModel, EmailStr, constr, validator
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    name: constr(min_length=1)
    password: constr(min_length=8)

class UserUpdate(BaseModel):
    name: Optional[constr(min_length=1)]
    password: Optional[constr(min_length=8)]

    @validator('name', 'password', pre=True, always=True)
    def not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Field cannot be empty')
        return v
