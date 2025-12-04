"""Tests for review_service module."""
import pytest  # noqa: F401
import os,tempfile,shutil
from pathlib import Path  # noqa: F401
from backend.services import review_service, file_service, user_service
from backend.models.review_model import ReviewRequest
from backend.models.user_model import User

@pytest.fixture
def isolated_user_service():
    """
    Ensure user service operations don't affect real data.
    Mock the CSV paths to use temporary files.
    """
    import tempfile
    import os
    from unittest.mock import patch
    
    # Create temporary directory for test data
    temp_dir = tempfile.mkdtemp()
    temp_user_csv = os.path.join(temp_dir, "test_users.csv")
    temp_bookmark_csv = os.path.join(temp_dir, "test_bookmarks.csv")
    
    with patch('backend.services.user_service.USER_CSV_PATH', temp_user_csv), \
         patch('backend.services.user_service.BOOKMARK_CSV_PATH', temp_bookmark_csv):
        yield
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except:
        pass

@pytest.fixture
def test_user(isolated_movie_env, isolated_user_service):
    """Create a test user for reviews."""
    email = "test@example.com"
    
    # Create a user with Slug tier (can write reviews)
    user = user_service.create_user(
        email=email,
        username="test_user",
        password="password123",
        tier=User.TIER_SLUG,
        tokens=0
    )

    yield user

    # Cleanup after test
    try:
        user_service.delete_user(email)
    except Exception:
        pass


@pytest.fixture
def test_user_2(isolated_movie_env, isolated_user_service):
    """Create a second test user."""
    email = "test2@example.com"
    
    user = user_service.create_user(
        email=email,
        username="test_user_2",
        password="password123",
        tier=User.TIER_SLUG,
        tokens=0
    )

    yield user

    # Cleanup after test
    try:
        user_service.delete_user(email)
    except Exception:
        pass


@pytest.fixture
def test_user_3(isolated_movie_env, isolated_user_service):
    """Create a third test user."""
    email = "test3@example.com"
    
    user = user_service.create_user(
        email=email,
        username="test_user_3",
        password="password123",
        tier=User.TIER_SLUG,
        tokens=0
    )

    yield user

    # Cleanup after test
    try:
        user_service.delete_user(email)
    except Exception:
        pass


@pytest.fixture(autouse=True)
def cleanup_review_files():
    """Ensure review files are properly closed and cleaned up."""
    yield
    # Force garbage collection to close any open file handles
    import gc
    gc.collect()


def test_add_multiple_reviews_and_average(isolated_movie_env, test_user, test_user_2, test_user_3):
    """
    Unit test - positive path / core logic
    Test adding multiple reviews and calculating average
    using isolated movie environment
    """
    movie_name = "anymovie"

    # Create the movie folder first
    file_service.create_movie_folder(movie_name)

    # Add multiple reviews using ReviewRequest and User objects
    review1 = ReviewRequest(
        movie_name=movie_name,
        rating=5.0,
        comment="Perfect!",
        review_title="Amazing"
    )
    review_service.add_review(review1, test_user)

    review2 = ReviewRequest(
        movie_name=movie_name,
        rating=3.0,
        comment="It was okay",
        review_title="Meh"
    )
    review_service.add_review(review2, test_user_2)

    review3 = ReviewRequest(
        movie_name=movie_name,
        rating=4.0,
        comment="Pretty good",
        review_title="Nice"
    )
    review_service.add_review(review3, test_user_3)

    reviews = review_service.read_reviews(movie_name)
    assert len(reviews) == 3, "Should have three reviews"

    avg_rating = review_service.recalc_average_rating(movie_name)
    assert avg_rating == 4.0, (
        f"Average of 5, 3, and 4 should be 4.0, got {avg_rating}"
    )


def test_read_reviews_with_real_data(temp_real_data_copy):
    """Integration test - Positive path:
    Read reviews from real data copy.
    """
    # Find an existing movie folder
    existing_movie = None
    for item in temp_real_data_copy.iterdir():
        if item.is_dir():
            existing_movie = item.name
            break

    assert existing_movie is not None, (
        "No movie folders found in real data copy"
    )

    # Should be able to read reviews without errors
    reviews = review_service.read_reviews(existing_movie)
    assert isinstance(reviews, list), "Should return a list of reviews"


def test_add_review_to_real_data(temp_real_data_copy, test_user):
    """Integration test: Positive path / Real write
    Add review to existing movie from real data copy."""
    # Find an existing movie folder
    existing_movie = None
    for item in temp_real_data_copy.iterdir():
        if item.is_dir():
            existing_movie = item.name
            break

    assert existing_movie is not None, (
        "No movie folders found in real data copy"
    )
    # Get initial review count
    initial_reviews = review_service.read_reviews(existing_movie)
    initial_count = len(initial_reviews)

    # Add a new review with ReviewRequest and User
    review = ReviewRequest(
        movie_name=existing_movie,
        rating=5.0,
        comment="Excellent movie!",
        review_title="Test Review"
    )
    review_service.add_review(review, test_user)

    # Verify review was added
    updated_reviews = review_service.read_reviews(existing_movie)
    new_count = len(updated_reviews)

    assert new_count == initial_count + 1, (
        "Review count should increase by 1. "
        f"Was {initial_count}, now {new_count}"
    )

    # Verify the new review exists (using Email column)
    assert any(
        r["Email"] == test_user.email and
        float(r["User's Rating out of 10"]) == 5.0
        for r in updated_reviews
    ), "New review not found in reviews"

    # Verify average rating can be calculated
    avg_rating = review_service.recalc_average_rating(existing_movie)
    assert avg_rating > 0, "Average rating should be positive"


def test_review_with_special_characters(isolated_movie_env):
    """Unit test - Edge case / Unicode and special characters:
    Test adding reviews with special characters and unicode."""
    movie_name = "test_movie"
    file_service.create_movie_folder(movie_name)

    email = "user_français@example.com"

    # Clean up if user exists
    existing_user = user_service.get_user_by_email(email)
    if existing_user:
        user_service.delete_user(email)

    # Create user with special characters
    user = user_service.create_user(
        email=email,
        username="user_français",
        password="password123",
        tier=User.TIER_SLUG
    )

    # Add review with special characters
    review = ReviewRequest(
        movie_name=movie_name,
        rating=4.5,
        comment="Très bon film! 🎬 Amazing & wonderful.",
        review_title="Incroyable!"
    )
    review_service.add_review(review, user)

    reviews = review_service.read_reviews(movie_name)
    assert len(reviews) == 1
    assert "français" in reviews[0]["Email"]
    assert "Très bon" in reviews[0]["Review"]

    # Cleanup
    try:
        user_service.delete_user(email)
    except Exception:
        pass


def test_report_review_integration(isolated_movie_env, test_user):
    """Integration test: Report a review and check the CSV is updated."""
    movie_name = "integration_movie"
    file_service.create_movie_folder(movie_name)

    # Add a review first
    review = ReviewRequest(
        movie_name=movie_name,
        rating=8.0,
        comment="Great movie!",
        review_title="Loved it"
    )
    review_service.add_review(review, test_user)

    # Report the review once
    result = review_service.report_review(
        email=test_user.email,
        movie_name=movie_name,
        reason="Offensive language"
    )
    assert result is True

    reviews = review_service.read_reviews(movie_name)
    reported_review = next(r for r in reviews if r["Email"] == test_user.email)
    assert reported_review["Reported"] == "Yes"
    assert reported_review["Report Reason"] == "Offensive language"
    assert reported_review["Report Count"] == "1"
    assert reported_review.get("Hidden", "No") == "No"

    # Report the same review again with another reason
    result2 = review_service.report_review(
        email=test_user.email,
        movie_name=movie_name,
        reason="Spam"
    )
    assert result2 is True

    reviews = review_service.read_reviews(movie_name)
    reported_review = next(r for r in reviews if r["Email"] == test_user.email)
    # Verify multiple reasons are appended
    assert reported_review["Report Reason"] == "Offensive language;Spam"
    # Report count incremented
    assert reported_review["Report Count"] == "2"
    # Hidden still No (assuming threshold >2)
    assert reported_review.get("Hidden", "No") == "No"

    # Test threshold logic
    # Report until it reaches REPORT_THRESHOLD
    for _ in range(review_service.REPORT_THRESHOLD - 2):
        review_service.report_review(
            email=test_user.email,
            movie_name=movie_name,
            reason="Another reason"
        )
    reviews = review_service.read_reviews(movie_name)
    reported_review = next(r for r in reviews if r["Email"] == test_user.email)
    assert reported_review["Report Count"] == (
        str(review_service.REPORT_THRESHOLD)
    )
    assert reported_review["Hidden"] == "Yes"


def test_handle_reported_review_integration(isolated_movie_env, test_user_2):
    """Integration test: Handle a reported review (remove it)."""
    movie_name = "integration_movie_handle"
    file_service.create_movie_folder(movie_name)

    # Add a review first
    review = ReviewRequest(
        movie_name=movie_name,
        rating=7.0,
        comment="Pretty good",
        review_title="Meh"
    )
    review_service.add_review(review, test_user_2)

    # Report the review
    review_service.report_review(
        email=test_user_2.email,
        movie_name=movie_name,
        reason="Spam"
    )

    # Case 1: Try removing when penalized = No → should fail
    reviews = review_service.read_reviews(movie_name)
    r = next(r for r in reviews if r["Email"] == test_user_2.email)
    r["Penalized"] = "No"
    review_service.write_reviews(movie_name, reviews)

    result = review_service.handle_reported_review(
        email=test_user_2.email,
        movie_name=movie_name,
        remove=True
    )
    assert result["success"] is False
    assert "penalized" in result["message"].lower()

    # Case 2: Set penalized = Yes → removal should succeed
    reviews = review_service.read_reviews(movie_name)
    r = next(r for r in reviews if r["Email"] == test_user_2.email)
    r["Penalized"] = "Yes"
    review_service.write_reviews(movie_name, reviews)

    result = review_service.handle_reported_review(
        email=test_user_2.email,
        movie_name=movie_name,
        remove=True
    )
    assert result["success"] is True
    assert "deleted" in result["message"].lower()

    reviews = review_service.read_reviews(movie_name)
    # Review should be removed
    assert all(r["Email"] != test_user_2.email for r in reviews)

    # Case 3: Keep a reported review when penalized = Yes → should fail
    # Add review again
    review_service.add_review(review, test_user_2)
    reviews = review_service.read_reviews(movie_name)
    r = next(r for r in reviews if r["Email"] == test_user_2.email)
    r.update({"Reported": "Yes", "Report Reason": "Spam", "Penalized": "Yes"})
    review_service.write_reviews(movie_name, reviews)

    result = review_service.handle_reported_review(
        email=test_user_2.email,
        movie_name=movie_name,
        remove=False
    )
    assert result["success"] is False
    assert "penalized" in result["message"].lower()

    # Case 4: Keep a reported review when penalized = No → should reset
    reviews = review_service.read_reviews(movie_name)
    r = next(r for r in reviews if r["Email"] == test_user_2.email)
    r.update({"Reported": "Yes", "Report Reason": "Spam", "Penalized": "No"})
    review_service.write_reviews(movie_name, reviews)

    result = review_service.handle_reported_review(
        email=test_user_2.email,
        movie_name=movie_name,
        remove=False
    )
    assert result["success"] is True
    reviews = review_service.read_reviews(movie_name)
    r = next(r for r in reviews if r["Email"] == test_user_2.email)
    assert r["Reported"] == "No"
    assert r["Report Reason"] == ""
    assert r["Report Count"] == "0"
    assert r["Hidden"] == "No"

    # Case 5: Attempt to handle a review that isn't reported → should fail
    result = review_service.handle_reported_review(
        email=test_user_2.email,
        movie_name=movie_name,
        remove=False
    )
    assert result["success"] is False
    assert "reported" in result["message"].lower()


def test_user_has_reviewed(isolated_movie_env, test_user):
    """Test checking if a user has already reviewed a movie."""
    movie_name = "check_movie"
    file_service.create_movie_folder(movie_name)

    # User hasn't reviewed yet
    assert not review_service.user_has_reviewed(movie_name, test_user.email)

    # Add a review
    review = ReviewRequest(
        movie_name=movie_name,
        rating=8.0,
        comment="Good!",
        review_title="Nice"
    )
    review_service.add_review(review, test_user)

    # Now user has reviewed
    assert review_service.user_has_reviewed(movie_name, test_user.email)


def test_get_review_by_email(isolated_movie_env, test_user):
    """Test getting a specific user's review by email."""
    movie_name = "email_test_movie"
    file_service.create_movie_folder(movie_name)

    # Add a review
    review = ReviewRequest(
        movie_name=movie_name,
        rating=9.0,
        comment="Excellent!",
        review_title="Best Ever"
    )
    review_service.add_review(review, test_user)

    # Get the review by email
    user_review = review_service.get_review_by_email(
        movie_name, test_user.email
    )

    assert user_review is not None
    assert user_review["Email"] == test_user.email
    assert float(user_review["User's Rating out of 10"]) == 9.0
    assert user_review["Review"] == "Excellent!"


def test_like_review_integration(isolated_movie_env, test_user):
    movie_name = "integration_like"
    file_service.create_movie_folder(movie_name)
    # Add review
    review_service.add_review(ReviewRequest(
        movie_name=movie_name,
        rating=9.0,
        comment="Awesome!",
        review_title="Loved it"
    ), test_user)
    
    # Like review - voter can be same as author or different user
    result = review_service.like_review(
        review_author_email=test_user.email,
        movie_name=movie_name,
        voter_email=test_user.email  # or use a different voter email
    )
    
    # Check the result dictionary
    assert result["success"] is True
    assert result["likes"] == 1
    assert result["dislikes"] == 0
    
    # Verify in CSV
    reviews = review_service.read_reviews(movie_name)
    r = next(rev for rev in reviews if rev["Email"] == test_user.email)
    assert r["Likes"] == "1"


def test_dislike_review_integration(isolated_movie_env, test_user):
    movie_name = "integration_dislike"
    file_service.create_movie_folder(movie_name)
    # Add review
    review_service.add_review(ReviewRequest(
        movie_name=movie_name,
        rating=7.0,
        comment="Not bad",
        review_title="Okay"
    ), test_user)
    
    # Dislike review
    result = review_service.dislike_review(
        review_author_email=test_user.email,
        movie_name=movie_name,
        voter_email=test_user.email  # or use a different voter email
    )
    
    # Check the result dictionary
    assert result["success"] is True
    assert result["likes"] == 0
    assert result["dislikes"] == 1
    
    # Verify in CSV
    reviews = review_service.read_reviews(movie_name)
    r = next(rev for rev in reviews if rev["Email"] == test_user.email)
    assert r["Dislikes"] == "1"
