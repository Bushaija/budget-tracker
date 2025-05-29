# from typing import Optional
# from datetime import timedelta

# from sqlmodel import Session, select

# from app.core.security import create_access_token
# from app.core.config import settings
# from app.models.user import User
# from app.schemas.auth import UserRegister, UserLogin
# from app.core.security import verify_password, get_password_hash
# from app.repositories.user_repository import userRepository


# class AuthService:
# 	def __init__(self, session: Session):
# 		self.session = session
# 		self.user_repo = userRepository(session)

# 	async def authenticate_user(self, email: str, password: str) -> Optional[User]:
# 		"""Authenticate user with email and password"""
# 		user = await self.user_repo.get_by_email(email)

# 		# TODO: raise custom exception instead of returning None
# 		if not user:
# 			return None
# 		if not verify_password(password, user.password_hash):
# 			return None
# 		if not user.is_active:
# 			return None 
# 		return user 


# 	async def register_user(self, user_data: UserRegister) -> User:
# 		"""register a new user"""
# 		password_hash = get_password_hash(user_data.password)

# 		user = User(
# 			full_name = user_data.full_name,
# 			email = user_data.email,
# 			password_hash = password_hash,
# 			province_id = user_data.province_id,
# 			district_id = user_data.district_id,
# 			hospital_id = user_data.hospital_id
# 		)

# 		return await self.user_repo.create(user)

# 	async def log_login_attempt(self, user_id: int, ip: str, user_agent: str, success: bool):
# 		login = UserLogin(
# 			user_id=user_id,
# 			ip_address=ip,
# 			user_agent=user_agent,
# 			success=success
# 		)
# 		self.session.add(login)
# 		await self.session.commit()

# 	async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
# 		"""Change user password"""
# 		user = await self.user_repo.get_by_id(user_id)
# 		if not user or not verify_password(old_password, user.password_hash):
# 			return False

# 		user.password_hash = get_password_hash(new_password)
# 		await self.user_repo.update(user)
# 		return True


# 	@staticmethod
# 	def generate_tokens(user: User) -> dict:
# 		access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
# 		refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

# 		access_token = create_access_token(
# 			data={"sub": user.email, "user_id": str(user.id)},
# 			expires_delta=access_token_expires
# 		)
# 		refresh_token = create_access_token(
# 			data={"sub": user.email, "user_id": str(user.id)},
# 			expires_delta=refresh_token_expires
# 		)

# 		return {
# 			"access_token": access_token,
# 			"refresh_token": refresh_token,
# 			"token_type": "bearer"
# 		}


import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session

from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, LoginResponse, UserTokenData, TokenData
from app.models import Users


class AuthService:
    def __init__(self):
        # JWT Configuration
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        
        # Password hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return self.pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            email: str = payload.get("sub")
            user_id: int = payload.get("user_id")
            
            if email is None or user_id is None:
                return None
                
            return TokenData(email=email, user_id=user_id)
        except JWTError:
            return None

    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[Users]:
        """Authenticate a user with email and password."""
        user_repo = UserRepository(db)
        user = user_repo.get_active_by_email(email)
        
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
            
        return user

    def login(self, db: Session, login_data: LoginRequest) -> Optional[LoginResponse]:
        """Login a user and return access token."""
        user = self.authenticate_user(db, login_data.email, login_data.password)
        if not user:
            return None

        # Create access token
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        access_token = self.create_access_token(
            data={"sub": user.email, "user_id": user.id},
            expires_delta=access_token_expires
        )

        # Create user token data
        user_token_data = UserTokenData(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            facility_id=user.facility_id,
            facility_name=user.facility.name if user.facility else "",
            facility_type=user.facility.facility_type.value if user.facility else "",
            district_id=user.district_id,
            district_name=user.district.name if user.district else "",
            province_id=user.province_id,
            province_name=user.province.name if user.province else "",
            is_active=user.is_active
        )

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60,  # Convert to seconds
            user=user_token_data
        )

    def get_current_user(self, db: Session, token: str) -> Optional[Users]:
        """Get current user from JWT token."""
        token_data = self.verify_token(token)
        if token_data is None:
            return None

        user_repo = UserRepository(db)
        user = user_repo.get_active_by_email(token_data.email)
        
        if user is None:
            return None
            
        return user

    def change_password(
        self, 
        db: Session, 
        user_id: int, 
        current_password: str, 
        new_password: str
    ) -> bool:
        """Change user password after verifying current password."""
        user_repo = UserRepository(db)
        user = user_repo.get_by_id(user_id)
        
        if not user:
            return False
            
        # Verify current password
        if not self.verify_password(current_password, user.password_hash):
            return False
            
        # Hash new password and update
        new_password_hash = self.get_password_hash(new_password)
        return user_repo.update_password(user_id, new_password_hash)

    def create_password_reset_token(self, email: str) -> str:
        """Create a password reset token (expires in 1 hour)."""
        expire = datetime.utcnow() + timedelta(hours=1)
        to_encode = {"sub": email, "exp": expire, "type": "password_reset"}
        
        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return token

    def verify_password_reset_token(self, token: str) -> Optional[str]:
        """Verify password reset token and return email."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            email: str = payload.get("sub")
            token_type: str = payload.get("type")
            
            if email is None or token_type != "password_reset":
                return None
                
            return email
        except JWTError:
            return None

    def reset_password(self, db: Session, token: str, new_password: str) -> bool:
        """Reset password using reset token."""
        email = self.verify_password_reset_token(token)
        if not email:
            return False

        user_repo = UserRepository(db)
        user = user_repo.get_by_email(email)
        if not user:
            return False

        # Hash new password and update
        new_password_hash = self.get_password_hash(new_password)
        return user_repo.update_password(user.id, new_password_hash)