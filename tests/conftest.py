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
def temp_real_data_copy(tmp_path):
    """Copy real database archive to temp dir for integration tests."""
    real_data_path = Path('./database/archive')
    
    # Skip test if real data doesn't exist
    if not real_data_path.exists():
        pytest.skip("Real data archive not found")
    
    dest_path = tmp_path / 'archive'
    shutil.copytree(real_data_path, dest_path)
    
    # Patch DATABASE_PATH to use the temp copy
    original_path = file_service.DATABASE_PATH
    file_service.DATABASE_PATH = str(dest_path)
    
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
def temp_user_csv(tmp_path, monkeypatch):
    """Create temporary user CSV file with proper structure for testing."""
    from backend.services import user_service  # Changed from user_routes
    
    # Create a temp CSV file
    user_csv_path = tmp_path / "user_information.csv"
    
    # Create the CSV with headers
    with open(user_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["user_email", "user_password", "user_tier"])  # Added user_tier
    
    # Patch the USER_CSV_PATH to use our temp file
    original_path = user_service.USER_CSV_PATH
    monkeypatch.setattr('backend.services.user_service.USER_CSV_PATH', str(user_csv_path))
    
    yield user_csv_path
    
    # Cleanup is automatic with tmp_path
    # Restore original path
    user_service.USER_CSV_PATH = original_path
@pytest.fixture
def fresh_movie_folder_with_metadata(temp_real_data_copy, tmp_path):
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
    # Path to your real data archive (adjust as needed)
    real_data_path = Path('./database/archive')

    # Check if real data exists; skip test if not
    if not real_data_path.exists() or not any(real_data_path.iterdir()):
        pytest.skip("Real data archive not found or empty")

    # Select a random movie folder from the archive
    movie_folders = [f for f in real_data_path.iterdir() if f.is_dir()]
    selected_folder = random.choice(movie_folders)

    # Destination folder inside tmp_path (named "anymovie")
    dest_folder = tmp_path / "anymovie"

    # Copy the entire movie folder to the temp test folder
    shutil.copytree(selected_folder, dest_folder)

    # Yield path for tests to use
    yield dest_folder

    # Cleanup is automatic: tmp_path and contents deleted after test