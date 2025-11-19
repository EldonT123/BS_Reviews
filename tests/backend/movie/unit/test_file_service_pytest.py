"""Tests for file_service module."""
import pytest
from pathlib import Path
from backend.services import file_service

TEST_MOVIE = "Test_Movie"


def test_get_movie_folder_path(temp_database_dir):
    """Test that get_movie_folder returns correct path."""
    path = file_service.get_movie_folder(TEST_MOVIE)
    assert path.endswith(TEST_MOVIE), f"Movie folder path should end with movie name, got: {path}"
    assert temp_database_dir.exists(), "Database directory should exist"


def test_create_movie_folder_creates_files(temp_database_dir):
    """Test that create_movie_folder creates folder and required files."""
    folder_path = Path(file_service.create_movie_folder(TEST_MOVIE))
    
    assert folder_path.exists(), "Movie folder was not created"
    assert folder_path.is_dir(), "Movie folder path is not a directory"

    metadata_path = folder_path / "metadata.json"
    reviews_path = folder_path / "movieReviews.csv"
    
    assert metadata_path.is_file(), "metadata.json was not created"
    assert reviews_path.is_file(), "movieReviews.csv was not created"


def test_check_metadata_exists_and_reviews_exists(temp_database_dir):
    """Test that check functions correctly identify existing files."""
    file_service.create_movie_folder(TEST_MOVIE)
    
    assert file_service.check_metadata_exists(TEST_MOVIE), "Metadata file should exist"
    assert file_service.check_reviews_exists(TEST_MOVIE), "Reviews file should exist"


def test_check_metadata_and_reviews_missing(temp_database_dir):
    """Test that check functions correctly identify missing files."""
    assert not file_service.check_metadata_exists(TEST_MOVIE), "Metadata file should not exist"
    assert not file_service.check_reviews_exists(TEST_MOVIE), "Reviews file should not exist"

