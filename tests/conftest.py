"""Shared pytest fixtures for all test files."""
import shutil
import pytest
import os
from pathlib import Path
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

