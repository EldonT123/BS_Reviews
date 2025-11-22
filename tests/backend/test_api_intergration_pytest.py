"""API integration tests."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services import file_service, review_service
import json
from pathlib import Path

client = TestClient(app)


def test_get_top_movies_success(temp_database_dir):
    """Test getting top movies with mocked data."""
    # Create two test movies with metadata
    for i, (movie_name, rating) in enumerate([("Movie_A", 8.5), ("Movie_B", 7.2)]):
        movie_folder = temp_database_dir / movie_name
        movie_folder.mkdir()
        
        metadata = {
            "title": movie_name.replace("_", " "),
            "movieIMDbRating": rating
        }
        
        metadata_path = movie_folder / "metadata.json"
        metadata_path.write_text(json.dumps(metadata), encoding='utf-8')

    response = client.get("/api/movies/top")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 5
    assert all("movieIMDbRating" in movie for movie in data)


def test_get_poster_not_found():
    """Test poster endpoint with non-existent movie."""
    response = client.get("/api/movies/poster/nonexistentmovie")
    assert response.status_code == 404
    assert response.json() == {"detail": "Poster not found"}


def test_get_most_commented_movies(temp_database_dir):
    """Test getting most commented movies with real folder structure."""
    # Create test movies with different comment counts
    movies_data = [
        ("MovieA", 15),
        ("MovieB", 10),
        ("MovieC", 20),
    ]
    
    for movie_name, comment_count in movies_data:
        movie_folder = temp_database_dir / movie_name
        movie_folder.mkdir()
        
        # Create metadata with commentCount
        metadata = {
            "title": movie_name,
            "commentCount": comment_count
        }
        
        metadata_path = movie_folder / "metadata.json"
        metadata_path.write_text(json.dumps(metadata), encoding='utf-8')
    
    response = client.get("/api/movies/most_commented")
    assert response.status_code == 200
    movies = response.json()
    
    assert isinstance(movies, list), "Expected response to be a list"
    assert len(movies) > 0, f"Expected at least one movie in response, got {movies}"
    
    # Check if sorted by commentCount descending
    if len(movies) > 1:
        comment_counts = [movie.get("commentCount", 0) for movie in movies]
        assert comment_counts == sorted(comment_counts, reverse=True), \
            "Movies should be sorted by commentCount descending"


def test_get_most_commented_movies_with_real_data(temp_real_data_copy):
    """Integration test: Get most commented movies from real data."""
    response = client.get("/api/movies/most_commented")
    assert response.status_code == 200
    movies = response.json()
    
    assert isinstance(movies, list), "Expected response to be a list"
    # Real data should have movies (unless archive is empty)
    if len(movies) > 0:
        # Verify structure if movies exist
        assert all("title" in movie for movie in movies), "All movies should have titles"