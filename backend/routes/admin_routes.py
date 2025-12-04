# backend/routes/admin_routes.py
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from pydantic import BaseModel, EmailStr
from typing import Optional
from backend.services import admin_service, user_service
from backend.services.search_service import SearchService
from backend.models.user_model import User
from backend.models.admin_model import Admin
from backend.middleware.auth_middleware import verify_admin_token
import os
import json

router = APIRouter()

# Initialize search service
search_service = SearchService(database_path="/app/database/archive")

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
    """Request model for creating movies."""
    movie_name: str
    title: str
    director: Optional[str] = ""
    genre: Optional[str] = ""
    year: Optional[str] = ""
    imdb_rating: Optional[float] = 0.0


class MovieUpdate(BaseModel):
    """Request model for updating movies."""
    title: Optional[str] = None
    director: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[str] = None
    imdb_rating: Optional[float] = None


class MovieDelete(BaseModel):
    """Request model for deleting movies."""
    movie_name: str


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
    """Get all movies (admin only)."""
    # Use search service to get all movies
    movie_folders = search_service._get_all_movie_folders()
    movies = []
    
    for folder in movie_folders:
        metadata = search_service._load_movie_metadata(folder)
        if metadata:
            # Handle genres
            genres = metadata.get("movieGenres", [])
            if isinstance(genres, list):
                genre_str = ", ".join(genres) if genres else ""
            else:
                genre_str = str(genres) if genres else ""
            
            movies.append({
                "movie_name": folder,
                "title": metadata.get("title", folder),
                "director": metadata.get("movieDirector", ""),
                "genre": genre_str,
                "year": metadata.get("releaseYear", ""),
                "movieIMDbRating": float(metadata.get("movieIMDbRating", 0)),
                "total_reviews": int(metadata.get("total_reviews", 0)),
                "average_rating": float(metadata.get("average_rating", 0)),
                "has_poster": os.path.exists(
                    os.path.join("/app/database/archive", folder, "poster.jpg")
                )
            })
    
    return {
        "movies": movies,
        "total": len(movies)
    }


@router.post("/movies")
async def create_movie(
    movie: MovieCreate,
    admin: Admin = Depends(verify_admin_token)
):
    """Create a new movie (admin only)."""
    database_path = "/app/database/archive"
    movie_dir = os.path.join(database_path, movie.movie_name)
    
    if os.path.exists(movie_dir):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie with this name already exists"
        )
    
    # Create movie directory
    os.makedirs(movie_dir, exist_ok=True)
    
    # Convert genre string to array
    genre_array = [g.strip() for g in movie.genre.split(",")] if movie.genre else []
    
    # Create metadata
    metadata = {
        "title": movie.title,
        "movieDirector": movie.director or "",
        "movieGenres": genre_array,
        "releaseYear": movie.year or "",
        "movieIMDbRating": movie.imdb_rating or 0.0,
        "total_reviews": 0,
        "average_rating": 0.0,
        "commentCount": 0
    }
    
    # Write metadata.json
    metadata_path = os.path.join(movie_dir, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    
    # Create empty reviews CSV
    reviews_path = os.path.join(movie_dir, "movieReviews.csv")
    with open(reviews_path, "w", encoding="utf-8") as f:
        f.write("Date of Review,Email,Username,Dislikes,Likes,User's Rating out of 10,Review Title,Review,Reported,Report Reason,Report Count,Penalized,Hidden\n")
    
    return {
        "message": f"Movie '{movie.title}' created successfully",
        "movie": {
            "movie_name": movie.movie_name,
            "title": movie.title,
            "director": movie.director,
            "genre": ", ".join(genre_array),
            "year": movie.year,
            "movieIMDbRating": movie.imdb_rating
        }
    }


@router.put("/movies/{movie_name}")
async def update_movie(
    movie_name: str,
    movie_update: MovieUpdate,
    admin: Admin = Depends(verify_admin_token)
):
    """Update a movie's metadata (admin only)."""
    database_path = "/app/database/archive"
    movie_dir = os.path.join(database_path, movie_name)
    
    if not os.path.exists(movie_dir):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )
    
    # Read existing metadata
    metadata_path = os.path.join(movie_dir, "metadata.json")
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    # Update fields if provided
    if movie_update.title is not None:
        metadata["title"] = movie_update.title
    if movie_update.director is not None:
        metadata["movieDirector"] = movie_update.director
    if movie_update.genre is not None:
        genre_array = [g.strip() for g in movie_update.genre.split(",")] if movie_update.genre else []
        metadata["movieGenres"] = genre_array
    if movie_update.year is not None:
        metadata["releaseYear"] = movie_update.year
    if movie_update.imdb_rating is not None:
        metadata["movieIMDbRating"] = movie_update.imdb_rating
    
    # Write updated metadata
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    
    return {
        "message": f"Movie '{movie_name}' updated successfully",
        "movie": metadata
    }


@router.delete("/movies/{movie_name}")
async def delete_movie(
    movie_name: str,
    admin: Admin = Depends(verify_admin_token)
):
    """Delete a movie (admin only)."""
    database_path = "/app/database/archive"
    movie_dir = os.path.join(database_path, movie_name)
    
    if not os.path.exists(movie_dir):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )
    
    # Delete the entire movie directory
    import shutil
    shutil.rmtree(movie_dir)
    
    return {
        "message": f"Movie '{movie_name}' deleted successfully"
    }


@router.post("/movies/{movie_name}/poster")
async def upload_poster(
    movie_name: str,
    file: UploadFile = File(...),
    admin: Admin = Depends(verify_admin_token)
):
    """Upload a poster for a movie (admin only)."""
    database_path = "/app/database/archive"
    movie_dir = os.path.join(database_path, movie_name)
    
    if not os.path.exists(movie_dir):
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
    
    # Save poster
    poster_path = os.path.join(movie_dir, "poster.jpg")
    poster_data = await file.read()
    with open(poster_path, "wb") as f:
        f.write(poster_data)
    
    return {
        "message": f"Poster uploaded successfully for '{movie_name}'"
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
