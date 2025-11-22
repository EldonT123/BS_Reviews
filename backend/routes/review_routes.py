# backend/routes/review_routes.py
"""Routes for review management - HTTP handling only."""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from backend.services import review_service, user_service
from backend.dependencies.auth import get_current_user, require_slug_tier
from backend.models.user_model import User

router = APIRouter()

# ==================== Request Models ====================


# This class alows for reviews and ratings to be created.
# In our case, a rating is just a review without any comment.
class ReviewInput(BaseModel):
    """Model for creating reviews."""
    rating: float
    comment: str = ""
    review_title: str = ""


class ReviewUpdate(BaseModel):
    """Model for updating reviews."""
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
async def post_review(
    movie_name: str,
    review: ReviewInput,
    current_user: User = Depends(require_slug_tier)
):    
    """
    Add a review to a movie.
    Requires: Authentication + Slug tier or above (Snails cannot write reviews).
    """
    # Example run
    # curl -X POST http://localhost:8000/reviews/Joker 
    # -H "Content-Type: application/json" 
    # -H "Authorization: Bearer <session id>" 
    # -d "{\"rating\": 9.5, \"comment\": \"Amazing movie!\", \"review_title\": \"Mind-bending\"}"

    # User is already authenticated and has Slug tier via dependency
    # Use authenticated user's email instead of trusting client input
    email = current_user.email

    # Validate rating
    is_valid, error_msg = review_service.validate_rating(review.rating)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Check if user already reviewed this movie
    if review_service.user_has_reviewed(movie_name, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=("You have already reviewed this movie. "
                    "Use PUT to update your review.")
        )

    # Add review
    success = review_service.add_review(
        username=email,
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

    if current_user.has_priority_reviews():
        message = (f"🌟 Review added successfully! "
                   f"As a {current_user.get_tier_display_name()}, "
                   f"your review will appear first!")
    else:
        message = "Review added successfully!"

    return {
        "message": message,
        "review": {
            "email": email,
            "rating": review.rating,
            "comment": review.comment,
            "review_title": review.review_title
        }
    }


@router.put("/{movie_name}")
async def update_review(
    movie_name: str,
    review: ReviewUpdate,
    current_user: User = Depends(require_slug_tier)
):
    """
    Update an existing review.
    Requires: Authentication + Slug tier or above.
    Users can only edit their own reviews.
    """
    # Example run
    # curl -X PUT http://localhost:8000/reviews/Joker 
    # -H "Content-Type: application/json" -H "Authorization: Bearer <session id>" 
    # -d "{\"rating\": 9.5, \"comment\": \"testing update\", \"review_title\": \"even better the second time\"}"

    # Use authenticated user's email
    email = current_user.email

    # Validate rating
    is_valid, error_msg = review_service.validate_rating(review.rating)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Check if review exists
    if not review_service.user_has_reviewed(movie_name, email):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=("You haven't written a review for this movie yet. "
                    "Use POST to create a new review.")
        )

    # Update review
    success = review_service.update_review(
        username=email,
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
            "email": email,
            "rating": review.rating,
            "comment": review.comment,
            "review_title": review.review_title
        }
    }


@router.delete("/{movie_name}")
async def delete_review(
    movie_name: str,
    current_user: User = Depends(require_slug_tier)
):
    """
    Delete a user's review.
    Requires: Authentication + Slug tier or above.
    Users can only delete their own reviews.
    """
    # Example run
    # curl -X DELETE http://localhost:8000/api/reviews/Inception
    # -H "Authorization: Bearer <session_id>"

    # Use authenticated user's email
    email = current_user.email

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
