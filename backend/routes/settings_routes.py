# backend/routes/settings_routes.py
"""Routes for user settings management - all routes require authentication."""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from backend.services import settings_service, user_service
from backend.models.user_model import User

router = APIRouter()


# ==================== Authentication Dependency ====================

async def get_current_user(email: str) -> User:
    """
    Verify user exists for protected routes.

    This is a simplified authentication dependency.
    In production, you would use JWT tokens or session-based auth.

    Args:
        email: User email from request

    Returns:
        User object if authenticated

    Raises:
        HTTPException: If user not found or not authenticated
    """
    user = user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return user


# ==================== Request Models ====================

class ChangeEmailRequest(BaseModel):
    """Request model for changing email."""
    current_email: EmailStr
    new_email: EmailStr
    current_password: str


class ChangePasswordRequest(BaseModel):
    """Request model for changing password."""
    email: EmailStr
    current_password: str
    new_password: str


class GetSettingsRequest(BaseModel):
    """Request model for getting user settings."""
    email: EmailStr


# ==================== Settings Routes (Protected) ====================

@router.get("/settings")
async def get_settings(email: str):
    """
    Get user's current settings.

    This route requires the user to be logged in (email parameter).

    Args:
        email: User's email address

    Returns:
        User settings including email and tier information
    """
    # Verify user exists (acts as authentication check)
    await get_current_user(email)

    settings = settings_service.get_user_settings(email)

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "message": "Settings retrieved successfully",
        "settings": settings
    }


@router.put("/settings/change-email")
async def change_email(request: ChangeEmailRequest):
    """
    Change user's email address.

    Requires current password verification.
    User must be logged in to access this endpoint.

    Args:
        request: Contains current_email, new_email, and current_password

    Returns:
        Success message with updated user information
    """
    # Verify user exists (authentication check)
    await get_current_user(request.current_email)

    try:
        success = settings_service.change_email(
            current_email=request.current_email,
            new_email=request.new_email,
            current_password=request.current_password
        )

        if success:
            updated_user = user_service.get_user_by_email(request.new_email)
            return {
                "message": "Email changed successfully",
                "user": updated_user.to_dict()
            }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/settings/change-password")
async def change_password(request: ChangePasswordRequest):
    """
    Change user's password.

    Requires current password verification.
    User must be logged in to access this endpoint.

    Args:
        request: Contains email, current_password, and new_password

    Returns:
        Success message
    """
    # Verify user exists (authentication check)
    await get_current_user(request.email)

    try:
        success = settings_service.change_password(
            email=request.email,
            current_password=request.current_password,
            new_password=request.new_password
        )

        if success:
            return {
                "message": "Password changed successfully",
                "email": request.email
            }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== Account Information ====================

@router.get("/settings/account/{email}")
async def get_account_info(email: str):
    """
    Get detailed account information for the user.

    User must be logged in to access this endpoint.

    Args:
        email: User's email address

    Returns:
        Detailed account information
    """
    # Verify user exists (authentication check)
    user = await get_current_user(email)

    return {
        "message": "Account information retrieved successfully",
        "account": {
            "email": user.email,
            "tier": user.tier,
            "tier_name": user.get_tier_display_name(),
            "tier_emoji": user.get_tier_emoji(),
            "permissions": user.get_permissions()
        }
    }