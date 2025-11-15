import os
import pytest
from backend.models.user_model import User


def test_user_repr():
    user = User(username="bob", is_admin=True)
    assert "bob" in repr(user)
    assert "admin=True" in repr(user)


def test_add_review_delegates(monkeypatch):
    """Ensure add_review calls review_service.add_review."""
    called = {}

    def fake_add_review(username, movie, rating, comment):
        called.update({
            "username": username,
            "movie": movie,
            "rating": rating,
            "comment": comment
        })

    monkeypatch.setattr("backend.services.review_service.add_review", fake_add_review)

    user = User("charlie")
    user.add_review("Matrix", 5, "Awesome")

    assert called == {
        "username": "charlie",
        "movie": "Matrix",
        "rating": 5,
        "comment": "Awesome"
    }


def test_add_review_real_integration(temp_real_data_copy):
    """Actually append a review in the cloned DB."""
    user = User("dana")
    existing_movies = [f.name for f in temp_real_data_copy.iterdir() if f.is_dir()]
    assert existing_movies, "No movies found in cloned DB"
    target_movie = existing_movies[0]

    user.add_review(target_movie, 8, "Good movie!")

    reviews_path = temp_real_data_copy / target_movie / "movieReviews.csv"
    assert reviews_path.exists()

    with open(reviews_path, encoding="utf-8") as f:
        content = f.read()
        assert "Good movie!" in content
        assert "dana" in content
