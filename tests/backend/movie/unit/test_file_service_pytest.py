"""Tests for file_service module. (with mocking)"""
import pytest
from unittest.mock import patch, MagicMock
from backend.services import file_service

TEST_MOVIE = "Test_Movie"

# Unit test: Path building logic
@patch("backend.services.file_service.DATABASE_PATH", "/fake/db")


def test_get_movie_folder_path():
    """
    Unit test positive path:
    Tests path building logic is correct
    """
    result = file_service.get_movie_folder(TEST_MOVIE)
    assert result == "/fake/db/Test_Movie"

"""Integration test - creates real files/folders in a temporary directories
Not needed with mocking because mocking does unit level testing


def test_create_movie_folder_creates_files(temp_database_dir):
    # Test that create_movie_folder creates folder and required files.

    folder_path = Path(file_service.create_movie_folder(TEST_MOVIE))
    
    assert folder_path.exists(), "Movie folder was not created"
    assert folder_path.is_dir(), "Movie folder path is not a directory"

    metadata_path = folder_path / "metadata.json"
    reviews_path = folder_path / "movieReviews.csv"
    
    assert metadata_path.is_file(), "metadata.json was not created"
    assert reviews_path.is_file(), "movieReviews.csv was not created"

"""
# Unit test: Existence Checks with Mocked Filesystem Logic
@patch("backend.services.file_service.os.path.exists")
@patch("backend.services.file_service.os.path.join", side_effect=lambda *a: "/mocked/path")


def test_check_metadata_exists_and_reviews_exists(mock_join, mock_exists):
    """
    Unit test positive path
    Simulate metadata.json and movieReviews.csv bock exist
    """
    mock_exists.return_value = True
   
    assert file_service.check_metadata_exists(TEST_MOVIE) is True
    assert file_service.check_reviews_exists(TEST_MOVIE) is True

@patch("backend.services.file_service.os.path.join")
@patch("backend.services.file_service.os.path.exists")


def test_check_metadata_and_reviews_missing(mock_join, mock_exists):
    """
    Unit test negative path/ edge case
    Mocks filesystem missing files.
    """
    # os.path.join → always return a fake consistent path
    mock_join.return_value = "/mocked/path"

    # os.path.exists → always return False
    mock_exists.return_value = False

    assert not file_service.check_metadata_exists(TEST_MOVIE) is False
    assert not file_service.check_reviews_exists(TEST_MOVIE) is False
