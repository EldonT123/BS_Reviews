"""Shared pytest fixtures for all test files."""
import shutil
import pytest
import os
import csv
from pathlib import Path
import random
from backend.services import file_service

@pytest.fixture(autouse=True)
def clean_test_data():
    """Clear and recreate movie data folder before each test."""
    data_path = os.path.join("backend", "data", "movies")
    if os.path.exists(data_path):
        shutil.rmtree(data_path)
    os.makedirs(data_path, exist_ok=True)


@pytest.fixture
def temp_database_dir(tmp_path):
    """Temporarily patch DATABASE_PATH to a fresh temp directory."""
    original_path = file_service.DATABASE_PATH
    file_service.DATABASE_PATH = str(tmp_path)
    yield tmp_path
    file_service.DATABASE_PATH = original_path


@pytest.fixture(scope="function")
def temp_real_data_copy(tmp_path, monkeypatch):
    """Copy real database archive to temp dir for integration tests."""
    # Try multiple possible paths for the real data
    possible_paths = [
        Path('./app/database/archive'),
        Path('./database/archive'),
        Path('app/database/archive'),
        Path('database/archive')
    ]
    
    real_data_path = None
    for path in possible_paths:
        if path.exists():
            real_data_path = path
            break
    
    # Skip test if real data doesn't exist
    if not real_data_path:
        pytest.skip("Real data archive not found")
    
    dest_path = tmp_path / 'archive'
    shutil.copytree(real_data_path, dest_path)
    
    # Patch DATABASE_PATH to use the temp copy
    original_path = file_service.DATABASE_PATH
    file_service.DATABASE_PATH = str(dest_path)
    
    # Also set DATABASE_DIR environment variable for movie_routes
    monkeypatch.setenv("DATABASE_DIR", str(dest_path))
    
    # Reload movie_routes to pick up new DATABASE_DIR
    from backend.routes import movie_routes
    import importlib
    importlib.reload(movie_routes)
    
    yield dest_path
    
    # Restore original path
    file_service.DATABASE_PATH = original_path


@pytest.fixture
def isolated_movie_env(tmp_path):
    """Create isolated environment for movie testing with DATABASE_PATH patched."""
    # Patch DATABASE_PATH to tmp_path so all services use it
    original_path = file_service.DATABASE_PATH
    file_service.DATABASE_PATH = str(tmp_path)
    
    yield tmp_path
    
    # Restore original path
    file_service.DATABASE_PATH = original_path


@pytest.fixture
def setup_test_database(temp_database_dir, monkeypatch):
    """Set the DATABASE_DIR environment variable to temp directory for API tests."""
    monkeypatch.setenv("DATABASE_DIR", str(temp_database_dir))
    
    # Reload the module to pick up the new environment variable
    from backend.routes import movie_routes
    import importlib
    importlib.reload(movie_routes)
    
    yield temp_database_dir


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    from fastapi.testclient import TestClient
    from backend.main import app
    return TestClient(app)


@pytest.fixture
def temp_user_csv(tmp_path, monkeypatch):
    """Create temporary user CSV file with proper structure for testing."""
    from backend.services import user_service
    
    # Create a temp CSV file
    user_csv_path = tmp_path / "user_information.csv"
    
    # Create the CSV with headers
    with open(user_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["user_email", "user_password", "user_tier"])
    
    # Patch the USER_CSV_PATH to use our temp file
    original_path = user_service.USER_CSV_PATH
    monkeypatch.setattr('backend.services.user_service.USER_CSV_PATH', str(user_csv_path))
    
    yield user_csv_path
    
    # Restore original path
    user_service.USER_CSV_PATH = original_path

# ==================== Admin Fixtures ====================

@pytest.fixture
def temp_admin_csv(tmp_path, monkeypatch):
    """Create a temporary admin CSV file for isolated testing."""
    from backend.services import admin_service
    
    # Create a temporary CSV file
    temp_csv = tmp_path / "admin_information.csv"
    temp_csv.write_text("admin_email,admin_password\n")
    
    # Patch the ADMIN_CSV_PATH to use our temporary file
    monkeypatch.setattr(admin_service, "ADMIN_CSV_PATH", str(temp_csv))
    
    yield str(temp_csv)


@pytest.fixture
def fresh_movie_folder_with_metadata(temp_real_data_copy, tmp_path):
    """Get a fresh copy of a movie folder with metadata for testing."""
    # Find a movie folder with metadata.json file
    movie_folders = [f for f in temp_real_data_copy.iterdir() if f.is_dir() and (f / "metadata.json").exists()]
    if not movie_folders:
        pytest.skip("No movie folders with metadata.json found in real data copy")
    
    original_folder = movie_folders[0]
    fresh_folder = tmp_path / original_folder.name
    
    # Copy entire movie folder to a fresh temp folder
    shutil.copytree(original_folder, fresh_folder)
    
    yield fresh_folder


@pytest.fixture
def anymovie_temp_folder(tmp_path):
    """Copy a random movie folder from archive to temp directory for testing."""
    # Try multiple possible paths for the real data
    possible_paths = [
        Path('./app/database/archive'),
        Path('./database/archive'),
        Path('app/database/archive'),
        Path('database/archive')
    ]
    
    real_data_path = None
    for path in possible_paths:
        if path.exists() and any(path.iterdir()):
            real_data_path = path
            break
    
    # Check if real data exists; skip test if not
    if not real_data_path:
        pytest.skip("Real data archive not found or empty")

    # Select a random movie folder from the archive
    movie_folders = [f for f in real_data_path.iterdir() if f.is_dir()]
    if not movie_folders:
        pytest.skip("No movie folders found in archive")
    
    selected_folder = random.choice(movie_folders)

    # Destination folder inside tmp_path (named "anymovie")
    dest_folder = tmp_path / "anymovie"

    # Copy the entire movie folder to the temp test folder
    shutil.copytree(selected_folder, dest_folder)

    # Yield path for tests to use
    yield dest_folder

# ==================== Combined Fixtures ====================

@pytest.fixture
def full_test_environment(temp_user_csv, temp_admin_csv, isolated_movie_env):
    """
    Combined fixture providing isolated user, admin, and movie environments.
    Use this for comprehensive integration tests.
    """
    return {
        "user_csv": temp_user_csv,
        "admin_csv": temp_admin_csv,
        "movies_dir": isolated_movie_env
    }