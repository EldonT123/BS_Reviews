# backend/dependencies/auth.py
from fastapi import Header, HTTPException, status, Depends
from backend.services import user_service
from backend.models.user_model import User
from typing import Optional


async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> User:
    """
    Dependency that validates session and returns current user.

    Expects Authorization header in format: "Bearer <session_id>"

    Raises:
        HTTPException: If session is invalid or missing
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated - Authorization header missing"
        )

    # Parse "Bearer <session_id>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Invalid authorization header format."
                "Use: Bearer <session_id>")
        )

    session_id = parts[1]

    # Verify session
    user = user_service.verify_session_id(session_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )

    return user


# For routes that need specific tier access
async def require_slug_tier(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require user to be Slug tier or higher"""
    if current_user.tier < User.TIER_SLUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature requires Slug tier or higher"
        )
    return current_user


async def require_banana_slug_tier(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require user to be Banana Slug tier"""
    if current_user.tier < User.TIER_BANANA_SLUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature requires Banana Slug tier"
        )
    return current_user
