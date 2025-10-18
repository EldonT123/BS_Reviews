import os
import pytest
from file_handler import get_movie_folder, check_metadata_exists, check_reviews_exists, create_movie_folder

# Use a temporary test movie folder
TEST_MOVIE = "Test_Movie"

@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    """Fixture to clean up after tests"""
    # Setup: make sure the test folder is removed before tests
    folder_path = get_movie_folder(TEST_MOVIE)
    if os.path.exists(folder_path):
        # Remove files if exist
        for f in os.listdir(folder_path):
            os.remove(os.path.join(folder_path, f))
        os.rmdir(folder_path)
    yield
    # Teardown: remove folder after tests
    if os.path.exists(folder_path):
        for f in os.listdir(folder_path):
            os.remove(os.path.join(folder_path, f))
        os.rmdir(folder_path)

def test_get_movie_folder_path():
    path = get_movie_folder(TEST_MOVIE)
    assert path.endswith(TEST_MOVIE)

def test_create_movie_folder():
    create_movie_folder(TEST_MOVIE)
    folder_path = get_movie_folder(TEST_MOVIE)
    assert os.path.exists(folder_path)

def test_metadata_exists():
    create_movie_folder(TEST_MOVIE)
    assert check_metadata_exists(TEST_MOVIE) is True

def test_reviews_exists():
    create_movie_folder(TEST_MOVIE)
    assert check_reviews_exists(TEST_MOVIE) is True

def test_files_in_folder():
    create_movie_folder(TEST_MOVIE)
    folder_path = get_movie_folder(TEST_MOVIE)
    files = os.listdir(folder_path)
    assert "metadata.json" in files
    assert "movieReviews.csv" in files
