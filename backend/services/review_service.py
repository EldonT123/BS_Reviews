# backend/services/review_service.py
"""Service layer for review management - handles all review business logic."""
import csv
import os
from datetime import datetime
from typing import Optional, List, Dict
from backend.services import file_service, user_service
from backend.models.user_model import User
from backend.models.review_model import ReviewRequest
from fastapi import HTTPException, status


RATING_LOWER_BOUND = 0
RATING_UPPER_BOUND = 10
REPORT_THRESHOLD = 3
CSV_FIELDNAMES = [
    "Date of Review",
    "Email",
    "Username",
    "Dislikes",
    "Likes",
    "User's Rating out of 10",
    "Review Title",
    "Review",
    "Reported",
    "Report Reason",
    "Report Count",
    "Penalized",
    "Hidden",
    "Liked By",  # New: semicolon-separated list of user emails who liked
    "Disliked By"  # New: semicolon-separated list of user emails who disliked
]


def review_message_return(success: bool, review: ReviewRequest, user: User):
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update or add review"
        )

    if user.has_priority_reviews():
        message = (f"🌟 Review added successfully! "
                   f"As a {user.get_tier_display_name()}, "
                   f"your review will appear first!")
    else:
        message = "Review added successfully!"

    return {
        "message": message,
        "review": {
            "email": user.email,
            "username": user.email,
            "rating": review.rating,
            "comment": review.comment,
            "review_title": review.review_title
        }
    }

# ==================== Read Operations ====================


def read_reviews(movie_name: str) -> list[dict]:
    """
    Read all reviews for a movie from CSV.
    Ensures reporting-related fields always have default values.
    Returns empty list if no reviews exist.
    """
    path = get_reviews_path(movie_name)

    if not os.path.exists(path):
        return []

    with open(path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        reviews = []
        for row in reader:
            review = {field: row.get(field, "") for field in CSV_FIELDNAMES}

            # Normalize reporting-related fields
            review["Reported"] = review.get("Reported") or "No"
            review["Report Reason"] = review.get("Report Reason") or ""
            review["Report Count"] = review.get("Report Count") or "0"
            review["Hidden"] = review.get("Hidden") or "No"
            review["Penalized"] = review.get("Penalized") or "No"

            # Normalize vote tracking fields
            review["Liked By"] = review.get("Liked By") or ""
            review["Disliked By"] = review.get("Disliked By") or ""

            reviews.append(review)

    return reviews


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

def write_reviews(movie_name: str, reviews: List[Dict]) -> bool:
    """
    Write all reviews back to CSV.
    Returns True if successful, False otherwise.
    """
    try:
        path = get_reviews_path(movie_name)

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()
            writer.writerows(reviews)

        return True
    except Exception as e:
        print(f"Error writing reviews: {e}")
        return False


def get_reviews_path(movie_name: str) -> str:
    """Get the path to the reviews CSV for a movie."""
    return os.path.join(
        file_service.get_movie_folder(movie_name),
        "movieReviews.csv"
    )


def get_user_reviews(user_email: str) -> List[Dict]:
    """
    Get all reviews written by a specific user across all movies.
    Returns a list of reviews with movie names attached.
    """
    from backend.services import file_service

    user_reviews = []

    # Get all movie folders
    movies_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../database/archive")
    )
    
    # Iterate through all movie folders
    for movie_folder in os.listdir(movies_dir):
        movie_path = os.path.join(movies_dir, movie_folder)

        if not os.path.isdir(movie_path):
            continue

        # Check if this movie has reviews
        reviews_file = os.path.join(movie_path, "movieReviews.csv")
        if not os.path.exists(reviews_file):
            continue

        # Read reviews for this movie
        try:
            with open(reviews_file, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("Email", "").lower() == user_email.lower():
                        # Found a review by this user
                        review_data = {
                            field: row.get(
                                field, "") for field in CSV_FIELDNAMES}
                        review_data[
                            "movie_name"] = movie_folder  # Add movie name
                        review_data[
                            "Hidden"] = review_data.get("Hidden") or "No"

                        # Only include non-hidden reviews
                        if review_data["Hidden"] != "Yes":
                            user_reviews.append(review_data)
        except Exception as e:
            print(f"Error reading reviews from {movie_folder}: {e}")
            continue

    # Sort by date (most recent first)
    user_reviews.sort(
        key=lambda x: x.get("Date of Review", ""),
        reverse=True
    )

    return user_reviews


def add_review(review: ReviewRequest, user: User) -> bool:
    """
    Add a new review to the movie's CSV file.
    Returns True if successful, False otherwise.
    """
    # Ensure movie folder exists
    movie_folder = file_service.get_movie_folder(review.movie_name)
    if not os.path.exists(movie_folder):
        file_service.create_movie_folder(review.movie_name)

    path = get_reviews_path(review.movie_name)

    # Always uses current date
    date = datetime.now().strftime("%Y-%m-%d")

    # Prepare new review row
    new_review = {
        "Date of Review": date,
        "Email": user.email,
        "Username": user.username,
        "Dislikes": "0",
        "Likes": "0",
        "User's Rating out of 10": str(review.rating),
        "Review Title": review.review_title,
        "Review": review.comment,
        "Reported": "No",
        "Report Reason": "",
        "Report Count": "0",
        "Penalized": "No",
        "Hidden": "No",
        "Liked By": "",
        "Disliked By": ""
    }

    # Check if file exists and has content
    file_exists = os.path.exists(path) and os.path.getsize(path) > 0

    # Append to file (don't overwrite!)
    try:
        with open(path, 'a', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)

            # Only write header if file is empty
            if not file_exists:
                writer.writeheader()

            writer.writerow(new_review)

        return True

    except Exception as e:
        print(f"Error adding review: {e}")
        return False


def update_review(review: ReviewRequest, user: User) -> bool:
    """
    Update an existing review.
    Returns True if successful, False if review not found.
    """
    reviews = read_reviews(review.movie_name)

    if not reviews:
        return False

    # Find and update the review
    updated = False
    for r in reviews:
        if r.get("Email", "") == user.email:
            r["User's Rating out of 10"] = str(review.rating)
            r["Review"] = review.comment
            r["Review Title"] = review.review_title
            r["Date of Review"] = datetime.now().strftime("%Y-%m-%d")
            updated = True
            break

    if not updated:
        return False

    # Write all reviews back to CSV
    return write_reviews(review.movie_name, reviews)


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
    return write_reviews(movie_name, reviews)


def report_review(email: str, movie_name: str, reason: str = "") -> bool:
    """
    Report a user's review for a movie.
    Increments report count, appends reason, and hides review if
    threshold reached. Returns False if the review does not exist.
    """
    # Check if the user has a review for this movie
    if not user_has_reviewed(movie_name, email):
        return False  # No review exists to report

    # Read all reviews for the movie
    reviews = read_reviews(movie_name)

    # Find the review in the list and update it
    for r in reviews:
        if r.get("Email") == email:
            # Mark as reported
            r["Reported"] = "Yes"

            # Increment Report Count
            current_count = int(r.get("Report Count") or 0)
            current_count += 1
            r["Report Count"] = str(current_count)

            # Append the new reason (semi-colon separated)
            existing_reasons = r.get("Report Reason", "")
            if existing_reasons:
                r["Report Reason"] = existing_reasons + ";" + reason
            else:
                r["Report Reason"] = reason

            # Set Hidden if threshold reached
            if current_count >= REPORT_THRESHOLD:
                r["Hidden"] = "Yes"

            # Write all reviews back to the movie CSV
            return write_reviews(movie_name, reviews)

    # Safety fallback (shouldn't reach here due to user_has_reviewed)
    return False


def handle_reported_review(
        email: str, movie_name: str, remove: bool = False
) -> dict:
    """
    Admin handles a reported review.

    remove: True -> attempt to delete the review
            False -> attempt to keep the review (reset report info)

    Returns a dictionary with:
        {
            "success": bool,
            "message": str
        }
    """
    reviews = read_reviews(movie_name)
    if not reviews:
        return {
            "success": False, "message": "No reviews exist for this movie."
        }

    for review in reviews:
        if review["Email"] == email and review["Reported"] == "Yes":
            if remove:
                if review["Penalized"] == "Yes":
                    success = delete_review(email, movie_name)
                    msg = (
                        "Review deleted successfully (user was penalized)."
                        if success
                        else "Review could not be deleted."
                    )
                    return {"success": success, "message": msg}
                else:
                    return {
                        "success": False, "message": "Cannot delete review: "
                        "user must be penalized first."
                    }
            else:
                if review["Penalized"] == "Yes":
                    return {
                        "success": False, "message": "Cannot keep review: "
                        "a penalized review cannot be reset."
                    }
                else:
                    review["Reported"] = "No"
                    review["Report Reason"] = ""
                    review["Report Count"] = "0"
                    review["Hidden"] = "No"
                    success = write_reviews(movie_name, reviews)
                    msg = (
                        "Review kept and report info reset successfully."
                        if success
                        else "Failed to reset review report info."
                    )
                    return {"success": success, "message": msg}

    return {
        "success": False, "message": "No reported review found for this user."
    }


def user_has_voted(review: Dict, voter_email: str, vote_type: str) -> bool:
    """
    Check if a user has already voted on a review.

    Args:
        review: The review dictionary
        voter_email: Email of the user voting
        vote_type: Either "like" or "dislike"

    Returns:
        True if user has already voted this way, False otherwise
    """
    field = "Liked By" if vote_type == "like" else "Disliked By"
    voters = review.get(field, "").split(";")
    return voter_email.lower() in [
        v.strip().lower() for v in voters if v.strip()]


def add_vote(review: Dict, voter_email: str, vote_type: str) -> None:
    """
    Add a user's vote to a review.

    Args:
        review: The review dictionary to modify
        voter_email: Email of the user voting
        vote_type: Either "like" or "dislike"
    """
    field = "Liked By" if vote_type == "like" else "Disliked By"
    count_field = "Likes" if vote_type == "like" else "Dislikes"

    # Add voter email
    current_voters = review.get(field, "")
    if current_voters:
        review[field] = current_voters + ";" + voter_email
    else:
        review[field] = voter_email

    # Increment count
    current_count = int(review.get(count_field, "0"))
    review[count_field] = str(current_count + 1)


def remove_vote(review: Dict, voter_email: str, vote_type: str) -> None:
    """
    Remove a user's vote from a review (for switching votes).

    Args:
        review: The review dictionary to modify
        voter_email: Email of the user whose vote to remove
        vote_type: Either "like" or "dislike"
    """
    field = "Liked By" if vote_type == "like" else "Disliked By"
    count_field = "Likes" if vote_type == "like" else "Dislikes"

    # Remove voter email
    voters = [v.strip() for v in review.get(field, "").split(";") if v.strip()]
    voters = [v for v in voters if v.lower() != voter_email.lower()]
    review[field] = ";".join(voters)

    # Decrement count
    current_count = int(review.get(count_field, "0"))
    review[count_field] = str(max(0, current_count - 1))


def like_review(
        review_author_email: str, movie_name: str, voter_email: str) -> dict:
    """
    Like a review. Users can only like once,
    and liking removes any existing dislike.

    Returns:
        dict with "success" (bool) and "message" (str)
    """
    reviews = read_reviews(movie_name)

    for r in reviews:
        if r["Email"] == review_author_email:
            # Check if already liked
            if user_has_voted(r, voter_email, "like"):
                return {
                    "success": False,
                    "message": "You have already liked this review"
                }

            # Remove dislike if exists
            if user_has_voted(r, voter_email, "dislike"):
                remove_vote(r, voter_email, "dislike")

            # Add like
            add_vote(r, voter_email, "like")

            # Save changes
            success = write_reviews(movie_name, reviews)
            return {
                "success": success,
                "message": ("Review liked successfully"
                            if success else "Failed to like review"),
                "likes": int(r["Likes"]),
                "dislikes": int(r["Dislikes"])
            }

    return {
        "success": False,
        "message": "Review not found"
    }


def dislike_review(
        review_author_email: str, movie_name: str, voter_email: str) -> dict:
    """
    Dislike a review. Users can only dislike once,
    and disliking removes any existing like.

    Returns:
        dict with "success" (bool) and "message" (str)
    """
    reviews = read_reviews(movie_name)

    for r in reviews:
        if r["Email"] == review_author_email:
            # Check if already disliked
            if user_has_voted(r, voter_email, "dislike"):
                return {
                    "success": False,
                    "message": "You have already disliked this review"
                }

            # Remove like if exists
            if user_has_voted(r, voter_email, "like"):
                remove_vote(r, voter_email, "like")

            # Add dislike
            add_vote(r, voter_email, "dislike")

            # Save changes
            success = write_reviews(movie_name, reviews)
            return {
                "success": success,
                "message": ("Review disliked successfully"
                            if success else "Failed to dislike review"),
                "likes": int(r["Likes"]),
                "dislikes": int(r["Dislikes"])
            }

    return {
        "success": False,
        "message": "Review not found"
    }


def get_user_vote_status(
        movie_name: str, review_author_email: str, voter_email: str) -> dict:
    """
    Get the current vote status of a user for a specific review.

    Returns:
        dict with "has_liked" (bool) and "has_disliked" (bool)
    """
    review = get_review_by_email(movie_name, review_author_email)

    if not review:
        return {"has_liked": False, "has_disliked": False}

    return {
        "has_liked": user_has_voted(review, voter_email, "like"),
        "has_disliked": user_has_voted(review, voter_email, "dislike")
    }


def mark_all_reviews_penalized(email: str) -> dict:
    """
    Mark all reviews by a user as penalized across all movies.
    This should be called when an admin bans a user from reviewing.

    Returns:
        {
            "success": bool,
            "movies_affected": list[str],
            "reviews_marked": int
        }
    """

    movies_affected = []
    reviews_marked = 0

    # Get all movie folders
    data_folder = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../data/movies")
    )

    if not os.path.exists(data_folder):
        return {
            "success": True,
            "movies_affected": [],
            "reviews_marked": 0
        }

    # Iterate through all movie folders
    for movie_name in os.listdir(data_folder):
        movie_path = os.path.join(data_folder, movie_name)
        if not os.path.isdir(movie_path):
            continue

        reviews_path = os.path.join(movie_path, "movieReviews.csv")
        if not os.path.exists(reviews_path):
            continue

        # Read reviews for this movie
        reviews = read_reviews(movie_name)
        modified = False

        # Mark user's reviews as penalized
        for review in reviews:
            if (
                review.get("Email") == email
                and review.get("Penalized") != "Yes"
            ):
                review["Penalized"] = "Yes"
                review["Hidden"] = "Yes"  # Also hide penalized reviews
                modified = True
                reviews_marked += 1

        # Write back if any changes were made
        if modified:
            write_reviews(movie_name, reviews)
            movies_affected.append(movie_name)

    return {
        "success": True,
        "movies_affected": movies_affected,
        "reviews_marked": reviews_marked
    }


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
        email = review.get("Email")
        user = user_service.get_user_by_email(email)

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
        email = review.get("Email")
        user = user_service.get_user_by_email(email)

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
        msg = (
            f"Rating must be between {RATING_LOWER_BOUND} "
            f"and {RATING_UPPER_BOUND}"
        )
        return False, msg

    return True, None
