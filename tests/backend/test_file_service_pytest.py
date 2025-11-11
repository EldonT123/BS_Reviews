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


def test_integration_create_and_verify_movie_folder(temp_database_dir):
    """Integration test: create movie folder and verify all components."""
    movie_name = "Integration_Movie"
    
    # Create folder (temp_database_dir ensures clean state)
    folder_path = Path(file_service.create_movie_folder(movie_name))
    
    assert folder_path.exists(), "Movie folder was not created"
    assert file_service.check_metadata_exists(movie_name), "Metadata file missing after creation"
    assert file_service.check_reviews_exists(movie_name), "Reviews file missing after creation"

    files = [f.name for f in folder_path.iterdir()]
    assert "metadata.json" in files, "metadata.json not found in folder"
    assert "movieReviews.csv" in files, "movieReviews.csv not found in folder"


def test_real_data_structure(temp_real_data_copy):
    """Integration test: Verify real data copy structure."""
    # Find movie folders
    movie_folders = [item for item in temp_real_data_copy.iterdir() if item.is_dir()]
    assert len(movie_folders) > 0, "Real data copy should contain movie folders"
    
    # Verify at least one folder has the expected structure
    test_folder = movie_folders[0]
    expected_files = ["metadata.json", "movieReviews.csv"]
    
    actual_files = [f.name for f in test_folder.iterdir()]
    for expected_file in expected_files:
        assert expected_file in actual_files, f"{expected_file} not found in {test_folder.name}"