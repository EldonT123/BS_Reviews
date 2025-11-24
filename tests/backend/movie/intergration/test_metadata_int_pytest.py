import json
import pytest
from backend.services import metadata_service, file_service

@pytest.fixture
def temp_movie_env(tmp_path, monkeypatch):
    """Fixture - Create an isolated temporary movie folder for tests."""
    temp_dir = tmp_path / "movies"
    temp_dir.mkdir(parents=True)

    # Patch get_movie_folder to return this temp path per movie
    def fake_get_movie_folder(movie_name):
        folder = temp_dir / movie_name
        folder.mkdir(parents=True, exist_ok=True)
        return str(folder)
    
    monkeypatch.setattr("backend.services.file_service.get_movie_folder", fake_get_movie_folder)
    return temp_dir

# Integration Tests (metadata operations)

def test_read_and_update_real_metadata(fresh_movie_folder_with_metadata):
    """
    Integration test positive path / real metadata: 
    Read and update real metadata.json contents
    """
    target_movie_folder = fresh_movie_folder_with_metadata
    target_movie = target_movie_folder.name
    path = target_movie_folder / "metadata.json"
    
    with open(path, "r", encoding="utf-8") as f:
        original = json.load(f)

    try:
        # Patch file_service.get_movie_folder to point to this fresh folder for this test
        from backend.services import file_service, metadata_service
        import builtins

        original_get_movie_folder = file_service.get_movie_folder
        file_service.get_movie_folder = lambda name: str(target_movie_folder)

        # Perform update
        metadata_service.update_average_rating(target_movie, 3.9)
        metadata_service.update_review_count(target_movie, 42)

        updated = metadata_service.read_metadata(target_movie)
        assert updated["average_rating"] == 3.9
        assert updated["total_reviews"] == 42
    finally:
        # Restore original content so later tests aren't affected
        with open(path, "w", encoding="utf-8") as f:
            json.dump(original, f, indent=2)
        
        # Restore original get_movie_folder method
        file_service.get_movie_folder = original_get_movie_folder
