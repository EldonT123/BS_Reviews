import pytest
from backend.models import movie_model
from backend.services import metadata_service, review_service

def test_movie_model_basic_properties(monkeypatch):

    # Patch functions inside movie_model
    monkeypatch.setattr(metadata_service, "read_metadata", lambda name: {
        "title": "Real FS Movie", "average_rating": 4.2, "total_reviews": 2
    })
    monkeypatch.setattr( review_service, "read_reviews", lambda name: [
        {"rating": 5, "review": "Great"}, {"rating": 3, "review": "Okay"}
    ])
    monkeypatch.setattr(review_service, "recalc_average_rating", lambda name: 4.2)

    movie = movie_model.Movie("TestMovie")
    data = movie.to_dict()

    assert movie.name == "TestMovie"
    assert data["title"] == "Real FS Movie"
    assert len(movie.reviews) == 2
    assert data["reviewCount"] == 2
    assert data["averageRating"] == 4.2


def test_movie_model_repr(monkeypatch):
    """Movie __repr__ working correctly."""
    
    # Mock service functions
    monkeypatch.setattr(
        metadata_service, 
        "read_metadata", 
        lambda name: {"title": "Example", "average_rating": 5}
    )
    monkeypatch.setattr(review_service, "read_reviews", lambda name: [])
    monkeypatch.setattr(review_service, "recalc_average_rating", lambda name: 5)

    movie = movie_model.Movie("ExampleMovie")
    result = repr(movie)

    assert result.startswith("<Movie")
    assert "/5>" in result


def test_movie_model_with_missing_files(monkeypatch):
    """Movie handles missing metadata.json and movieReviews.csv."""
    
    # Simulate services returning nothing
    monkeypatch.setattr(metadata_service, "read_metadata", lambda name: {})
    monkeypatch.setattr(review_service, "read_reviews", lambda name: [])
    monkeypatch.setattr(review_service, "recalc_average_rating", lambda name: 0)

    movie = movie_model.Movie("GhostMovie")
    data = movie.to_dict()

    assert movie.metadata == {}
    assert movie.reviews == []
    assert movie.average_rating == 0
    assert data["title"] == "GhostMovie"  # Falls back to movie.name
    assert data["reviewCount"] == 0
    assert data["averageRating"] == 0