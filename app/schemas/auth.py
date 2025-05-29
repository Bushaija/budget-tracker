# from pydantic import BaseModel, EmailStr, validator
# from typing import Optional
# from app.utils.enums import UserRole


# class UserRegister(BaseModel):
# 	full_name: str 
# 	email: EmailStr
# 	password: str 
# 	confirm_password: str 
# 	province_id: int
# 	district_id: int
# 	hospital_id: int 

# 	@validator("confirm_password")
# 	def password_match(cls, v, values, **kwargs):
# 		if 'password' in values and v != values['password']:
# 			raise ValueError('Passwords do not match')
# 		return v 

# 	@validator('password')
# 	def validate_password(cls, v):
# 		if len(v) < 8:
# 			raise ValueError("Password must be at least 8 characters long")
# 		return v 

# class UserLogin(BaseModel):
# 	email: EmailStr
# 	password: str 

# class Token(BaseModel):
# 	access_token: str 
# 	refresh_token: str 
# 	token_type: str = "bearer"

# class TokenData(BaseModel):
# 	user_id: Optional[int] = None
# 	email: Optional[str] = None

# class UserInToken(BaseModel):
# 	id: int 
# 	email: str 
# 	full_name: str 
# 	role: UserRole 
# 	is_active: bool

# class LoginResponse(BaseModel):
# 	success: bool = True
# 	message: str = "Login successful"
# 	data: dict


# ==========

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserTokenData"


class UserTokenData(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    facility_id: int
    facility_name: str
    facility_type: str
    district_id: int
    district_name: str
    province_id: int
    province_name: str
    is_active: bool


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordResetResponse(BaseModel):
    message: str
    
    
# Update forward reference
LoginResponse.model_rebuild()