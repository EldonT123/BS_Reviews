"""Tests for admin service business logic."""
import pytest
from backend.services import admin_service
from backend.models.admin_model import Admin

TEST_ADMIN_EMAIL = "admin@example.com"
TEST_ADMIN_PASSWORD = "AdminPass123!"


# ==================== UNIT TESTS - Admin Service Business Logic ====================

def test_create_admin(temp_admin_csv):
    """Test admin creation."""
    admin = admin_service.create_admin(TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)
    
    assert admin.email == TEST_ADMIN_EMAIL.lower()
    assert admin.password_hash != TEST_ADMIN_PASSWORD


def test_create_admin_duplicate(temp_admin_csv):
    """Test that creating duplicate admin raises error."""
    admin_service.create_admin(TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)
    
    with pytest.raises(ValueError, match="already exists"):
        admin_service.create_admin(TEST_ADMIN_EMAIL, "DifferentPass123!")


def test_authenticate_admin_success(temp_admin_csv):
    """Test successful admin authentication."""
    admin_service.create_admin(TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)
    
    admin = admin_service.authenticate_admin(TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)
    
    assert admin is not None
    assert admin.email == TEST_ADMIN_EMAIL.lower()


def test_authenticate_admin_wrong_password(temp_admin_csv):
    """Test authentication fails with wrong password."""
    admin_service.create_admin(TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)
    
    with pytest.raises(ValueError, match="Invalid credentials"):
        admin_service.authenticate_admin(TEST_ADMIN_EMAIL, "WrongPassword123!")


def test_authenticate_admin_not_found(temp_admin_csv):
    """Test authentication fails for non-existent admin."""
    with pytest.raises(ValueError, match="Invalid credentials"):
        admin_service.authenticate_admin("nonexistent@test.com", TEST_ADMIN_PASSWORD)


def test_admin_exists(temp_admin_csv):
    """Test checking if admin exists."""
    assert admin_service.admin_exists(TEST_ADMIN_EMAIL) is False
    
    admin_service.create_admin(TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)
    
    assert admin_service.admin_exists(TEST_ADMIN_EMAIL) is True


def test_get_all_admins(temp_admin_csv):
    """Test getting all admins."""
    admin_service.create_admin("admin1@test.com", TEST_ADMIN_PASSWORD)
    admin_service.create_admin("admin2@test.com", TEST_ADMIN_PASSWORD)
    
    admins = admin_service.get_all_admins()
    
    assert len(admins) == 2
    assert all(isinstance(admin, Admin) for admin in admins)


def test_delete_admin(temp_admin_csv):
    """Test deleting an admin."""
    admin_service.create_admin(TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)
    
    success = admin_service.delete_admin(TEST_ADMIN_EMAIL)
    
    assert success is True
    assert admin_service.get_admin_by_email(TEST_ADMIN_EMAIL) is None


def test_delete_nonexistent_admin(temp_admin_csv):
    """Test deleting non-existent admin returns False."""
    success = admin_service.delete_admin("nonexistent@test.com")
    
    assert success is False


def test_get_admin_by_email(temp_admin_csv):
    """Test retrieving admin by email."""
    admin_service.create_admin(TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)
    
    admin = admin_service.get_admin_by_email(TEST_ADMIN_EMAIL)
    
    assert admin is not None
    assert admin.email == TEST_ADMIN_EMAIL.lower()


def test_get_admin_by_email_not_found(temp_admin_csv):
    """Test that get_admin_by_email returns None for non-existent admin."""
    admin = admin_service.get_admin_by_email("doesnotexist@test.com")
    
    assert admin is None
