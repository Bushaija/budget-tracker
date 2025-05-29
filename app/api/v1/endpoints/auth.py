# from datetime import timedelta
# from fastapi import APIRouter, Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordRequestForm
# from sqlmodel import Session

# from app.core.database import get_session
# from app.core.security import create_access_token, verify_password, get_password_hash
# from app.schemas.auth import UserRegister, UserLogin, Token, LoginResponse
# from app.services.auth_service import AuthService, generate_tokens
# from app.services.user_service import UserService 
# from app.core.config import settings


# router = APIRouter(prefix="/auth", tags=["authentication"])

# # TODO: use a consistent BaseResponse model here
# @router.post("/register", response_model=dict)
# async def register_user(
# 		user_data: UserRegister,
# 		session: Session = Depends(get_session)
# 	):
# 	"""register a new user"""
# 	auth_service = AuthService(session)
# 	user_service = UserService(session)

# 	# check if user already exists
# 	if await user_service.get_user_by_email(user_data.email):
# 		raise HTTPException(
# 			status_code=status.HTTP_400_BAD_REQUEST,
# 			detail="Email already registered"
# 		)

# 	# create user
# 	user = await auth_service.register_user(user_data)

# 	return {
# 		"success": True,
# 		"message": "User registered successfully",
# 		"data": {
# 			"user_id": user.id,
# 			"email": user.email,
# 			"full_name": user.full_name,
# 		}
# 	}

# @router.post("/login", response_model=LoginResponse)
# async def login_user(
# 		form_data: OAuth2PasswordRequestForm = Depends(),
# 		session: Session = Depends(get_session)
# 	):
# 	"""Login user and return JWT Tokens"""
# 	auth_service = AuthService(session)

# 	# authenticate user
# 	user = await auth_service.authenticate_user(form_data.username, form_data.password)

# 	if not user:
# 		raise HTTPException(
# 			status_code=status.HTTP_401_UNAUTHORIZED,
# 			detail="Incorrect email or password"
# 		)

# 	# create tokens
# 	tokens = AuthService.generate_tokens(user)

# 	return LoginResponse(
# 		data = {
# 			"token": tokens["access_token"],
# 			"refresh_token": tokens["refresh_token"],
# 			"token_type": "bearer",
# 			"user": {
# 				"id": user.id,
# 				"full_name": user.full_name,
# 				"email": user.email,
# 				"role": user.role,
# 				"province": user.province.name if user.province else None,
# 				"district": user.district.name if user.district else None,
# 				"hospital": user.hospital.name if user.hospital else None,
# 			}
# 		}
# 	)

# @router.post("/logout")
# async def logout_user(current_user: User = Depends(get_current_user)):
# 	"""logout user (client should discard token)"""
# 	return {"success": True, "message": "Logged out successfully"}

# @router.post("/refresh")
# async def refresh_token(current_user: User = Depends(get_current_user)):
# 	"""refresh access token"""
# 	tokens = AuthService.generate_tokens(current_user)
# 	return {
# 		"success": True,
# 		"data": {
# 			"access_token": tokens["access_token"],
# 			"refresh_token": tokens["refresh_token"],
# 			"token_type": "bearer"
# 		}
# 	}


from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session

from app.core.database import get_session
from app.services.auth_service import AuthService
from app.schemas.auth import (
    LoginRequest, 
    LoginResponse, 
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    PasswordResetResponse
)
from app.models import Users

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()
auth_service = AuthService()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_session)
) -> Users:
    """Dependency to get current authenticated user."""
    token = credentials.credentials
    user = auth_service.get_current_user(db, token)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_session)
):
    """
    Authenticate user and return access token.
    """
    try:
        result = auth_service.login(db, login_data)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Change current user's password.
    """
    try:
        success = auth_service.change_password(
            db=db,
            user_id=current_user.id,
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        return {"message": "Password changed successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_session)
):
    """
    Request password reset token (to be sent via email).
    """
    try:
        # Create password reset token
        token = auth_service.create_password_reset_token(request.email)
        
        # TODO: Send email with reset token
        # For now, we'll just return success message
        # In production, you should send the token via email
        
        return PasswordResetResponse(
            message="Password reset instructions have been sent to your email"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password reset request"
        )


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_session)
):
    """
    Reset password using reset token.
    """
    try:
        success = auth_service.reset_password(
            db=db,
            token=request.token,
            new_password=request.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        return PasswordResetResponse(
            message="Password has been reset successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )


@router.get("/me")
async def get_current_user_info(
    current_user: Users = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "facility_id": current_user.facility_id,
        "facility_name": current_user.facility.name if current_user.facility else None,
        "facility_type": current_user.facility.facility_type.value if current_user.facility else None,
        "district_id": current_user.district_id,
        "district_name": current_user.district.name if current_user.district else None,
        "province_id": current_user.province_id,
        "province_name": current_user.province.name if current_user.province else None,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at
    }


@router.post("/verify-token")
async def verify_token(
    current_user: Users = Depends(get_current_user)
):
    """
    Verify if the provided token is valid.
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email
    }