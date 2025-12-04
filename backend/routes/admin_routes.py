# backend/routes/admin_routes.py
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from backend.services import admin_service, user_service, review_service
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


class TokenPenalty(BaseModel):
    """Request model for removing tokens from a user."""
    email: EmailStr
    tokens_to_remove: int


class ReviewBan(BaseModel):
    """Request model for banning/unbanning user from reviews."""
    email: EmailStr
    ban: bool = True  # True = ban, False = unban


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


@router.post("/users/remove-tokens")
async def remove_user_tokens(
    penalty: TokenPenalty,
    admin: Admin = Depends(verify_admin_token)
):
    """Remove tokens from a user as a penalty (admin only)."""
    if penalty.tokens_to_remove <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token amount must be positive"
        )

    # Get user to check current balance
    user = user_service.get_user_by_email(penalty.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if user has enough tokens
    if user.tokens < penalty.tokens_to_remove:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User only has {user.tokens} tokens. Cannot remove {penalty.tokens_to_remove}."
        )

    # Deduct tokens
    success = user_service.deduct_tokens_from_user(
        penalty.email, 
        penalty.tokens_to_remove
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove tokens"
        )

    # Get updated user
    updated_user = user_service.get_user_by_email(penalty.email)

    return {
        "message": f"Removed {penalty.tokens_to_remove} tokens from {penalty.email}",
        "previous_balance": user.tokens,
        "new_balance": updated_user.tokens,
        "user": updated_user.to_dict()
    }


@router.post("/users/review-ban")
async def ban_user_from_reviews(
    ban_request: ReviewBan,
    admin: Admin = Depends(verify_admin_token)
):
    """
    Ban or unban a user from writing reviews (admin only).
    When banned:
    - User cannot write new reviews
    - User cannot rate movies
    - User cannot edit existing reviews
    - All existing reviews are marked as penalized and hidden
    """
    # Check if user exists
    user = user_service.get_user_by_email(ban_request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check current status
    if ban_request.ban and user.review_banned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already banned from reviewing"
        )

    if not ban_request.ban and not user.review_banned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not currently banned from reviewing"
        )

    # Update ban status
    success = user_service.update_review_ban_status(
        ban_request.email, 
        ban_request.ban
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update review ban status"
        )

    # If banning, mark all existing reviews as penalized
    review_result = {"reviews_marked": 0, "movies_affected": []}
    if ban_request.ban:
        review_result = review_service.mark_all_reviews_penalized(ban_request.email)

    # Get updated user
    updated_user = user_service.get_user_by_email(ban_request.email)

    action = "banned from" if ban_request.ban else "unbanned from"
    message = f"User {ban_request.email} has been {action} writing reviews"

    if ban_request.ban and review_result["reviews_marked"] > 0:
        message += f". {review_result['reviews_marked']} existing reviews marked as penalized across {len(review_result['movies_affected'])} movies"

    return {
        "message": message,
        "user": updated_user.to_dict(),
        "reviews_affected": review_result if ban_request.ban else None
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
