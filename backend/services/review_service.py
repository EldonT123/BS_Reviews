# backend/services/review_service.py
"""Service layer for review management - handles all review business logic."""
import csv
import os
from datetime import datetime
from typing import Optional, List, Dict
from backend.services import file_service, user_service
from backend.models.user_model import User
from backend.routes.review_routes import ReviewRequest
from fastapi import HTTPException, status


RATING_LOWER_BOUND = 0
RATING_UPPER_BOUND = 10


def review_message_return(success: bool, review: ReviewRequest):
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update or add review"
        )

    if review.user.has_priority_reviews():
        message = (f"🌟 Review added successfully! "
                   f"As a {review.user.get_tier_display_name()}, "
                   f"your review will appear first!")
    else:
        message = "Review added successfully!"

    return {
        "message": message,
        "review": {
            "email": review.user.email,
            "username": review.user.email,
            "rating": review.rating,
            "comment": review.comment,
            "review_title": review.review_title
        }
    }

# ==================== Read Operations ====================


def read_reviews(movie_name: str) -> List[Dict]:
    """
    Read all reviews for a movie from CSV.
    Returns empty list if no reviews exist.
    """
    path = os.path.join(
        file_service.get_movie_folder(movie_name),
        "movieReviews.csv"
                       )

    if not os.path.exists(path):
        return []

    with open(path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)


def get_review_by_email(movie_name: str, email: str) -> Optional[Dict]:
    """
    Get a specific user's review for a movie by email.
    Returns None if review doesn't exist.
    """
    reviews = read_reviews(movie_name)

    for review in reviews:
        if review.get("Email", "") == email:
            return review

    return None


def user_has_reviewed(movie_name: str, email: str) -> bool:
    """Check if a user has already reviewed a movie."""
    return get_review_by_email(movie_name, email) is not None


# ==================== Write Operations ====================

def add_review(review: ReviewRequest) -> bool:
    """
    Add a new review to the movie's CSV file.
    Returns True if successful, False otherwise.
    """
    # Ensure movie folder exists
    movie_folder = file_service.get_movie_folder(review.movie_name)
    if not os.path.exists(movie_folder):
        file_service.create_movie_folder(review.movie_name)

    path = os.path.join(movie_folder, "movieReviews.csv")

    # Use current date if not provided
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    # Prepare new review row
    new_review = {
        "Date of Review": date,
        "User": review.user.username,
        "Likes": "0",
        "Dislikes": "0",
        "User's Rating out of 10": str(review.rating),
        "Review Title": review.review_title,
        "Review": review.comment
    }

    # Check if file exists and has content
    file_exists = os.path.exists(path) and os.path.getsize(path) > 0

    # Append to file (don't overwrite!)
    try:
        with open(path, 'a', encoding='utf-8', newline='') as f:
            fieldnames = [
                "Date of Review", "User", "Likes",
                "Dislike", "User's Rating out of 10",
                "Review Title", "Review"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            # Only write header if file is empty
            if not file_exists:
                writer.writeheader()

            writer.writerow(new_review)

        return True

    except Exception as e:
        print(f"Error adding review: {e}")
        return False


def update_review(review: ReviewRequest) -> bool:
    """
    Update an existing review.
    Returns True if successful, False if review not found.
    """
    reviews = read_reviews(review.movie_name)

    if not reviews:
        return False

    # Find and update the review
    updated = False
    for review in reviews:
        if review.get("Email", "") == review.user.email:
            review["User's Rating out of 10"] = str(review.rating)
            review["Review"] = review.comment
            review["Review Title"] = review.review_title
            review["Date of Review"] = datetime.now().strftime("%Y-%m-%d")
            updated = True
            break

    if not updated:
        return False

    # Write all reviews back to CSV
    try:
        movie_folder = file_service.get_movie_folder(review.movie_name)
        path = os.path.join(movie_folder, "movieReviews.csv")

        with open(path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "Date of Review", "User", "Usefulness Vote",
                "Total Votes", "User's Rating out of 10",
                "Review Title", "Review"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(reviews)

        return True

    except Exception as e:
        print(f"Error updating review: {e}")
        return False


def delete_review(email: str, movie_name: str) -> bool:
    """
    Delete a user's review.
    Returns True if successful, False if review not found.
    """
    reviews = read_reviews(movie_name)

    if not reviews:
        return False

    # Filter out the review to delete
    original_count = len(reviews)
    reviews = [
        r
        for r in reviews
        if r.get("Email", "") != email
    ]

    if len(reviews) == original_count:
        return False  # Review not found

    # Write remaining reviews back to CSV
    try:
        movie_folder = file_service.get_movie_folder(movie_name)
        path = os.path.join(movie_folder, "movieReviews.csv")

        with open(path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "Date of Review", "User", "Likes",
                "Dislikes", "User's Rating out of 10",
                "Review Title", "Review"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(reviews)

        return True

    except Exception as e:
        print(f"Error deleting review: {e}")
        return False


def report_review(email: str, movie_name: str, reason: str = "") -> bool:
    """
    Mark a user's review as reported.
    Returns True if successful, False if review not found.
    """
    reviews = read_reviews(movie_name)

    if not reviews:
        return False

    # Find the review
    reported = False
    for review in reviews:
        if review.get("Email", "") == email:
            # Add or update a 'Reported' column
            review["Reported"] = "Yes"
            review["Report Reason"] = reason
            reported = True
            break

    if not reported:
        return False

    # Write back all reviews
    try:
        movie_folder = file_service.get_movie_folder(movie_name)
        path = os.path.join(movie_folder, "movieReviews.csv")

        # Make sure 'Reported' and 'Report Reason' are in headers
        fieldnames = [
            "Date of Review", "User", "Likes",
            "Dislikes", "User's Rating out of 10",
            "Review Title", "Review", "Reported", "Report Reason"
        ]

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(reviews)

        return True

    except Exception as e:
        print(f"Error reporting review: {e}")
        return False


def handle_reported_review(
        email: str, movie_name: str, action: str = "keep"
) -> bool:
    """
    Admin handles a reported review.
    action: "remove" to delete it, "keep" to clear the report flag.
    """
    reviews = read_reviews(movie_name)
    if not reviews:
        return False

    updated = False
    for review in reviews:
        if (
            review.get("Email", "") == email
            and review.get("Reported") == "Yes"
        ):
            if action == "remove":
                return delete_review(email, movie_name)
            else:  # keep
                review["Reported"] = ""
                review["Report Reason"] = ""
            updated = True
            break

    if not updated:
        return False

    # Write updated reviews back to CSV (same as in report_review)
    movie_folder = file_service.get_movie_folder(movie_name)
    path = os.path.join(movie_folder, "movieReviews.csv")
    fieldnames = [
        "Date of Review", "User", "Likes",
        "Dislikes", "User's Rating out of 10",
        "Review Title", "Review", "Reported", "Report Reason"
    ]

    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(reviews)
        return True
    except Exception as e:
        print(f"Error handling reported review: {e}")
        return False


# ==================== Calculations & Statistics ====================

def recalc_average_rating(movie_name: str) -> float:
    """
    Calculate average rating from all reviews.
    Returns 0 if no valid ratings exist.
    """
    reviews = read_reviews(movie_name)

    if not reviews:
        return 0.0

    valid_ratings = []
    for review in reviews:
        rating_str = review.get("User's Rating out of 10", "").strip()
        if rating_str:
            try:
                rating = float(rating_str)
                valid_ratings.append(rating)
            except ValueError:
                continue

    if not valid_ratings:
        return 0.0

    return sum(valid_ratings) / len(valid_ratings)


def get_review_stats(movie_name: str) -> Dict:
    """
    Get comprehensive statistics about reviews for a movie.
    Includes tier breakdown and ratings.
    """
    reviews = read_reviews(movie_name)

    if not reviews:
        return {
            "total_reviews": 0,
            "average_rating": 0.0,
            "tier_breakdown": {
                "banana_slug": 0,
                "slug": 0,
                "snail": 0,
                "unknown": 0
            }
        }

    # Count reviews by tier
    tier_counts = {
        User.TIER_BANANA_SLUG: 0,
        User.TIER_SLUG: 0,
        User.TIER_SNAIL: 0,
        "unknown": 0
    }

    total_rating = 0
    valid_ratings_count = 0

    for review in reviews:
        username = review.get("User")
        user = user_service.get_user_by_email(username)

        if user:
            tier_counts[user.tier] = tier_counts.get(user.tier, 0) + 1
        else:
            tier_counts["unknown"] += 1

        # Add to rating calculation
        rating_str = review.get("User's Rating out of 10", "").strip()
        if rating_str:
            try:
                total_rating += float(rating_str)
                valid_ratings_count += 1
            except ValueError:
                pass

    avg_rating = (
        total_rating / valid_ratings_count
        if valid_ratings_count > 0
        else 0.0
    )

    return {
        "total_reviews": len(reviews),
        "average_rating": round(avg_rating, 2),
        "tier_breakdown": {
            "banana_slug": tier_counts.get(User.TIER_BANANA_SLUG, 0),
            "slug": tier_counts.get(User.TIER_SLUG, 0),
            "snail": tier_counts.get(User.TIER_SNAIL, 0),
            "unknown": tier_counts.get("unknown", 0)
        }
    }


# ==================== Sorting & Filtering ====================

def sort_reviews_by_tier(reviews: List[Dict]) -> List[Dict]:
    """
    Sort reviews so Banana Slug users' reviews appear first.
    Adds tier information to each review.
    """
    priority_reviews = []
    regular_reviews = []

    for review in reviews:
        username = review.get("User")
        user = user_service.get_user_by_email(username)

        # Add tier info to review
        if user:
            review["user_tier"] = user.tier
            review["user_tier_display"] = user.get_tier_display_name()

            # Separate by priority
            if user.has_priority_reviews():
                priority_reviews.append(review)
            else:
                regular_reviews.append(review)
        else:
            # User not found (legacy review), treat as regular
            review["user_tier"] = "unknown"
            review["user_tier_display"] = "User"
            regular_reviews.append(review)

    # Banana Slugs first, then everyone else
    return priority_reviews + regular_reviews


# ==================== Validation ====================

def validate_review_permission(email: str) -> tuple[bool, Optional[str]]:
    """
    Check if a user has permission to write reviews.
    Returns (has_permission, error_message)
    """
    user = user_service.get_user_by_email(email)

    if not user:
        return False, "User not found. Please sign up first."

    if not user.can_write_reviews():
        return False, (
                      f"🐌 {user.get_tier_display_name()} "
                      f"tier cannot write reviews. "
                      f"Upgrade to Slug tier to unlock this feature!"
                      )

    return True, None


def validate_edit_permission(email: str) -> tuple[bool, Optional[str]]:
    """
    Check if a user has permission to edit reviews.
    Returns (has_permission, error_message)
    """
    user = user_service.get_user_by_email(email)

    if not user:
        return False, "User not found"

    if not user.can_edit_own_reviews():
        return False, (
                      f"🐌 {user.get_tier_display_name()} "
                      f"tier cannot edit reviews."
                      )

    return True, None


def validate_rating(rating: float) -> tuple[bool, Optional[str]]:
    """
    Validate rating is within acceptable range.
    Returns (is_valid, error_message)
    """
    if not (RATING_LOWER_BOUND <= rating <= RATING_UPPER_BOUND):
        return False, f"Rating must be between {RATING_LOWER_BOUND} and {RATING_UPPER_BOUND}"

    return True, None
