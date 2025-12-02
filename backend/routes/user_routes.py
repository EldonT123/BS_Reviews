# backend/routes/user_routes.py
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Form, UploadFile, File
from pydantic import BaseModel, EmailStr
from backend.services import user_service
from backend.models.user_model import User
from backend.dependencies.auth import get_current_user

router = APIRouter()

# ==================== Request Models ====================


class UserSignupAuth(BaseModel):
    """Request model for signup."""
    email: EmailStr
    username: str
    password: str


class UserLoginAuth(BaseModel):
    """Request model for login"""
    email: EmailStr
    password: str


class BookmarkRequest(BaseModel):
    """Request model for bookmark operations"""
    email: EmailStr
    movie_title: str


class SignoutRequest(BaseModel):
    """Request model for signout."""
    session_id: str

class UpdateProfileRequest(BaseModel):
    """Request model for updating profile"""
    current_email: EmailStr
    current_password: str
    new_email: Optional[EmailStr] = None
    new_username: Optional[str] = None
    new_password: Optional[str] = None


# ==================== Public Routes ====================


@router.post("/signup")
async def signup(user: UserSignupAuth):
    """Create new user account - starts as Snail tier."""
    try:
        new_user = user_service.create_user(
            email=user.email,
            username=user.username,
            password=user.password,
            tier=User.TIER_SNAIL
        )

        return {
            "message": (f"Welcome {new_user.get_tier_display_name()}! "
                        f"You can now browse movies and reviews."),
            "user": new_user.to_dict()
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login")
async def login(user: UserLoginAuth):
    """Authenticate user and return user info with session ID."""
    try:
        authenticated_user, session_id = user_service.authenticate_user(
            email=user.email,
            password=user.password
        )

        return {
            "message": (f"Welcome back, "
                        f"{authenticated_user.get_tier_display_name()}!"),
            "user": authenticated_user.to_dict(),
            "session_id": session_id
        }

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


@router.post("/signout")
async def signout(
    request: SignoutRequest,
    current_user: User = Depends(get_current_user)
):
    """Sign out user - requires authentication"""
    # Verify the session_id belongs to the current user
    success = user_service.signout_user(request.session_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired session ID"
        )

    return {"message": "Successfully signed out"}


@router.get("/check-session/{session_id}")
async def check_session(session_id: str):
    """Check if a session ID is valid and return user info."""
    user = user_service.verify_session_id(session_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )

    return {
        "message": "Session is valid",
        "logged_in": True,
        "user": user.to_dict()
    }


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


# ==================== User Profile ====================

@router.get("/profile/me")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile - requires authentication"""
    return {"user": current_user.to_dict()}


@router.get("/profile/{email}")
async def get_user_profile(
    email: str,
    current_user: User = Depends(get_current_user)
):
    """Get any user profile - requires authentication"""
    user = user_service.get_user_by_email(email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {"user": user.to_dict()}

@router.put("/update-profile")
async def update_profile(request: UpdateProfileRequest):
    """Update user profile (email, username, password)."""
    try:
        # Verify current credentials
        user = user_service.authenticate_user(
            email=request.current_email,
            password=request.current_password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Check if new email is already taken
        if request.new_email and request.new_email != request.current_email:
            if user_service.user_exists(request.new_email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
        
        # Update the user
        success = user_service.update_user_profile(
            current_email=request.current_email,
            new_email=request.new_email or request.current_email,
            new_username=request.new_username,
            new_password=request.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "Profile updated successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

"""
@router.post("/upload-profile-image")
async def upload_profile_image(email: str = Form(...), profile_image: UploadFile = File(...)):
    #Upload profile image for Banana Slug tier users.
    if not user_service.user_exists(email):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = user_service.get_user_by_email(email)
    if user.tier != User.TIER_BANANA_SLUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Banana Slug tier users can upload profile images"
        )
        """
    
    # Commented out image upload functionality to be implemented later when storage is set up
"""try:
        success = user_service.save_profile_image(email, profile_image)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload image"
            )
        return {"message": "Profile image uploaded successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )"""

# ==================== Bookmark Routes ====================


@router.post("/bookmarks/add")
async def add_bookmark(request: BookmarkRequest):
    """
    Add a movie to a user's bookmarked list
    """
    if not user_service.user_exists(request.email):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    added = user_service.add_bookmark(request.email, request.movie_title)

    if not added:
        return {
            "message": "Movie already bookmarked.",
            "bookmarked": False
        }

    return {
        "message": "Movie added to bookmarks.",
        "bookmarked": True
    }


@router.post("/bookmarks/remove")
async def remove_bookmark(request: BookmarkRequest):
    """
    Remove a movie from a user's bookmarked list
    """
    if not user_service.user_exists(request.email):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    removed = user_service.remove_bookmark(request.email, request.movie_title)

    if not removed:
        return {
            "message": "Bookmark not found.",
            "removed": False
        }

    return {
        "message": "Bookmark removed.",
        "removed": True
    }


@router.get("/bookmarks/{email}")
async def get_bookmarks(email: str):
    """
    Retrieve all bookmarked movie IDs for a user.
    """
    if not user_service.user_exists(email):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    bookmarks = user_service.get_user_bookmarks(email)

    return {
        "email": email,
        "bookmarks": bookmarks
    }


@router.get("/bookmarks/{email}/{movie_title}")
async def check_bookmark(email: str, movie_title: str):
    """
    Check if specific movie is bookmarked by the user
    """
    if not user_service.user_exists(email):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    bookmarked = user_service.is_bookmarked(email, movie_title)

    return {
        "email": email,
        "movie_title": movie_title,
        "bookmarked": bookmarked
    }
