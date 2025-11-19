# backend/routes/user_routes.py
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from backend.services import user_service
from backend.models.user_model import User

router = APIRouter()

# ==================== Request Models ====================

class UserAuth(BaseModel):
    """Request model for login/signup."""
    email: EmailStr
    password: str


class TierUpgrade(BaseModel):
    """Request model for tier upgrades."""
    email: EmailStr
    new_tier: str  # Changed from new_role


# ==================== Public Routes ====================

@router.post("/signup")
async def signup(user: UserAuth):
    """Create new user account - starts as Snail tier."""
    try:
        new_user = user_service.create_user(
            email=user.email,
            password=user.password,
            tier=User.TIER_SNAIL  # Changed from role to tier
        )
        
        return {
            "message": f"Welcome {new_user.get_tier_display_name()}! You can now browse movies and reviews.",
            "user": new_user.to_dict()
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login")
async def login(user: UserAuth):
    """Authenticate user and return user info with permissions."""
    try:
        authenticated_user = user_service.authenticate_user(
            email=user.email,
            password=user.password
        )
        
        return {
            "message": f"Welcome back, {authenticated_user.get_tier_display_name()}!",
            "user": authenticated_user.to_dict()
        }
    
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


# ==================== Tier Information ====================

@router.get("/tiers")
async def get_tier_info():
    """Get information about all available tiers."""
    return {
        "tiers": [
            {
                "name": "Snail",
                "tier": User.TIER_SNAIL,
                "emoji": "🐌",
                "permissions": [
                    "Browse movies",
                    "View reviews",
                    "Read ratings"
                ]
            },
            {
                "name": "Slug",
                "tier": User.TIER_SLUG,
                "emoji": "🐌",
                "permissions": [
                    "All Snail permissions",
                    "Write reviews",
                    "Edit own reviews",
                    "Rate movies"
                ]
            },
            {
                "name": "Banana Slug",
                "tier": User.TIER_BANANA_SLUG,
                "emoji": "🍌",
                "permissions": [
                    "All Slug permissions",
                    "Reviews appear first",
                    "Special cosmetics (coming soon)",
                    "VIP status"
                ]
            }
        ]
    }


# ==================== Admin Routes ====================

@router.post("/admin/upgrade-tier")
async def upgrade_user_tier(upgrade: TierUpgrade):
    """
    Upgrade a user's tier (admin only for now).
    Later: Add authentication middleware here
    """
    valid_tiers = [User.TIER_SNAIL, User.TIER_SLUG, User.TIER_BANANA_SLUG, User.TIER_ADMIN]
    
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


@router.get("/admin/users")
async def get_all_users():
    """Get all users with their tiers (admin only)."""
    users = user_service.get_all_users()
    return {
        "users": [user.to_dict() for user in users],
        "total": len(users)
    }