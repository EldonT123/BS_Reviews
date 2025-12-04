# backend/routes/review_routes.py
"""Routes for review management - HTTP handling only."""
from fastapi import APIRouter, HTTPException, status, Depends
from backend.services import review_service
from backend.dependencies.auth import require_slug_tier
from backend.models.user_model import User
from backend.models.review_model import ReviewRequest
from backend.models.admin_model import Admin
from backend.middleware.auth_middleware import verify_admin_token

router = APIRouter()


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
    review: ReviewRequest,
    current_user: User = Depends(require_slug_tier)
):
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
    if review_service.user_has_reviewed(review.movie_name, current_user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=("You have already reviewed this movie. "
                    "Use PUT to update your review.")
        )

    # Add review
    success = review_service.add_review(review, current_user)

    review_message = review_service.review_message_return(
        success, review, current_user)
    return review_message


@router.put("/{movie_name}")
async def update_review(
    review: ReviewRequest,
    current_user: User = Depends(require_slug_tier)
):
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
    if not review_service.user_has_reviewed(
            review.movie_name, current_user.email):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=("You haven't written a review for this movie yet. "
                    "Use POST to create a new review.")
        )

    # Update review
    success = review_service.update_review(review, current_user)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update review"
        )

    review_message = review_service.review_message_return(
        success, review, current_user)
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


@router.post("/{movie_name}/report")
async def report_review_route(
    movie_name: str,
    email: str,  # email of the user being reported
    reason: str = "",
    current_user: User = Depends(require_slug_tier)
):
    """
    Report a review for a movie.
    Requires: Authentication + Slug tier or above.
    """
    # Ensure the review exists
    if not review_service.user_has_reviewed(movie_name, email):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review to report not found"
        )

    # Call the service method
    result = review_service.report_review(email, movie_name, reason)
    return result  # Already a dict {success: bool, message: str}


@router.put("/{movie_name}/reported")
async def handle_reported_review_route(
    movie_name: str,
    email: str,  # email of the review being handled
    remove: bool = False,
    current_admin: Admin = Depends(verify_admin_token)
):
    """
    Admin handles a reported review.
    remove=True -> attempt to delete the review
    remove=False -> attempt to keep (reset) the review
    Only admins can perform this action.
    """
    result = review_service.handle_reported_review(email, movie_name, remove)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    return result


@router.post("/reviews/{movie_name}/like")
def route_like_review(movie_name: str, email: str):
    success = review_service.like_review(email, movie_name)
    if not success:
        raise HTTPException(status_code=404, detail="Review not found.")
    return {"success": True, "message": "Review liked."}


@router.post("/reviews/{movie_name}/dislike")
def route_dislike_review(movie_name: str, email: str):
    success = review_service.dislike_review(email, movie_name)
    if not success:
        raise HTTPException(status_code=404, detail="Review not found.")
    return {"success": True, "message": "Review disliked."}
