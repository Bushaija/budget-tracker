from typing import List, Optional, Tuple
from sqlmodel import Session
import math

from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.models import Users, UserRole


class UserService:
    def __init__(self):
        self.auth_service = AuthService()

    def create_user(self, db: Session, user_data: UserCreate) -> Optional[UserResponse]:
        """Create a new user."""
        user_repo = UserRepository(db)
        
        # Check if email already exists
        if user_repo.exists_by_email(user_data.email):
            raise ValueError("Email already registered")

        # Hash password
        password_hash = self.auth_service.get_password_hash(user_data.password)
        
        # Create user
        user = user_repo.create(user_data, password_hash)
        return self._convert_to_response(user)

    def get_user_by_id(self, db: Session, user_id: int) -> Optional[UserResponse]:
        """Get user by ID."""
        user_repo = UserRepository(db)
        user = user_repo.get_by_id(user_id)
        
        if not user:
            return None
            
        return self._convert_to_response(user)

    def get_user_by_email(self, db: Session, email: str) -> Optional[UserResponse]:
        """Get user by email."""
        user_repo = UserRepository(db)
        user = user_repo.get_by_email(email)
        
        if not user:
            return None
            
        return self._convert_to_response(user)

    def update_user(
        self, 
        db: Session, 
        user_id: int, 
        user_data: UserUpdate,
        current_user: Users
    ) -> Optional[UserResponse]:
        """Update user data."""
        user_repo = UserRepository(db)
        
        # Check if user exists
        existing_user = user_repo.get_by_id(user_id)
        if not existing_user:
            return None

        # Authorization check
        if not self._can_modify_user(current_user, existing_user):
            raise PermissionError("Not authorized to modify this user")

        # Check email uniqueness if email is being updated
        if user_data.email and user_repo.exists_by_email(user_data.email, exclude_id=user_id):
            raise ValueError("Email already registered")

        # Update user
        updated_user = user_repo.update(user_id, user_data)
        return self._convert_to_response(updated_user) if updated_user else None

    def delete_user(self, db: Session, user_id: int, current_user: Users) -> bool:
        """Soft delete user."""
        user_repo = UserRepository(db)
        
        # Check if user exists
        existing_user = user_repo.get_by_id(user_id)
        if not existing_user:
            return False

        # Prevent self-deletion
        if existing_user.id == current_user.id:
            raise ValueError("Cannot delete your own account")

        # Authorization check
        if not self._can_modify_user(current_user, existing_user):
            raise PermissionError("Not authorized to delete this user")

        return user_repo.delete(user_id)

    def get_users_list(
        self,
        db: Session,
        page: int = 1,
        size: int = 20,
        facility_id: Optional[int] = None,
        district_id: Optional[int] = None,
        province_id: Optional[int] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        current_user: Users = None
    ) -> UserListResponse:
        """Get paginated list of users with filtering."""
        user_repo = UserRepository(db)
        
        # Apply authorization filters
        if current_user and current_user.role != UserRole.ADMIN:
            # Non-admin users can only see users from their facility/district/province
            if current_user.role == UserRole.MANAGER:
                # Managers can see users from their district
                if district_id is None:
                    district_id = current_user.district_id
                elif district_id != current_user.district_id:
                    # Restrict to their district if they try to access another
                    district_id = current_user.district_id
            else:
                # Accountants can only see users from their facility
                if facility_id is None:
                    facility_id = current_user.facility_id
                elif facility_id != current_user.facility_id:
                    # Restrict to their facility if they try to access another
                    facility_id = current_user.facility_id

        # Calculate pagination
 
        skip = (page - 1) * size
        
        # Get users and total count
        users, total = user_repo.get_all(
            skip=skip,
            limit=size,
            facility_id=facility_id,
            district_id=district_id,
            province_id=province_id,
            role=role,
            is_active=is_active,
            search=search
        )
     

        # Convert to response objects
        user_responses = [self._convert_to_response(user) for user in users]
        print("user_responses", user_responses)
        # Calculate total pages
        total_pages = math.ceil(total / size) if total > 0 else 1

        return UserListResponse(
            users=user_responses,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages
        )

    def change_user_password(
        self, 
        db: Session, 
        user_id: int, 
        current_password: str, 
        new_password: str,
        current_user: Users
    ) -> bool:
        """Change user password."""
        # Users can only change their own password unless they're admin
        if current_user.id != user_id and current_user.role != UserRole.ADMIN:
            raise PermissionError("Not authorized to change this user's password")

        return self.auth_service.change_password(db, user_id, current_password, new_password)

    def get_users_by_facility(self, db: Session, facility_id: int) -> List[UserResponse]:
        """Get all users in a facility."""
        user_repo = UserRepository(db)
        users = user_repo.get_users_by_facility(facility_id)
        return [self._convert_to_response(user) for user in users]

    def get_users_by_district(self, db: Session, district_id: int) -> List[UserResponse]:
        """Get all users in a district."""
        user_repo = UserRepository(db)
        users = user_repo.get_users_by_district(district_id)
        return [self._convert_to_response(user) for user in users]

    def get_admin_users(self, db: Session) -> List[UserResponse]:
        """Get all admin users."""
        user_repo = UserRepository(db)
        users = user_repo.get_admins()
        return [self._convert_to_response(user) for user in users]

    def activate_user(self, db: Session, user_id: int, current_user: Users) -> bool:
        """Activate a user account."""
        user_repo = UserRepository(db)
        
        # Check if user exists
        existing_user = user_repo.get_by_id(user_id)
        if not existing_user:
            return False

        # Authorization check
        if not self._can_modify_user(current_user, existing_user):
            raise PermissionError("Not authorized to activate this user")

        # Update user status
        update_data = UserUpdate(is_active=True)
        updated_user = user_repo.update(user_id, update_data)
        return updated_user is not None

    def deactivate_user(self, db: Session, user_id: int, current_user: Users) -> bool:
        """Deactivate a user account."""
        user_repo = UserRepository(db)
        
        # Check if user exists
        existing_user = user_repo.get_by_id(user_id)
        if not existing_user:
            return False

        # Prevent self-deactivation
        if existing_user.id == current_user.id:
            raise ValueError("Cannot deactivate your own account")

        # Authorization check
        if not self._can_modify_user(current_user, existing_user):
            raise PermissionError("Not authorized to deactivate this user")

        # Update user status
        update_data = UserUpdate(is_active=False)
        updated_user = user_repo.update(user_id, update_data)
        return updated_user is not None

    def _convert_to_response(self, user: Users) -> UserResponse:
        print("user", user)
        """Convert User model to UserResponse."""
        return UserResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            province_id=user.province_id,
            district_id=user.district_id,
            facility_id=user.facility_id,
            role=user.role,
            is_active=user.is_active,
            updated_at=user.updated_at,
            created_at=user.created_at if user.created_at else None,

            
            province_name=user.province.name if user.province else None,
            district_name=user.district.name if user.district else None,
            facility_name=user.facility.name if user.facility else None,
            facility_type=user.facility.facility_type.value if user.facility else None
        )

    def _can_modify_user(self, current_user: Users, target_user: Users) -> bool:
        """Check if current user can modify target user."""
        # Admins can modify anyone
        if current_user.role == UserRole.ADMIN:
            return True
        
        # Managers can modify users in their district (except other managers and admins)
        if current_user.role == UserRole.MANAGER:
            return (
                current_user.district_id == target_user.district_id and
                target_user.role == UserRole.ACCOUNTANT
            )
        
        # Accountants can only modify themselves
        if current_user.role == UserRole.ACCOUNTANT:
            return current_user.id == target_user.id
        
        return False