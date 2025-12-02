# backend/routes/review_routes.py
"""Routes for review management - HTTP handling only."""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from backend.services import review_service
from backend.dependencies.auth import require_slug_tier
from backend.models.user_model import User

router = APIRouter()

# ==================== Request Models ====================


# This class alows for reviews and ratings to be created.
# In our case, a rating is just a review without any comment.
class ReviewRequest(BaseModel):
    """Model for creating reviews."""
    movie_name: str
    rating: float
    comment: str = ""
    review_title: str = ""
    user: User = Depends(require_slug_tier)


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
async def post_review(review: ReviewRequest):
    """
    Add a review to a movie.
    Requires: Authentication + Slug tier or above.
    """

    # User is already authenticated and has Slug tier via dependency
    # Use authenticated user's email instead of trusting client input

    # Validate rating
    is_valid, error_msg = review_service.validate_rating(review.rating)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Check if user already reviewed this movie
    if review_service.user_has_reviewed(review.movie_name, review.user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=("You have already reviewed this movie. "
                    "Use PUT to update your review.")
        )

    # Add review
    success = review_service.add_review(review)

    review_message = review_service.review_message_return(success, review)
    return review_message


@router.put("/{movie_name}")
async def update_review(review: ReviewRequest):
    """
    Update an existing review.
    Requires: Authentication + Slug tier or above.
    Users can only edit their own reviews.
    """

    # Validate rating
    is_valid, error_msg = review_service.validate_rating(review.rating)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Check if review exists
    if not review_service.user_has_reviewed(review.movie_name, review.user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=("You haven't written a review for this movie yet. "
                    "Use POST to create a new review.")
        )

    # Update review
    success = review_service.update_review(review)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update review"
        )

    review_message = review_service.review_message_return(success, review)
    return review_message


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
    success = review_service.delete_review(
        username=email, movie_name=movie_name
        )

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
