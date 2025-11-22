import json
import pytest
from backend.services import metadata_service, file_service

@pytest.fixture
def temp_movie_env(tmp_path, monkeypatch):
    """
    Create an isolated temporary movie folder for tests.
    """
    temp_dir = tmp_path / "movies"
    temp_dir.mkdir(parents=True)

    # Patch get_movie_folder to return this temp path per movie
    def fake_get_movie_folder(movie_name):
        folder = temp_dir / movie_name
        folder.mkdir(parents=True, exist_ok=True)
        return str(folder)
    
    monkeypatch.setattr("backend.services.file_service.get_movie_folder", fake_get_movie_folder)
    return temp_dir


# --- UNIT TESTS (Pure behavior, isolated filesystem) ---

def test_read_metadata_missing_file(monkeypatch, tmp_path):
    """
    Unit test - tests a single function in isolation
    If metadata.json does not exist, return an empty dict.
    """
    dummy_folder = tmp_path / "NoMovie"
    dummy_folder.mkdir()
    monkeypatch.setattr(file_service, "get_movie_folder", lambda name: str(dummy_folder))

    result = metadata_service.read_metadata("NoMovie")
    assert result == {}, "Expected empty dict for missing metadata.json"


def test_write_and_read_metadata(temp_movie_env):
    """
    Unit test - Behavioural and light integration with filesystem
    reads and writes metadata using real JSON I/O
    Touches both write and read
    Ensure write_metadata creates and can read back valid JSON.
    """
    movie_name = "UnitTestMovie"
    # No need to create folder manually; get_movie_folder will create it
    data = {"title": "Test Movie", "director": "Tester", "average_rating": 4.5}

    metadata_service.write_metadata(movie_name, data)

    # Read back using the same service function to verify
    result = metadata_service.read_metadata(movie_name)
    assert result == data, "Written metadata should match read data"


def test_update_average_rating(temp_movie_env):
    """
    Unit test - tests single update function with fake filesystem
    Ensure update_average_rating correctly modifies the field.
    """
    movie_name = "AverageTest"
    initial_data = {"title": "Temp", "average_rating": 2.0}
    metadata_service.write_metadata(movie_name, initial_data)

    metadata_service.update_average_rating(movie_name, 4.3)

    result = metadata_service.read_metadata(movie_name)
    assert result["average_rating"] == 4.3, "Average rating was not updated"


def test_update_review_count(temp_movie_env):
    """Ensure update_review_count modifies review count correctly."""
    movie_name = "CountTest"
    initial_data = {"title": "Temp", "total_reviews": 0}
    metadata_service.write_metadata(movie_name, initial_data)

    metadata_service.update_review_count(movie_name, 10)

    result = metadata_service.read_metadata(movie_name)
    assert result["total_reviews"] == 10, "Review count was not updated"


