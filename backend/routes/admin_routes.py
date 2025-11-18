# backend/routes/admin_routes.py
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from backend.services import admin_service, user_service
from backend.models.user_model import User

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
    """Create new admin account."""
    try:
        new_admin = admin_service.create_admin(
            email=admin.email,
            password=admin.password
        )
        
        return {
            "message": "Admin account created successfully",
            "admin": new_admin.to_dict()
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login")
async def admin_login(admin: AdminAuth):
    """Authenticate admin and return admin info."""
    try:
        authenticated_admin = admin_service.authenticate_admin(
            email=admin.email,
            password=admin.password
        )
        
        return {
            "message": "Admin authenticated successfully",
            "admin": authenticated_admin.to_dict()
        }
    
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials"
        )


# ==================== User Management ====================

@router.get("/users")
async def get_all_users():
    """Get all users with their tiers (admin only)."""
    users = user_service.get_all_users()
    return {
        "users": [user.to_dict() for user in users],
        "total": len(users)
    }


@router.post("/users/upgrade-tier")
async def upgrade_user_tier(upgrade: TierUpgrade):
    """
    Upgrade a user's tier (admin only).
    TODO: Add authentication middleware to verify admin status
    """
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
async def delete_user(user_delete: UserDelete):
    """
    Delete a user (admin only).
    TODO: Add authentication middleware to verify admin status
    """
    success = user_service.delete_user(user_delete.email)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "message": f"User {user_delete.email} deleted successfully"
    }


# ==================== Admin Management ====================

@router.get("/admins")
async def get_all_admins():
    """Get all admins (admin only, for super admin management)."""
    admins = admin_service.get_all_admins()
    return {
        "admins": [admin.to_dict() for admin in admins],
        "total": len(admins)
    }
