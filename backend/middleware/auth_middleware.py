# backend/middleware/auth_middleware.py
from fastapi import Header, HTTPException, status
from typing import Optional
from backend.services import admin_service


async def verify_admin_token(x_admin_token: Optional[str] = Header(None)):
    """
    Dependency to verify admin authentication token.

    Args:
        x_admin_token: Admin token from request header

    Returns:
        Admin object if authenticated

    Raises:
        HTTPException: If token is missing or invalid
    """
    if not x_admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Verify token and get admin
        admin = admin_service.verify_admin_token(x_admin_token)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired admin token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return admin

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
            headers={"WWW-Authenticate": "Bearer"},
        )
