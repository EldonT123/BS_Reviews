# backend/routes/review_routes.py
"""Routes for review management - HTTP handling only."""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from backend.services import review_service, user_service
from backend.models.user_model import User

router = APIRouter()

# ==================== Request Models ====================

class ReviewInput(BaseModel):
    """Model for creating reviews."""
    email: EmailStr
    rating: float
    comment: str
    review_title: str = ""


class ReviewUpdate(BaseModel):
    """Model for updating reviews."""
    email: EmailStr
    rating: float
    comment: str
    review_title: str = ""


# ==================== Routes ====================

@router.get("/{movie_name}")
async def get_reviews(movie_name: str):
    """
    Get all reviews for a movie.
    Reviews from Banana Slug users appear first.
    """
    reviews = review_service.read_reviews(movie_name)
    
    if not reviews:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No reviews found for this movie"
        )
    
    # Sort with Banana Slugs first
    sorted_reviews = review_service.sort_reviews_by_tier(reviews)
    
    return {
        "movie": movie_name,
        "total_reviews": len(sorted_reviews),
        "reviews": sorted_reviews
    }


@router.post("/{movie_name}")
async def post_review(movie_name: str, review: ReviewInput):
    """
    Add a review to a movie.
    Requires: Slug tier or above (Snails cannot write reviews).
    """
    # Validate permission
    has_permission, error_msg = review_service.validate_review_permission(review.email)
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_msg
        )
    
    # Validate rating
    is_valid, error_msg = review_service.validate_rating(review.rating)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Check if user already reviewed this movie
    if review_service.user_has_reviewed(movie_name, review.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this movie. Use PUT to update your review."
        )
    
    # Add review
    success = review_service.add_review(
        username=review.email,
        movie_name=movie_name,
        rating=review.rating,
        comment=review.comment,
        review_title=review.review_title
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add review"
        )
    
    # Get user for custom message
    user = user_service.get_user_by_email(review.email)
    
    if user and user.has_priority_reviews():
        message = f"🍌 Review added successfully! As a {user.get_tier_display_name()}, your review will appear first!"
    else:
        message = "Review added successfully!"
    
    return {
        "message": message,
        "review": {
            "email": review.email,
            "rating": review.rating,
            "comment": review.comment,
            "review_title": review.review_title
        }
    }


@router.put("/{movie_name}")
async def update_review(movie_name: str, review: ReviewUpdate):
    """
    Update an existing review.
    Requires: Slug tier or above.
    Users can only edit their own reviews.
    """
    # Validate permission
    has_permission, error_msg = review_service.validate_edit_permission(review.email)
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_msg
        )
    
    # Validate rating
    is_valid, error_msg = review_service.validate_rating(review.rating)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Check if review exists
    if not review_service.user_has_reviewed(movie_name, review.email):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You haven't written a review for this movie yet. Use POST to create a new review."
        )
    
    # Update review
    success = review_service.update_review(
        username=review.email,
        movie_name=movie_name,
        rating=review.rating,
        comment=review.comment,
        review_title=review.review_title
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update review"
        )
    
    return {
        "message": "Review updated successfully!",
        "review": {
            "email": review.email,
            "rating": review.rating,
            "comment": review.comment,
            "review_title": review.review_title
        }
    }


@router.delete("/{movie_name}/{email}")
async def delete_review(movie_name: str, email: EmailStr):
    """
    Delete a user's review.
    Users can only delete their own reviews.
    """
    # Validate permission
    has_permission, error_msg = review_service.validate_edit_permission(email)
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_msg
        )
    
    # Delete review
    success = review_service.delete_review(username=email, movie_name=movie_name)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    return {"message": "Review deleted successfully"}


@router.get("/{movie_name}/stats")
async def get_review_stats(movie_name: str):
    """
    Get statistics about reviews for a movie.
    Shows breakdown by tier and average rating.
    """
    stats = review_service.get_review_stats(movie_name)
    
    if stats["total_reviews"] == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No reviews found for this movie"
        )
    
    return {
        "movie": movie_name,
        **stats
    }


@router.get("/{movie_name}/average")
async def get_average_rating(movie_name: str):
    """Get the average rating for a movie."""
    avg_rating = review_service.recalc_average_rating(movie_name)
    
    return {
        "movie": movie_name,
        "average_rating": round(avg_rating, 2)
    }