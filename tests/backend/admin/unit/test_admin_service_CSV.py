"""Tests for admin service CSV operations."""
import pytest
from unittest.mock import Mock, patch, mock_open, MagicMock
from backend.services import admin_service
from backend.models.admin_model import Admin
import csv
from io import StringIO


TEST_ADMIN_EMAIL = "admin@example.com"
TEST_ADMIN_PASSWORD = "AdminPass123!"


# ==================== UNIT TESTS - CSV Operations ====================

@patch('os.path.exists')
def test_read_admins_empty_file(mock_exists):
    """Test reading from non-existent CSV file returns empty dict."""
    # Arrange
    mock_exists.return_value = False
    
    # Act
    admins = admin_service.read_admins()
    
    # Assert
    assert admins == {}


@patch('builtins.open', new_callable=mock_open, read_data='admin_email,admin_password\nadmin1@test.com,hash1\nadmin2@test.com,hash2\n')
@patch('os.path.exists', return_value=True)
def test_read_admins_with_data(mock_exists, mock_file):
    """Test reading admins from populated CSV."""
    # Act
    admins = admin_service.read_admins()
    
    # Assert
    assert "admin1@test.com" in admins
    assert "admin2@test.com" in admins
    assert admins["admin1@test.com"] == "hash1"
    assert admins["admin2@test.com"] == "hash2"
    mock_file.assert_called_once()


@patch('builtins.open', new_callable=mock_open, read_data='admin_email,admin_password\nAdmin@Example.COM,hashed123\n')
@patch('os.path.exists', return_value=True)
def test_read_admins_case_insensitive(mock_exists, mock_file):
    """Test that admin email keys are stored in lowercase."""
    # Act
    admins = admin_service.read_admins()
    
    # Assert
    assert "admin@example.com" in admins
    assert "Admin@Example.COM" not in admins
    assert admins["admin@example.com"] == "hashed123"


@patch('builtins.open', new_callable=mock_open)
@patch('backend.services.admin_service.ensure_admin_csv_exists')
def test_save_admin_creates_entry(mock_ensure, mock_file):
    """Test that save_admin writes to CSV."""
    # Act
    admin_service.save_admin("newadmin@test.com", "hashedpass789")
    
    # Assert
    mock_ensure.assert_called_once()
    mock_file.assert_called_once()
    
    # Verify write was called
    handle = mock_file()
    assert handle.write.called


@patch('backend.services.admin_service.read_admins')
def test_get_admin_by_email_found(mock_read_admins):
    """Test retrieving an admin by email."""
    # Arrange
    mock_read_admins.return_value = {"findme@test.com": "hashed_password"}
    
    # Act
    admin = admin_service.get_admin_by_email("findme@test.com")
    
    # Assert
    assert admin is not None
    assert admin.email == "findme@test.com"
    assert admin.password_hash == "hashed_password"
    mock_read_admins.assert_called_once()


@patch('backend.services.admin_service.read_admins')
def test_get_admin_by_email_not_found(mock_read_admins):
    """Test that get_admin_by_email returns None for non-existent admin."""
    # Arrange
    mock_read_admins.return_value = {}
    
    # Act
    admin = admin_service.get_admin_by_email("doesnotexist@test.com")
    
    # Assert
    assert admin is None
    mock_read_admins.assert_called_once()


@patch('os.makedirs')
@patch('os.path.exists', return_value=False)
@patch('builtins.open', new_callable=mock_open)
def test_ensure_admin_csv_exists_creates_file(mock_file, mock_exists, mock_makedirs):
    """Test that ensure_admin_csv_exists creates file with headers."""
    # Act
    admin_service.ensure_admin_csv_exists()
    
    # Assert
    mock_makedirs.assert_called_once()
    mock_file.assert_called()
    
    # Verify headers were written
    handle = mock_file()
    assert handle.write.called


@patch('os.path.exists', return_value=True)
@patch('os.makedirs')
@patch('builtins.open', new_callable=mock_open)
def test_ensure_admin_csv_exists_skips_if_exists(mock_file, mock_makedirs, mock_exists):
    """Test that ensure_admin_csv_exists doesn't recreate existing file."""
    # Act
    admin_service.ensure_admin_csv_exists()
    
    # Assert - makedirs called to ensure directory exists
    mock_makedirs.assert_called_once()
    # File should not be opened for writing since it exists
    mock_file.assert_not_called()
