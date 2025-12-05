# backend/routes/admin_routes.py
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from backend.services import admin_service, user_service, review_service, file_service
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


class MovieCreate(BaseModel):
    """Request model for creating movies with full metadata."""
    movie_name: str
    title: str
    director: Optional[str] = ""
    directors: Optional[List[str]] = []
    genre: Optional[str] = ""
    movieGenres: Optional[List[str]] = []
    year: Optional[str] = ""
    datePublished: Optional[str] = ""
    imdb_rating: Optional[float] = 0.0
    description: Optional[str] = ""
    duration: Optional[int] = 0
    creators: Optional[List[str]] = []
    mainStars: Optional[List[str]] = []
    totalRatingCount: Optional[int] = 0
    totalUserReviews: Optional[str] = "0"
    totalCriticReviews: Optional[str] = "0"
    metaScore: Optional[str] = "0"


class MovieUpdate(BaseModel):
    """Request model for updating movies with full metadata."""
    title: Optional[str] = None
    director: Optional[str] = None
    directors: Optional[List[str]] = None
    genre: Optional[str] = None
    movieGenres: Optional[List[str]] = None
    year: Optional[str] = None
    datePublished: Optional[str] = None
    imdb_rating: Optional[float] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    creators: Optional[List[str]] = None
    mainStars: Optional[List[str]] = None
    totalRatingCount: Optional[int] = None
    totalUserReviews: Optional[str] = None
    totalCriticReviews: Optional[str] = None
    metaScore: Optional[str] = None


class MovieDelete(BaseModel):
    """Request model for deleting movies."""
    movie_name: str
class TokenPenalty(BaseModel):
    """Request model for removing tokens from a user."""
    email: EmailStr
    tokens_to_remove: int


class ReviewBan(BaseModel):
    """Request model for banning/unbanning user from reviews."""
    email: EmailStr
    ban: bool = True  # True = ban, False = unban


class UserBan(BaseModel):
    """Request model for banning users permanently."""
    email: EmailStr
    reason: str = ""


class UserUnban(BaseModel):
    """Request model for unbanning users."""
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


# ==================== Movie Management (Protected) ====================

@router.get("/movies")
async def get_all_movies(admin: Admin = Depends(verify_admin_token)):
    """Get all movies with full metadata (admin only)."""
    try:
        movies = file_service.get_all_movies()
        return {
            "movies": movies,
            "total": len(movies)
        }
    except Exception as e:
        print(f"Error in get_all_movies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching movies: {str(e)}"
        )


@router.post("/movies")
async def create_movie(
    movie: MovieCreate,
    admin: Admin = Depends(verify_admin_token)
):
    """Create a new movie with full metadata (admin only)."""
    try:
        # Check if movie already exists
        if file_service.movie_exists(movie.movie_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Movie with this name already exists"
            )

        # Handle genres - prefer movieGenres array, fallback to genre string
        genres = movie.movieGenres if movie.movieGenres else (
            [g.strip() for g in movie.genre.split(",")] if movie.genre else []
        )

        # Handle directors - prefer directors array,
        # fallback to director string
        directors = movie.directors if movie.directors else (
            [movie.director] if movie.director else []
        )

        # Handle date - prefer datePublished, fallback to year
        date_published = movie.datePublished if movie.datePublished else (
            f"{movie.year}-01-01" if movie.year else ""
        )

        # Create movie using file_service
        success = file_service.create_movie_with_metadata(
            movie_name=movie.movie_name,
            title=movie.title,
            directors=directors,
            genres=genres,
            date_published=date_published,
            imdb_rating=movie.imdb_rating or 0.0,
            description=movie.description or "",
            duration=movie.duration or 0,
            creators=movie.creators or [],
            main_stars=movie.mainStars or [],
            total_rating_count=movie.totalRatingCount or 0,
            total_user_reviews=movie.totalUserReviews or "0",
            total_critic_reviews=movie.totalCriticReviews or "0",
            meta_score=movie.metaScore or "0"
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create movie"
            )

        # Get the created movie metadata
        metadata = file_service.get_movie_metadata(movie.movie_name)

        return {
            "message": f"Movie '{movie.title}' created successfully",
            "movie": metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating movie: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating movie: {str(e)}"
        )


@router.put("/movies/{movie_name}")
async def update_movie(
    movie_name: str,
    movie_update: MovieUpdate,
    admin: Admin = Depends(verify_admin_token)
):
    """Update a movie's metadata with all fields (admin only)."""
    try:
        # Check if movie exists
        if not file_service.movie_exists(movie_name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movie not found"
            )

        # Prepare updates dictionary
        updates = {}

        if movie_update.title is not None:
            updates["title"] = movie_update.title

        if movie_update.imdb_rating is not None:
            updates["movieIMDbRating"] = movie_update.imdb_rating

        if movie_update.totalRatingCount is not None:
            updates["totalRatingCount"] = movie_update.totalRatingCount

        if movie_update.totalUserReviews is not None:
            updates["totalUserReviews"] = movie_update.totalUserReviews

        if movie_update.totalCriticReviews is not None:
            updates["totalCriticReviews"] = movie_update.totalCriticReviews

        if movie_update.metaScore is not None:
            updates["metaScore"] = movie_update.metaScore

        # Handle genres
        if movie_update.movieGenres is not None:
            updates["movieGenres"] = movie_update.movieGenres
        elif movie_update.genre is not None:
            updates["movieGenres"] = (
                [g.strip() for g in movie_update.genre.split(",")]
                if movie_update.genre
                else []
            )

        # Handle directors
        if movie_update.directors is not None:
            updates["directors"] = movie_update.directors
        elif movie_update.director is not None:
            updates["directors"] = (
                [movie_update.director] if movie_update.director else []
            )

        # Handle date
        if movie_update.datePublished is not None:
            updates["datePublished"] = movie_update.datePublished
        elif movie_update.year is not None:
            updates["datePublished"] = (
                f"{movie_update.year}-01-01" if movie_update.year else ""
            )

        if movie_update.creators is not None:
            updates["creators"] = movie_update.creators

        if movie_update.mainStars is not None:
            updates["mainStars"] = movie_update.mainStars

        if movie_update.description is not None:
            updates["description"] = movie_update.description

        if movie_update.duration is not None:
            updates["duration"] = movie_update.duration

        # Update using file_service
        success = file_service.update_movie_metadata(movie_name, updates)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update movie"
            )

        # Get updated metadata
        metadata = file_service.get_movie_metadata(movie_name)

        return {
            "message": f"Movie '{movie_name}' updated successfully",
            "movie": metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating movie: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating movie: {str(e)}"
        )


@router.delete("/movies/{movie_name}")
async def delete_movie(
    movie_name: str,
    admin: Admin = Depends(verify_admin_token)
):
    """Delete a movie (admin only)."""
    try:
        # Check if movie exists
        if not file_service.movie_exists(movie_name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movie not found"
            )

        # Delete using file_service
        message = file_service.delete_movie_folder(movie_name)

        return {
            "message": message
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )
    except Exception as e:
        print(f"Error deleting movie: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting movie: {str(e)}"
        )


@router.post("/movies/{movie_name}/poster")
async def upload_poster(
    movie_name: str,
    file: UploadFile = File(...),
    admin: Admin = Depends(verify_admin_token)
):
    """Upload a poster for a movie (admin only)."""
    # Check if movie exists
    if not file_service.movie_exists(movie_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )

    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )

    # Save poster using file_service
    poster_data = await file.read()
    success = file_service.save_poster(movie_name, poster_data)
    
    return {
        "message": f"Poster uploaded successfully for '{movie_name}'"
            detail="Failed to unban email"
        )

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
            detail=(f"User only has {user.tokens} tokens. ",
                    f"Cannot remove {penalty.tokens_to_remove}.")
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
        "message": (
            f"Removed {penalty.tokens_to_remove} tokens "
            f"from {penalty.email}"
        ),
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
        review_result = review_service.mark_all_reviews_penalized(
            ban_request.email)

    # Get updated user
    updated_user = user_service.get_user_by_email(ban_request.email)

    action = "banned from" if ban_request.ban else "unbanned from"
    message = f"User {ban_request.email} has been {action} writing reviews"

    if ban_request.ban and review_result["reviews_marked"] > 0:
        message += (
            f". {review_result['reviews_marked']} "
            f"existing reviews marked as penalized "
            f"across {len(review_result['movies_affected'])} movies"
        )

    return {
        "message": message,
        "user": updated_user.to_dict(),
        "reviews_affected": review_result if ban_request.ban else None
    }


@router.post("/users/ban")
async def ban_user(
    ban_request: UserBan,
    admin: Admin = Depends(verify_admin_token)
):
    """
    Permanently ban a user (admin only).
    This will:
    - Add email to permanent blacklist
    - Delete user account completely
    - Revoke all active sessions
    - Mark all reviews as penalized and hidden
    - Prevent future signups with this email
    """
    result = admin_service.ban_user(
        email=ban_request.email,
        admin_email=admin.email,
        reason=ban_request.reason
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )

    return {
        "message": result["message"],
        "details": result["details"]
    }


@router.post("/users/unban")
async def unban_user(
    unban_request: UserUnban,
    admin: Admin = Depends(verify_admin_token)
):
    """
    Remove an email from the ban list (admin only).
    This allows the email to create a new account.
    Note: This does NOT restore the deleted account.
    """
    # Check if email is actually banned
    if not admin_service.is_email_banned(unban_request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is not currently banned"
        )

    # Get ban info before removing
    ban_info = admin_service.get_banned_email_info(unban_request.email)

    # Remove from blacklist
    success = admin_service.remove_banned_email(unban_request.email)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save poster"
        )

    return {
        "message": (
            f"Email {unban_request.email} has been unbanned "
            f"and can now create a new account"
        ),
        "previous_ban_info": ban_info
    }


@router.get("/users/banned")
async def get_banned_users(admin: Admin = Depends(verify_admin_token)):
    """
    Get list of all banned emails (admin only).
    """
    banned_emails = admin_service.get_all_banned_emails()

    return {
        "banned_emails": banned_emails,
        "total": len(banned_emails)
    }


@router.get("/users/banned/{email}")
async def check_banned_status(
    email: str,
    admin: Admin = Depends(verify_admin_token)
):
    """
    Check if a specific email is banned (admin only).
    """
    is_banned = admin_service.is_email_banned(email)

    if not is_banned:
        return {
            "email": email,
            "is_banned": False
        }

    ban_info = admin_service.get_banned_email_info(email)

    return {
        "email": email,
        "is_banned": True,
        "ban_info": ban_info
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
