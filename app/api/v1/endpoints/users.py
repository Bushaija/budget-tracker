from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session

from app.core.database import get_session
from app.services.user_service import UserService
from app.schemas.user import (
    UserCreate, 
    UserUpdate, 
    UserResponse, 
    UserListResponse,
    UserChangePassword
)
from app.models import Users, UserRole
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter(prefix="/users", tags=["User Management"])
user_service = UserService()


def require_admin(current_user: Users = Depends(get_current_user)) -> Users:
    """Dependency that requires admin role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_manager_or_admin(current_user: Users = Depends(get_current_user)) -> Users:
    """Dependency that requires manager or admin role."""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager or Admin access required"
        )
    return current_user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_session),
    current_user: Users = Depends(require_admin)
):
    """
    Create a new user. (Admin only)
    """
    try:
        user = user_service.create_user(db, user_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )
        return user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get("/", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    facility_id: Optional[int] = Query(None, description="Filter by facility ID"),
    district_id: Optional[int] = Query(None, description="Filter by district ID"),
    province_id: Optional[int] = Query(None, description="Filter by province ID"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    db: Session = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    """
    Get paginated list of users with filtering.
    Access is role-based:
    - Admin: Can see all users
    - Manager: Can see users in their district
    - Accountant: Can see users in their facility
    """
    try:
        return user_service.get_users_list(
            db=db,
            page=page,
            size=size,
            facility_id=facility_id,
            district_id=district_id,
            province_id=province_id,
            role=role,
            is_active=is_active,
            search=search,
            current_user=current_user
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    """
    Get user by ID.
    Users can access their own data, managers can access users in their district,
    admins can access any user.
    """
    try:
        user = user_service.get_user_by_id(db, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Authorization check
        if not _can_access_user(current_user, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this user"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    """
    Update user data.
    Authorization based on role hierarchy.
    """
    try:
        user = user_service.update_user(db, user_id, user_data, current_user)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    """
    Soft delete user (deactivate).
    Authorization based on role hierarchy.
    """
    try:
        success = user_service.delete_user(db, user_id, current_user)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "User deleted successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


@router.post("/{user_id}/change-password")
async def change_user_password(
    user_id: int,
    password_data: UserChangePassword,
    db: Session = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    """
    Change user password.
    Users can change their own password, admins can change any password.
    """
    try:
        success = user_service.change_user_password(
            db=db,
            user_id=user_id,
            current_password=password_data.current_password,
            new_password=password_data.new_password,
            current_user=current_user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        return {"message": "Password changed successfully"}
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    db: Session = Depends(get_session),
    current_user: Users = Depends(require_manager_or_admin)
):
    """
    Activate user account. (Manager/Admin only)
    """
    try:
        success = user_service.activate_user(db, user_id, current_user)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "User activated successfully"}
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate user"
        )


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    db: Session = Depends(get_session),
    current_user: Users = Depends(require_manager_or_admin)
):
    """
    Deactivate user account. (Manager/Admin only)
    """
    try:
        success = user_service.deactivate_user(db, user_id, current_user)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "User deactivated successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )


@router.get("/facility/{facility_id}", response_model=List[UserResponse])
async def get_users_by_facility(
    facility_id: int,
    db: Session = Depends(get_session),
    current_user: Users = Depends(require_manager_or_admin)
):
    """
    Get all users in a specific facility. (Manager/Admin only)
    """
    try:
        # Authorization check for managers
        if current_user.role == UserRole.MANAGER:
            # Managers can only access facilities in their district
            # You might want to add a check here to ensure the facility
            # belongs to the manager's district
            pass
        
        users = user_service.get_users_by_facility(db, facility_id)
        return users
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/district/{district_id}", response_model=List[UserResponse])
async def get_users_by_district(
    district_id: int,
    db: Session = Depends(get_session),
    current_user: Users = Depends(require_manager_or_admin)
):
    """
    Get all users in a specific district. (Manager/Admin only)
    """
    try:
        # Authorization check for managers
        if current_user.role == UserRole.MANAGER and current_user.district_id != district_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only access users in your own district"
            )
        
        users = user_service.get_users_by_district(db, district_id)
        return users
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/admin/all", response_model=List[UserResponse])
async def get_admin_users(
    db: Session = Depends(get_session),
    current_user: Users = Depends(require_admin)
):
    """
    Get all admin users. (Admin only)
    """
    try:
        users = user_service.get_admin_users(db)
        return users
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve admin users"
        )


def _can_access_user(current_user: Users, target_user: UserResponse) -> bool:
    """Check if current user can access target user data."""
    # Users can access their own data
    if current_user.id == target_user.id:
        return True
    
    # Admins can access anyone
    if current_user.role == UserRole.ADMIN:
        return True
    
    # Managers can access users in their district
    if current_user.role == UserRole.MANAGER:
        return current_user.district_id == target_user.district_id
    
    # Accountants can only access their own data (already checked above)
    return False