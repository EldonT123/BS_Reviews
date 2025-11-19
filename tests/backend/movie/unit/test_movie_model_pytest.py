import pytest
from backend.models.movie_model import Movie


def test_movie_model_basic_properties(temp_real_data_copy):
    """Ensure Movie initializes correctly using cloned real data."""
    existing_movies = [f.name for f in temp_real_data_copy.iterdir() if f.is_dir()]
    assert existing_movies, "No movies found in cloned DB for testing."
    movie_name = existing_movies[0]

    movie = Movie(movie_name)
    data = movie.to_dict()

    assert movie.name == movie_name
    assert isinstance(movie.metadata, dict)
    assert isinstance(movie.reviews, list)
    assert isinstance(movie.average_rating, (float, int))
    assert "title" in data
    assert "averageRating" in data


def test_movie_model_repr(temp_real_data_copy):
    """Verify Movie string representation."""
    movie = Movie("ExampleMovie")
    result = repr(movie)
    assert result.startswith("<Movie")
    assert "/5>" in result


def test_movie_model_with_missing_files(monkeypatch):
    """Simulate missing metadata/reviews gracefully."""
    monkeypatch.setattr("backend.services.metadata_service.read_metadata", lambda n: {})
    monkeypatch.setattr("backend.services.review_service.read_reviews", lambda n: [])
    monkeypatch.setattr("backend.services.review_service.recalc_average_rating", lambda n: 0)

    movie = Movie("GhostMovie")
    assert movie.metadata == {}
    assert movie.reviews == []
    assert movie.average_rating == 0
