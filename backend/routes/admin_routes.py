# backend/routes/admin_routes.py
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from backend.services import admin_service, user_service
from backend.models.user_model import User
from backend.models.admin_model import Admin
from backend.middleware.auth_middleware import verify_admin_token

router = APIRouter()

# ==================== Request Models ====================

class AdminAuth(BaseModel):
    """Request model for admin login/signup."""
    email: EmailStr
    password: str


class TierUpgrade(BaseModel):
    """Request model for tier upgrades."""
    email: EmailStr
    new_tier: str


class UserDelete(BaseModel):
    """Request model for deleting users."""
    email: EmailStr


# ==================== Admin Authentication ====================

@router.post("/signup")
async def admin_signup(admin: AdminAuth):
    """Create new admin account and return authentication token."""
    try:
        new_admin, token = admin_service.create_admin(
            email=admin.email,
            password=admin.password
        )
        
        return {
            "message": "Admin account created successfully",
            "admin": new_admin.to_dict(),
            "token": token,
            "token_type": "bearer"
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login")
async def admin_login(admin: AdminAuth):
    """Authenticate admin and return admin info with authentication token."""
    try:
        authenticated_admin, token = admin_service.authenticate_admin(
            email=admin.email,
            password=admin.password
        )
        
        return {
            "message": "Admin authenticated successfully",
            "admin": authenticated_admin.to_dict(),
            "token": token,
            "token_type": "bearer"
        }
    
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials"
        )


@router.post("/logout")
async def admin_logout(admin: Admin = Depends(verify_admin_token)):
    """Logout admin by revoking token."""
    # Note: Token is extracted from header in dependency
    # For full implementation, you'd need to pass the token to revoke_token
    return {
        "message": "Admin logged out successfully"
    }


# ==================== User Management (Protected) ====================

@router.get("/users")
async def get_all_users(admin: Admin = Depends(verify_admin_token)):
    """Get all users with their tiers (admin only)."""
    users = user_service.get_all_users()
    return {
        "users": [user.to_dict() for user in users],
        "total": len(users)
    }


@router.post("/users/upgrade-tier")
async def upgrade_user_tier(
    upgrade: TierUpgrade,
    admin: Admin = Depends(verify_admin_token)
):
    """Upgrade a user's tier (admin only - now protected)."""
    valid_tiers = [User.TIER_SNAIL, User.TIER_SLUG, User.TIER_BANANA_SLUG]
    
    if upgrade.new_tier not in valid_tiers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier. Must be one of: {valid_tiers}"
        )
    
    success = user_service.update_user_tier(upgrade.email, upgrade.new_tier)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = user_service.get_user_by_email(upgrade.email)
    return {
        "message": f"User upgraded to {user.get_tier_display_name()}!",
        "user": user.to_dict()
    }


@router.delete("/users")
async def delete_user(
    user_delete: UserDelete,
    admin: Admin = Depends(verify_admin_token)
):
    """Delete a user (admin only - now protected)."""
    success = user_service.delete_user(user_delete.email)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "message": f"User {user_delete.email} deleted successfully"
    }


# ==================== Admin Management (Protected) ====================

@router.get("/admins")
async def get_all_admins(admin: Admin = Depends(verify_admin_token)):
    """Get all admins (admin only, for super admin management)."""
    admins = admin_service.get_all_admins()
    return {
        "admins": [admin.to_dict() for admin in admins],
        "total": len(admins)
    }
