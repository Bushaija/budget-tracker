from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import create_access_token, verify_password, get_password_hash
from app.schemas.auth import UserRegister, UserLogin, Token, LoginResponse
from app.services.auth_service import AuthService, generate_tokens
from app.services.user_service import UserService 
from app.core.config import settings


router = APIRouter(prefix="/auth", tags=["authentication"])

# TODO: use a consistent BaseResponse model here
@router.post("/register", response_model=dict)
async def register_user(
		user_data: UserRegister,
		session: Session = Depends(get_session)
	):
	"""register a new user"""
	auth_service = AuthService(session)
	user_service = UserService(session)

	# check if user already exists
	if await user_service.get_user_by_email(user_data.email):
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Email already registered"
		)

	# create user
	user = await auth_service.register_user(user_data)

	return {
		"success": True,
		"message": "User registered successfully",
		"data": {
			"user_id": user.id,
			"email": user.email,
			"full_name": user.full_name,
		}
	}

@router.post("/login", response_model=LoginResponse)
async def login_user(
		form_data: OAuth2PasswordRequestForm = Depends(),
		session: Session = Depends(get_session)
	):
	"""Login user and return JWT Tokens"""
	auth_service = AuthService(session)

	# authenticate user
	user = await auth_service.authenticate_user(form_data.username, form_data.password)

	if not user:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Incorrect email or password"
		)

	# create tokens
	tokens = AuthService.generate_tokens(user)

	return LoginResponse(
		data = {
			"token": tokens["access_token"],
			"refresh_token": tokens["refresh_token"],
			"token_type": "bearer",
			"user": {
				"id": user.id,
				"full_name": user.full_name,
				"email": user.email,
				"role": user.role,
				"province": user.province.name if user.province else None,
				"district": user.district.name if user.district else None,
				"hospital": user.hospital.name if user.hospital else None,
			}
		}
	)

@router.post("/logout")
async def logout_user(current_user: User = Depends(get_current_user)):
	"""logout user (client should discard token)"""
	return {"success": True, "message": "Logged out successfully"}

@router.post("/refresh")
async def refresh_token(current_user: User = Depends(get_current_user)):
	"""refresh access token"""
	tokens = AuthService.generate_tokens(current_user)
	return {
		"success": True,
		"data": {
			"access_token": tokens["access_token"],
			"refresh_token": tokens["refresh_token"],
			"token_type": "bearer"
		}
	}