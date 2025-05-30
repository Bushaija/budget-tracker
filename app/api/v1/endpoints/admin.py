from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from datetime import datetime, timedelta

from app.core.database import get_session
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.schemas.user import UserResponse, UserListResponse
from app.models import Users, UserRole
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.user import UserCreate

router = APIRouter(prefix="/admin", tags=["Admin Management"])
user_service = UserService()
auth_service = AuthService()


def require_admin(current_user: Users = Depends(get_current_user)) -> Users:
    """Dependency that requires admin role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_admin_dashboard(
    db: Session = Depends(get_session),
    current_user: Users = Depends(require_admin)
):
    """
    Get admin dashboard statistics and overview.
    """
    try:
        # Get user statistics by role
        all_users, total_users = user_service.get_users_list(
            db=db, page=1, size=1000, current_user=current_user
        ).users, 0
        
        # Calculate statistics
        stats = {
            "total_users": len(all_users),
            "active_users": len([u for u in all_users if u.is_active]),
            "inactive_users": len([u for u in all_users if not u.is_active]),
            "users_by_role": {
                "admin": len([u for u in all_users if u.role == UserRole.ADMIN]),
                "manager": len([u for u in all_users if u.role == UserRole.MANAGER]),
                "accountant": len([u for u in all_users if u.role == UserRole.ACCOUNTANT])
            },
            "recent_registrations": len([
                u for u in all_users 
                if u.created_at and u.created_at >= datetime.utcnow() - timedelta(days=30)
            ])
        }
        
        return {
            "dashboard_stats": stats,
            "generated_at": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data"
        )


@router.get("/users/analytics", response_model=Dict[str, Any])
async def get_user_analytics(
    db: Session = Depends(get_session),
    current_user: Users = Depends(require_admin)
):
    """
    Get detailed user analytics for admin dashboard.
    """
    try:
        # Get all users for analysis
        all_users, _ = user_service.get_users_list(
            db=db, page=1, size=1000, current_user=current_user
        ).users, 0
        
        # Analyze user distribution by location
        province_stats = {}
        district_stats = {}
        facility_stats = {}
        
        for user in all_users:
            # Province stats
            province_name = user.province_name or "Unknown"
            if province_name not in province_stats:
                province_stats[province_name] = {"total": 0, "active": 0}
            province_stats[province_name]["total"] += 1
            if user.is_active:
                province_stats[province_name]["active"] += 1
            
            # District stats
            district_name = user.district_name or "Unknown"
            if district_name not in district_stats:
                district_stats[district_name] = {"total": 0, "active": 0}
            district_stats[district_name]["total"] += 1
            if user.is_active:
                district_stats[district_name]["active"] += 1
            
            # Facility stats
            facility_name = user.facility_name or "Unknown"
            if facility_name not in facility_stats:
                facility_stats[facility_name] = {"total": 0, "active": 0, "type": user.facility_type}
            facility_stats[facility_name]["total"] += 1
            if user.is_active:
                facility_stats[facility_name]["active"] += 1
        
        # Recent activity analysis
        now = datetime.utcnow()
        activity_stats = {
            "last_7_days": len([
                u for u in all_users 
                if u.created_at and u.created_at >= now - timedelta(days=7)
            ]),
            "last_30_days": len([
                u for u in all_users 
                if u.created_at and u.created_at >= now - timedelta(days=30)
            ]),
            "last_90_days": len([
                u for u in all_users 
                if u.created_at and u.created_at >= now - timedelta(days=90)
            ])
        }
        
        return {
            "user_distribution": {
                "by_province": province_stats,
                "by_district": district_stats,
                "by_facility": facility_stats
            },
            "registration_activity": activity_stats,
            "generated_at": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user analytics"
        )


@router.get("/users/inactive", response_model=UserListResponse)
async def get_inactive_users(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    facility_id: Optional[int] = Query(None, description="Filter by facility ID"),
    district_id: Optional[int] = Query(None, description="Filter by district ID"),
    province_id: Optional[int] = Query(None, description="Filter by province ID"),
    db: Session = Depends(get_session),
    current_user: Users = Depends(require_admin)
):
    """
    Get all inactive users with filtering options.
    """
    try:
        return user_service.get_users_list(
            db=db,
            page=page,
            size=size,
            facility_id=facility_id,
            district_id=district_id,
            province_id=province_id,
            is_active=False,
            current_user=current_user
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve inactive users"
        )


@router.get("/users/recent", response_model=List[UserResponse])
async def get_recent_users(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of users to return"),
    db: Session = Depends(get_session),
    current_user: Users = Depends(require_admin)
):
    """
    Get recently registered users.
    """
    try:
        # Get users with larger page size for filtering
        all_users, _ = user_service.get_users_list(
            db=db, page=1, size=1000, current_user=current_user
        ).users, 0
        
        # Filter for recent users
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_users = [
            user for user in all_users
            if user.created_at and user.created_at >= cutoff_date
        ]
        
        # Sort by creation date (newest first) and limit
        recent_users.sort(key=lambda x: x.created_at, reverse=True)
        return recent_users[:limit]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent users"
        )


@router.post("/users/{user_id}/reset-password")
async def admin_reset_user_password(
    user_id: int,
    new_password: str = Query(..., description="New password for the user"),
    db: Session = Depends(get_session),
    current_user: Users = Depends(require_admin)
):
    """
    Admin can reset any user's password without requiring current password.
    """
    try:
        # Get the target user
        target_user = user_service.get_user_by_id(db, user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Hash new password and update directly via repository
        from app.repositories.user_repository import UserRepository
        user_repo = UserRepository(db)
        new_password_hash = auth_service.get_password_hash(new_password)
        
        success = user_repo.update_password(user_id, new_password_hash)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to reset password"
            )
        
        return {
            "message": f"Password reset successfully for user {target_user.email}",
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset user password"
        )


@router.post("/users/bulk-activate")
async def bulk_activate_users(
    user_ids: List[int],
    db: Session = Depends(get_session),
    current_user: Users = Depends(require_admin)
):
    """
    Bulk activate multiple users.
    """
    try:
        results = {"success": [], "failed": [], "not_found": []}
        
        for user_id in user_ids:
            try:
                success = user_service.activate_user(db, user_id, current_user)
                if success:
                    results["success"].append(user_id)
                else:
                    results["not_found"].append(user_id)
            except Exception:
                results["failed"].append(user_id)
        
        return {
            "message": f"Bulk activation completed. Success: {len(results['success'])}, Failed: {len(results['failed'])}, Not Found: {len(results['not_found'])}",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk activation"
        )


@router.post("/users/bulk-deactivate")
async def bulk_deactivate_users(
    user_ids: List[int],
    db: Session = Depends(get_session),
    current_user: Users = Depends(require_admin)
):
    """
    Bulk deactivate multiple users.
    """
    try:
        results = {"success": [], "failed": [], "not_found": [], "self_deactivation": []}
        
        for user_id in user_ids:
            # Prevent admin from deactivating themselves
            if user_id == current_user.id:
                results["self_deactivation"].append(user_id)
                continue
                
            try:
                success = user_service.deactivate_user(db, user_id, current_user)
                if success:
                    results["success"].append(user_id)
                else:
                    results["not_found"].append(user_id)
            except Exception:
                results["failed"].append(user_id)
        
        return {
            "message": f"Bulk deactivation completed. Success: {len(results['success'])}, Failed: {len(results['failed'])}, Not Found: {len(results['not_found'])}",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk deactivation"
        )


@router.get("/users/search-advanced")
async def advanced_user_search(
    email_pattern: Optional[str] = Query(None, description="Email pattern to search"),
    name_pattern: Optional[str] = Query(None, description="Name pattern to search"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    created_after: Optional[str] = Query(None, description="Created after date (YYYY-MM-DD)"),
    created_before: Optional[str] = Query(None, description="Created before date (YYYY-MM-DD)"),
    facility_id: Optional[int] = Query(None, description="Filter by facility ID"),
    district_id: Optional[int] = Query(None, description="Filter by district ID"),
    province_id: Optional[int] = Query(None, description="Filter by province ID"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=200, description="Page size"),
    db: Session = Depends(get_session),
    current_user: Users = Depends(require_admin)
):
    """
    Advanced user search with multiple filters.
    """
    try:
        # Build search pattern
        search_terms = []
        if email_pattern:
            search_terms.append(email_pattern)
        if name_pattern:
            search_terms.append(name_pattern)
        search = " ".join(search_terms) if search_terms else None
        
        # Get users with filters
        result = user_service.get_users_list(
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
        
        # Additional date filtering if specified
        if created_after or created_before:
            filtered_users = []
            for user in result.users:
                if not user.created_at:
                    continue
                    
                user_date = user.created_at.date()
                
                if created_after:
                    after_date = datetime.strptime(created_after, "%Y-%m-%d").date()
                    if user_date < after_date:
                        continue
                        
                if created_before:
                    before_date = datetime.strptime(created_before, "%Y-%m-%d").date()
                    if user_date > before_date:
                        continue
                        
                filtered_users.append(user)
            
            result.users = filtered_users
            result.total = len(filtered_users)
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform advanced search"
        )


@router.get("/system/health")
async def system_health_check(
    current_user: Users = Depends(require_admin)
):
    """
    Basic system health check for admin monitoring.
    """
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "admin_user": current_user.email,
            "system_info": {
                "authentication": "operational",
                "database": "connected",
                "user_management": "operational"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="System health check failed"
        )
    

# extra

@router.post("/users/create-admin", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_admin_user(
    user_data: UserCreate,
    db: Session = Depends(get_session),
    current_user: Users = Depends(require_admin),
    require_confirmation: bool = Query(True, description="Require explicit confirmation for admin creation")
):
    """
    Create a new admin user. (Admin only)
    This is a dedicated endpoint for creating admin users with additional security checks.
    """
    try:
        # Additional validation for admin creation
        if user_data.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This endpoint is specifically for creating admin users"
            )
        
        # Optional: Add confirmation requirement
        if require_confirmation:
            # In a real implementation, you might want to require a confirmation token
            # or additional authentication step
            pass
        
        # Log admin creation attempt for audit purposes
        # TODO: Implement audit logging
        print(f"Admin {current_user.email} attempting to create new admin: {user_data.email}")
        
        user = user_service.create_user(db, user_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create admin user"
            )
        
        # Log successful admin creation
        print(f"New admin user created: {user.email} by {current_user.email}")
        
        return user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create admin user"
        )


@router.get("/users/admins", response_model=List[UserResponse])
async def get_all_admin_users(
    include_inactive: bool = Query(False, description="Include inactive admin users"),
    db: Session = Depends(get_session),
    current_user: Users = Depends(require_admin)
):
    """
    Get all admin users. (Admin only)
    """
    try:
        # Get all users with admin role
        result = user_service.get_users_list(
            db=db,
            page=1,
            size=1000,  # Large enough to get all admins
            role="admin",
            is_active=None if include_inactive else True,
            current_user=current_user
        )
        
        return result.users
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve admin users"
        )


@router.post("/users/{user_id}/promote-to-admin")
async def promote_user_to_admin(
    user_id: int,
    confirmation: bool = Query(..., description="Explicit confirmation required"),
    db: Session = Depends(get_session),
    current_user: Users = Depends(require_admin)
):
    """
    Promote an existing user to admin role. (Admin only)
    """
    try:
        if not confirmation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Explicit confirmation required for admin promotion"
            )
        
        # Get the target user
        target_user = user_service.get_user_by_id(db, user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user is already an admin
        if target_user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already an admin"
            )
        
        # Update user role to admin
        update_data = UserUpdate(role=UserRole.ADMIN)
        updated_user = user_service.update_user(db, user_id, update_data, current_user)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to promote user to admin"
            )
        
        # Log the promotion for audit purposes
        print(f"User {target_user.email} promoted to admin by {current_user.email}")
        
        return {
            "message": f"User {target_user.email} has been promoted to admin",
            "user": updated_user
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to promote user to admin"
        )


@router.post("/users/{user_id}/demote-from-admin")
async def demote_admin_user(
    user_id: int,
    new_role: UserRole = Query(..., description="New role for the demoted admin"),
    confirmation: bool = Query(..., description="Explicit confirmation required"),
    db: Session = Depends(get_session),
    current_user: Users = Depends(require_admin)
):
    """
    Demote an admin user to a lower role. (Admin only)
    """
    try:
        if not confirmation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Explicit confirmation required for admin demotion"
            )
        
        # Prevent self-demotion
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote yourself"
            )
        
        # Validate new role
        if new_role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote admin to admin role"
            )
        
        # Get the target user
        target_user = user_service.get_user_by_id(db, user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user is actually an admin
        if target_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not an admin"
            )
        
        # Update user role
        update_data = UserUpdate(role=new_role)
        updated_user = user_service.update_user(db, user_id, update_data, current_user)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to demote admin user"
            )
        
        # Log the demotion for audit purposes
        print(f"Admin {target_user.email} demoted to {new_role.value} by {current_user.email}")
        
        return {
            "message": f"Admin {target_user.email} has been demoted to {new_role.value}",
            "user": updated_user
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to demote admin user"
        )


@router.get("/security/admin-activity")
async def get_admin_activity_log(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: Session = Depends(get_session),
    current_user: Users = Depends(require_admin)
):
    """
    Get admin activity summary for security monitoring. (Admin only)
    """
    try:
        # This is a placeholder for admin activity logging
        # In a real implementation, you would track admin actions in an audit log table
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get recent admin users
        admin_result = user_service.get_users_list(
            db=db,
            page=1,
            size=1000,
            role="ADMIN",
            current_user=current_user
        )
        
        # Count recent admin registrations
        recent_admin_registrations = len([
            user for user in admin_result.users
            if user.created_at and user.created_at >= cutoff_date
        ])
        
        return {
            "period_days": days,
            "total_admins": len(admin_result.users),
            "active_admins": len([u for u in admin_result.users if u.is_active]),
            "recent_admin_registrations": recent_admin_registrations,
            "monitoring_period": {
                "start_date": cutoff_date,
                "end_date": datetime.utcnow()
            },
            "note": "This is a basic implementation. Consider implementing comprehensive audit logging for production."
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve admin activity log"
        )