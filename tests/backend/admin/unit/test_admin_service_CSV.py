"""Tests for admin service CSV operations."""
import pytest
from backend.services import admin_service
from backend.models.admin_model import Admin


TEST_ADMIN_EMAIL = "admin@example.com"
TEST_ADMIN_PASSWORD = "AdminPass123!"


# ==================== UNIT TESTS - CSV Operations ====================

def test_read_admins_empty_file(temp_admin_csv):
    """Test reading from empty CSV file."""
    admins = admin_service.read_admins()
    assert admins == {}


def test_read_admins_with_data(temp_admin_csv):
    """Test reading admins from populated CSV."""
    # Add test admins
    admin_service.save_admin("admin1@test.com", "hash1")
    admin_service.save_admin("admin2@test.com", "hash2")
    
    admins = admin_service.read_admins()
    assert "admin1@test.com" in admins
    assert "admin2@test.com" in admins
    assert admins["admin1@test.com"] == "hash1"
    assert admins["admin2@test.com"] == "hash2"


def test_read_admins_case_insensitive(temp_admin_csv):
    """Test that admin email keys are stored in lowercase."""
    admin_service.save_admin("Admin@Example.COM", "hashed123")
    admins = admin_service.read_admins()
    
    assert "admin@example.com" in admins
    assert "Admin@Example.COM" not in admins


def test_save_admin_creates_entry(temp_admin_csv):
    """Test that save_admin adds admin to CSV."""
    admin_service.save_admin("newadmin@test.com", "hashedpass789")
    admins = admin_service.read_admins()
    
    assert "newadmin@test.com" in admins
    assert admins["newadmin@test.com"] == "hashedpass789"


def test_get_admin_by_email(temp_admin_csv):
    """Test retrieving an admin by email."""
    admin_service.create_admin("findme@test.com", TEST_ADMIN_PASSWORD)
    
    admin = admin_service.get_admin_by_email("findme@test.com")
    
    assert admin is not None
    assert admin.email == "findme@test.com"


def test_get_admin_by_email_not_found(temp_admin_csv):
    """Test that get_admin_by_email returns None for non-existent admin."""
    admin = admin_service.get_admin_by_email("doesnotexist@test.com")
    assert admin is None


def test_ensure_admin_csv_exists(temp_admin_csv):
    """Test that ensure_admin_csv_exists creates file with headers."""
    from backend.services.admin_service import ADMIN_CSV_PATH
    import os
    
    # CSV should exist after fixture setup
    assert os.path.exists(ADMIN_CSV_PATH)
    
    # Read and verify headers
    with open(ADMIN_CSV_PATH, 'r', encoding='utf-8') as f:
        first_line = f.readline().strip()
        assert first_line == "admin_email,admin_password"
