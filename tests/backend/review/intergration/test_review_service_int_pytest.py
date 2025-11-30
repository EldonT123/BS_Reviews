"""Tests for review_service module."""
import pytest  # noqa: F401
from pathlib import Path  # noqa: F401
from backend.services import review_service, file_service


def test_add_multiple_reviews_and_average(isolated_movie_env):
    """Test adding multiple reviews and calculating average."""
    movie_name = "anymovie"

    # Create the movie folder first
    file_service.create_movie_folder(movie_name)

    # Add multiple reviews
    review_service.add_review("user1", movie_name, 5.0, "Perfect!", "Amazing")
    review_service.add_review("user2", movie_name, 3.0, "It was okay", "Meh")
    review_service.add_review("user3", movie_name, 4.0, "Pretty good", "Nice")

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


def test_add_review_to_real_data(temp_real_data_copy):
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

    # Add a new review with correct parameters
    review_service.add_review(
        username="pytest_user",
        movie_name=existing_movie,
        rating=5.0,
        comment="Excellent movie!",
        review_title="Test Review"
    )

    # Verify review was added
    updated_reviews = review_service.read_reviews(existing_movie)
    new_count = len(updated_reviews)

    assert new_count == initial_count + 1, (
        "Review count should increase by 1. "
        f"Was {initial_count}, now {new_count}"
    )

    # Verify the new review exists (using correct column name)
    assert any(
        r["User"] == "pytest_user" and
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

    # Add review with special characters
    review_service.add_review(
        username="user_français",
        movie_name=movie_name,
        rating=4.5,
        comment="Très bon film! 🎬 Amazing & wonderful.",
        review_title="Incroyable!"
    )

    reviews = review_service.read_reviews(movie_name)
    assert len(reviews) == 1
    assert "français" in reviews[0]["User"]
    assert "Très bon" in reviews[0]["Review"]


def test_report_review_integration(isolated_movie_env):
    """Integration test: Report a review and check the CSV is updated."""
    movie_name = "integration_movie"
    file_service.create_movie_folder(movie_name)

    # Add a review first
    review_service.add_review(
        username="user1",
        movie_name=movie_name,
        rating=8.0,
        comment="Great movie!",
        review_title="Loved it"
    )

    # Report the review
    result = review_service.report_review(
        movie_name=movie_name,
        username="user1",
        reason="Offensive language"
    )
    assert result is True

    # Read back reviews and check fields
    reviews = review_service.read_reviews(movie_name)
    reported_review = next(r for r in reviews if r["User"] == "user1")
    assert reported_review["Reported"] == "Yes"
    assert reported_review["Report Reason"] == "Offensive language"


def test_handle_reported_review_integration(isolated_movie_env):
    """Integration test: Handle a reported review (remove it)."""
    movie_name = "integration_movie_handle"
    file_service.create_movie_folder(movie_name)

    # Add a review first
    review_service.add_review(
        username="user2",
        movie_name=movie_name,
        rating=7.0,
        comment="Pretty good",
        review_title="Meh"
    )

    # Report the review
    review_service.report_review(
        movie_name=movie_name,
        username="user2",
        reason="Spam"
    )

    # Handle the report: remove the review
    result = review_service.handle_reported_review(
        movie_name=movie_name,
        username="user2",
        action="remove"
    )
    assert result is True

    # Check that the review was actually removed
    reviews = review_service.read_reviews(movie_name)
    assert all(r["User"] != "user2" for r in reviews)
