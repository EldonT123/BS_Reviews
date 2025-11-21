"""Tests for file_service module."""
import pytest  # noqa: F401
from pathlib import Path
from backend.services import file_service

TEST_MOVIE = "Test_Movie"


def test_integration_create_and_verify_movie_folder(temp_database_dir):
    """Integration test: create movie folder and verify all components."""
    movie_name = "Integration_Movie"

    # Create folder (temp_database_dir ensures clean state)
    folder_path = Path(file_service.create_movie_folder(movie_name))

    assert folder_path.exists(), "Movie folder was not created"
    assert file_service.check_metadata_exists(movie_name), (
        "Metadata file missing after creation"
    )
    assert file_service.check_reviews_exists(movie_name), (
        "Reviews file missing after creation"
    )

    files = [f.name for f in folder_path.iterdir()]
    assert "metadata.json" in files, "metadata.json not found in folder"
    assert "movieReviews.csv" in files, "movieReviews.csv not found in folder"


def test_integration_create_and_delete_movie_folder(temp_database_dir):
    """Integration test: create a movie folder and then delete it."""
    # Step 1: Create the folder
    folder_path = Path(file_service.create_movie_folder(TEST_MOVIE))

    # Verify folder and files exist
    assert folder_path.exists(), "Movie folder was not created"
    assert file_service.check_metadata_exists(TEST_MOVIE), (
        "Metadata file missing after creation"
    )
    assert file_service.check_reviews_exists(TEST_MOVIE), (
        "Reviews file missing after creation"
    )

    # Step 2: Delete the folder
    result = file_service.delete_movie_folder(TEST_MOVIE)

    # Verify folder no longer exists
    assert not folder_path.exists(), "Movie folder still exists"

    # Verify return message
    assert f"'{TEST_MOVIE}' has been deleted." in result
