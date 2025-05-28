from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from app.utils.enums import UserRole


class UserRegister(BaseModel):
	full_name: str 
	email: EmailStr
	password: str 
	confirm_password: str 
	province_id: int
	district_id: int
	hospital_id: int 

	@validator("confirm_password")
	def password_match(cls, v, values, **kwargs):
		if 'password' in values and v != values['password']:
			raise ValueError('Passwords do not match')
		return v 

	@validator('password')
	def validate_password(cls, v):
		if len(v) < 8:
			raise ValueError("Password must be at least 8 characters long")
		return v 

class UserLogin(BaseModel):
	email: EmailStr
	password: str 

class Token(BaseModel):
	access_token: str 
	refresh_token: str 
	token_type: str = "bearer"

class TokenData(BaseModel):
	user_id: Optional[int] = None
	email: Optional[str] = None

class UserInToken(BaseModel):
	id: int 
	email: str 
	full_name: str 
	role: UserRole 
	is_active: bool

class LoginResponse(BaseModel):
	success: bool = True
	message: str = "Login successful"
	data: dict