"""Tests for file_service module."""
import pytest
from pathlib import Path
from backend.services import file_service

TEST_MOVIE = "Test_Movie"

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


def test_real_data_structure(anymovie_temp_folder):
    expected_files = ["metadata.json", "movieReviews.csv"]
    actual_files = [f.name for f in anymovie_temp_folder.iterdir()]

    for expected_file in expected_files:
        assert expected_file in actual_files, f"{expected_file} not found in {anymovie_temp_folder.name}"