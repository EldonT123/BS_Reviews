# backend/middleware/auth_middleware.py
from fastapi import Header, HTTPException, status
from typing import Optional
from backend.services import admin_service


async def verify_admin_token(authorization: Optional[str] = Header(None)):
    """
    Dependency to verify admin authentication token.

    Args:
        authorization: Authorization header with Bearer token (e.g., "Bearer <token>")

    Returns:
        Admin object if authenticated

    Raises:
        HTTPException: If token is missing or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>" format
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme. Use Bearer token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Verify token and get admin
        admin = admin_service.verify_admin_token(token)
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