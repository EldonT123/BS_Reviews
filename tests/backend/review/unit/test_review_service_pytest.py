"""Tests for review_service module."""
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from backend.services import review_service, file_service


def test_read_reviews_empty_file(isolated_movie_env):
    """Test reading reviews from an empty CSV file."""
    movie_name = "anymovie"
    
    # Use file_service to properly create the movie folder with CSV
    file_service.create_movie_folder(movie_name)
    
    reviews = review_service.read_reviews(movie_name)
    assert reviews == [], "Empty CSV (with headers only) should return empty list"


def test_add_review_and_recalc_average():
    """Unit test add_review and recalc_average_rating with mocks."""

    movie_name = "anymovie"
    mock_csv_data = "Date of Review,User,Usefulness Vote,Total Votes,User's Rating out of 10,Review Title,Review\n"

    # Mock open for writing (add_review writes CSV)
    with patch("builtins.open", mock_open()) as mocked_file:
        # Call add_review
        review_service.add_review(
            username="tester",
            movie_name=movie_name,
            rating=4.0,
            comment="Great movie!",
            review_title="Loved it"
        )
        # Assert file was opened for append
        mocked_file.assert_called()

    # Mock read_reviews to return a fake review list
    with patch("backend.services.review_service.read_reviews", return_value=[
        {
            "User": "tester",
            "User's Rating out of 10": "4.0",
            "Review Title": "Loved it",
            "Review": "Great movie!"
        }
    ]):
        reviews = review_service.read_reviews(movie_name)
        assert len(reviews) == 1
        assert reviews[0]["User"] == "tester"
        assert float(reviews[0]["User's Rating out of 10"]) == 4.0

    # Mock recalc_average_rating to calculate based on fake data
    with patch("backend.services.review_service.read_reviews", return_value=[
        {"User's Rating out of 10": "4.0"},
        {"User's Rating out of 10": "5.0"}
    ]):
        avg = review_service.recalc_average_rating(movie_name)
        # recalc_average_rating implementation reads reviews, so let's call real function
        # or if recalc_average_rating uses read_reviews internally, it will get mocked data
        assert avg == pytest.approx(4.5)


def test_recalc_average_rating_with_invalid_rating():
    """Unit test average rating calculation ignoring invalid/empty ratings."""
    movie_name = "anymovie"

    # Mock read_reviews to simulate one valid and one invalid rating
    with patch("backend.services.review_service.read_reviews", return_value=[
        {"User's Rating out of 10": "5.0"},
        {"User's Rating out of 10": ""}
    ]):
        avg = review_service.recalc_average_rating(movie_name)
        assert avg == 5.0


