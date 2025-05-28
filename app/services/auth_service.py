from typing import Optional
from datetime import timedelta

from sqlmodel import Session, select

from app.core.security import create_access_token
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin
from app.core.security import verify_password, get_password_hash
from app.repositories.user_repository import userRepository


class AuthService:
	def __init__(self, session: Session):
		self.session = session
		self.user_repo = userRepository(session)

	async def authenticate_user(self, email: str, password: str) -> Optional[User]:
		"""Authenticate user with email and password"""
		user = await self.user_repo.get_by_email(email)

		# TODO: raise custom exception instead of returning None
		if not user:
			return None
		if not verify_password(password, user.password_hash):
			return None
		if not user.is_active:
			return None 
		return user 


	async def register_user(self, user_data: UserRegister) -> User:
		"""register a new user"""
		password_hash = get_password_hash(user_data.password)

		user = User(
			full_name = user_data.full_name,
			email = user_data.email,
			password_hash = password_hash,
			province_id = user_data.province_id,
			district_id = user_data.district_id,
			hospital_id = user_data.hospital_id
		)

		return await self.user_repo.create(user)

	async def log_login_attempt(self, user_id: int, ip: str, user_agent: str, success: bool):
		login = UserLogin(
			user_id=user_id,
			ip_address=ip,
			user_agent=user_agent,
			success=success
		)
		self.session.add(login)
		await self.session.commit()

	async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
		"""Change user password"""
		user = await self.user_repo.get_by_id(user_id)
		if not user or not verify_password(old_password, user.password_hash):
			return False

		user.password_hash = get_password_hash(new_password)
		await self.user_repo.update(user)
		return True


	@staticmethod
	def generate_tokens(user: User) -> dict:
		access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
		refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

		access_token = create_access_token(
			data={"sub": user.email, "user_id": str(user.id)},
			expires_delta=access_token_expires
		)
		refresh_token = create_access_token(
			data={"sub": user.email, "user_id": str(user.id)},
			expires_delta=refresh_token_expires
		)

		return {
			"access_token": access_token,
			"refresh_token": refresh_token,
			"token_type": "bearer"
		}