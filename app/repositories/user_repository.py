from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select, func, and_
from sqlalchemy.orm import selectinload

from app.models import Users, Provinces, Districts, Facilities
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[Users]:
        """Get user by ID with related data."""
        statement = (
            select(Users)
            .options(
                selectinload(Users.province),
                selectinload(Users.district),
                selectinload(Users.facility)
            )
            .where(Users.id == user_id)
        )
        return self.db.exec(statement).first()

    def get_by_email(self, email: str) -> Optional[Users]:
        """Get user by email with related data."""
        statement = (
            select(Users)
            .options(
                selectinload(Users.province),
                selectinload(Users.district),
                selectinload(Users.facility)
            )
            .where(Users.email == email)
        )
        return self.db.exec(statement).first()

    def get_active_by_email(self, email: str) -> Optional[Users]:
        """Get active user by email."""
        statement = (
            select(Users)
            .options(
                selectinload(Users.province),
                selectinload(Users.district),
                selectinload(Users.facility)
            )
            .where(and_(Users.email == email, Users.is_active == True))
        )
        return self.db.exec(statement).first()

    def create(self, user_data: UserCreate, password_hash: str) -> Users:
        """Create a new user."""
        user = Users(
            full_name=user_data.full_name,
            email=user_data.email,
            password_hash=password_hash,
            province_id=user_data.province_id,
            district_id=user_data.district_id,
            facility_id=user_data.facility_id,
            role=user_data.role,
            is_active=user_data.is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return self.get_by_id(user.id)

    def update(self, user_id: int, user_data: UserUpdate) -> Optional[Users]:
        """Update user data."""
        user = self.db.get(Users, user_id)
        if not user:
            return None

        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return self.get_by_id(user.id)

    def update_password(self, user_id: int, password_hash: str) -> bool:
        """Update user password."""
        user = self.db.get(Users, user_id)
        if not user:
            return False

        user.password_hash = password_hash
        user.updated_at = datetime.utcnow()
        self.db.add(user)
        self.db.commit()
        return True

    def delete(self, user_id: int) -> bool:
        """Soft delete user by setting is_active to False."""
        user = self.db.get(Users, user_id)
        if not user:
            return False

        user.is_active = False
        user.updated_at = datetime.utcnow()
        self.db.add(user)
        self.db.commit()
        return True

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        facility_id: Optional[int] = None,
        district_id: Optional[int] = None,
        province_id: Optional[int] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> tuple[List[Users], int]:
        """Get all users with filtering and pagination."""
        # Base query with joins
        query = (
            select(Users)
            .options(
                selectinload(Users.province),
                selectinload(Users.district),
                selectinload(Users.facility)
            )
        )

        # Apply filters
        conditions = []
        
        if facility_id is not None:
            conditions.append(Users.facility_id == facility_id)
        if district_id is not None:
            conditions.append(Users.district_id == district_id)
        if province_id is not None:
            conditions.append(Users.province_id == province_id)
        if role is not None:
            conditions.append(Users.role == role)
        if is_active is not None:
            conditions.append(Users.is_active == is_active)
        if search:
            search_pattern = f"%{search}%"
            conditions.append(
                Users.full_name.ilike(search_pattern) | 
                Users.email.ilike(search_pattern)
            )

        if conditions:
            query = query.where(and_(*conditions))

        # Get total count
        count_query = select(func.count(Users.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total = self.db.exec(count_query).one()

        # Apply pagination and ordering
        query = query.order_by(Users.created_at.desc()).offset(skip).limit(limit)
        users = self.db.exec(query).all()

        return users, total

    def exists_by_email(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """Check if user exists by email."""
        query = select(Users.id).where(Users.email == email)
        if exclude_id:
            query = query.where(Users.id != exclude_id)
        
        result = self.db.exec(query).first()
        return result is not None

    def get_users_by_facility(self, facility_id: int) -> List[Users]:
        """Get all users in a facility."""
        statement = (
            select(Users)
            .options(
                selectinload(Users.province),
                selectinload(Users.district),
                selectinload(Users.facility)
            )
            .where(and_(Users.facility_id == facility_id, Users.is_active == True))
            .order_by(Users.full_name)
        )
        return self.db.exec(statement).all()

    def get_users_by_district(self, district_id: int) -> List[Users]:
        """Get all users in a district."""
        statement = (
            select(Users)
            .options(
                selectinload(Users.province),
                selectinload(Users.district),
                selectinload(Users.facility)
            )
            .where(and_(Users.district_id == district_id, Users.is_active == True))
            .order_by(Users.full_name)
        )
        return self.db.exec(statement).all()

    def get_admins(self) -> List[Users]:
        """Get all admin users."""
        statement = (
            select(Users)
            .options(
                selectinload(Users.province),
                selectinload(Users.district),
                selectinload(Users.facility)
            )
            .where(and_(Users.role == "admin", Users.is_active == True))
            .order_by(Users.full_name)
        )
        return self.db.exec(statement).all()