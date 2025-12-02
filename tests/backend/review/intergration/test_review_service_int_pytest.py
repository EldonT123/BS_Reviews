"""Tests for review_service module."""
import pytest  # noqa: F401
from pathlib import Path  # noqa: F401
from backend.services import review_service, file_service, user_service
from backend.models.review_model import ReviewRequest
from backend.models.user_model import User


@pytest.fixture
def test_user(isolated_movie_env):
    """Create a test user for reviews."""
    email = "test@example.com"
    
    # Clean up if user exists from previous test
    existing_user = user_service.get_user_by_email(email)
    if existing_user:
        user_service.delete_user(email)
    
    # Create a user with Slug tier (can write reviews)
    user = user_service.create_user(
        email=email,
        username="test_user",
        password="password123",
        tier=User.TIER_SLUG
    )
    
    yield user
    
    # Cleanup after test
    try:
        user_service.delete_user(email)
    except:
        pass


@pytest.fixture
def test_user_2(isolated_movie_env):
    """Create a second test user."""
    email = "test2@example.com"
    
    # Clean up if user exists
    existing_user = user_service.get_user_by_email(email)
    if existing_user:
        user_service.delete_user(email)
    
    user = user_service.create_user(
        email=email,
        username="test_user_2",
        password="password123",
        tier=User.TIER_SLUG
    )
    
    yield user
    
    # Cleanup after test
    try:
        user_service.delete_user(email)
    except:
        pass


@pytest.fixture
def test_user_3(isolated_movie_env):
    """Create a third test user."""
    email = "test3@example.com"
    
    # Clean up if user exists
    existing_user = user_service.get_user_by_email(email)
    if existing_user:
        user_service.delete_user(email)
    
    user = user_service.create_user(
        email=email,
        username="test_user_3",
        password="password123",
        tier=User.TIER_SLUG
    )
    
    yield user
    
    # Cleanup after test
    try:
        user_service.delete_user(email)
    except:
        pass


def test_add_multiple_reviews_and_average(isolated_movie_env, test_user, test_user_2, test_user_3):
    """Test adding multiple reviews and calculating average."""
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
    """Integration test: Read reviews from real data copy."""
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
    """Integration test: Add review to existing movie from real data copy."""
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
    """Test adding reviews with special characters and unicode."""
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
    except:
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

    # Report the review using email
    result = review_service.report_review(
        email=test_user.email,
        movie_name=movie_name,
        reason="Offensive language"
    )
    assert result is True

    # Read back reviews and check fields
    reviews = review_service.read_reviews(movie_name)
    reported_review = next(r for r in reviews if r["Email"] == test_user.email)
    assert reported_review["Reported"] == "Yes"
    assert reported_review["Report Reason"] == "Offensive language"


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

    # Handle the report: remove the review
    result = review_service.handle_reported_review(
        email=test_user_2.email,
        movie_name=movie_name,
        action="remove"
    )
    assert result is True

    # Check that the review was actually removed
    reviews = review_service.read_reviews(movie_name)
    assert all(r["Email"] != test_user_2.email for r in reviews)


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
    user_review = review_service.get_review_by_email(movie_name, test_user.email)
    
    assert user_review is not None
    assert user_review["Email"] == test_user.email
    assert float(user_review["User's Rating out of 10"]) == 9.0
    assert user_review["Review"] == "Excellent!"