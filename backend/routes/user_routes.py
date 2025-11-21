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


class BookmarkRequest(BaseModel):
    """Request model for bookmark operations"""
    email: EmailStr
    movie_title: str

# ==================== Public Routes ====================


@router.post("/signup")
async def signup(user: UserAuth):
    """Create new user account - starts as Snail tier."""
    try:
        new_user = user_service.create_user(
            email=user.email,
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
async def login(user: UserAuth):
    """Authenticate user and return user info with permissions."""
    try:
        authenticated_user = user_service.authenticate_user(
            email=user.email,
            password=user.password
        )

        return {
            "message": (f"Welcome back, "
                        f"{authenticated_user.get_tier_display_name()}!"),
            "user": authenticated_user.to_dict(),
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


# ==================== User Profile ====================

@router.get("/profile/{email}")
async def get_user_profile(email: str):
    """Get user profile information."""
    user = user_service.get_user_by_email(email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "user": user.to_dict()
    }
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
