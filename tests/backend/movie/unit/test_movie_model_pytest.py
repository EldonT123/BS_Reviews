"""Unit tests for Movie model behavior with fully mocked services."""
import pytest
from backend.services import metadata_service, review_service
from backend.models import movie_model

# Unit test: Model initialization and basic fields

def test_movie_model_basic_properties(monkeypatch):
    """
    Unit test Positive path/Initialization Logic:
    Ensures movie loads metadata, reviews and calculated rating
    correctly when all service functions return valid data
    """

    #Mock metadata and review service response
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

# Unit test - __repr__ Functionality

def test_movie_model_repr(monkeypatch):
    """
    Unit Test- positiv path/Representation:
    Ensures Movie __repr__ is working correctly.
    """
    
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

# Unit test - Handling missing metadata and missing reviews

def test_movie_model_with_missing_files(monkeypatch):
    """
    Unit test negative path/Missing file behaviour: 
    Ensures Movie handles missing metadata.json 
    and movieReviews.csv whether they exist or not.
    (Services return empty values)
    """
    
    monkeypatch.setattr(metadata_service, "read_metadata", lambda name: {})
    monkeypatch.setattr(review_service, "read_reviews", lambda name: [])
    monkeypatch.setattr(review_service, "recalc_average_rating", lambda name: 0)

    movie = movie_model.Movie("GhostMovie")
    data = movie.to_dict()

    #Internal fields
    assert movie.metadata == {}
    assert movie.reviews == []
    assert movie.average_rating == 0

    #Fallback logic inside to_dict()
    assert data["title"] == "GhostMovie"  # Falls back to movie.name
    assert data["reviewCount"] == 0
    assert data["averageRating"] == 0