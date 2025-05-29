from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models import UserRole


class UserBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    province_id: int = Field(..., gt=0)
    district_id: int = Field(..., gt=0)
    facility_id: int = Field(..., gt=0)
    role: UserRole = UserRole.ACCOUNTANT
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    province_id: Optional[int] = Field(None, gt=0)
    district_id: Optional[int] = Field(None, gt=0)
    facility_id: Optional[int] = Field(None, gt=0)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserChangePassword(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    # Related data
    province_name: Optional[str] = None
    district_name: Optional[str] = None
    facility_name: Optional[str] = None
    facility_type: Optional[str] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
    page: int
    size: int
    total_pages: int