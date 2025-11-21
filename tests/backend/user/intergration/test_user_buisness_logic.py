"""Tests for user authentication routes and services."""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import csv
from backend.main import app
from backend.services import user_service
from backend.models.user_model import User
from backend.services.user_service import USER_CSV_PATH

client = TestClient(app)

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "ValidPass123!"

# ==================== INTEGRATION TESTS - User Service Business Logic ====================

def test_create_user(temp_user_csv):
    """Test user creation."""
    user = user_service.create_user(TEST_EMAIL, TEST_PASSWORD, User.TIER_SLUG)
    
    assert user.email == TEST_EMAIL.lower()
    assert user.tier == User.TIER_SLUG
    assert user.password_hash != TEST_PASSWORD


def test_create_user_duplicate(temp_user_csv):
    """Test that creating duplicate user raises error."""
    user_service.create_user(TEST_EMAIL, TEST_PASSWORD)
    
    with pytest.raises(ValueError, match="already exists"):
        user_service.create_user(TEST_EMAIL, "DifferentPass123!")


def test_authenticate_user_success(temp_user_csv):
    """Test successful authentication."""
    user_service.create_user(TEST_EMAIL, TEST_PASSWORD)
    user, token = user_service.authenticate_user(TEST_EMAIL, TEST_PASSWORD)  # Unpack tuple
    assert user is not None
    assert user.email == TEST_EMAIL.lower()
    assert token is not None  # Also verify token was created
    assert len(token) > 0


def test_authenticate_user_wrong_password(temp_user_csv):
    """Test authentication fails with wrong password."""
    user_service.create_user(TEST_EMAIL, TEST_PASSWORD)
    
    with pytest.raises(ValueError, match="Invalid credentials"):
        user_service.authenticate_user(TEST_EMAIL, "WrongPassword123!")


def test_authenticate_user_not_found(temp_user_csv):
    """Test authentication fails for non-existent user."""
    with pytest.raises(ValueError, match="Invalid credentials"):
        user_service.authenticate_user("nonexistent@test.com", TEST_PASSWORD)


def test_update_user_tier(temp_user_csv):
    """Test updating user tier."""
    user_service.create_user(TEST_EMAIL, TEST_PASSWORD, User.TIER_SNAIL)
    
    success = user_service.update_user_tier(TEST_EMAIL, User.TIER_BANANA_SLUG)
    
    assert success is True
    
    user = user_service.get_user_by_email(TEST_EMAIL)
    assert user.tier == User.TIER_BANANA_SLUG


def test_delete_user(temp_user_csv):
    """Test deleting a user."""
    user_service.create_user(TEST_EMAIL, TEST_PASSWORD)
    
    success = user_service.delete_user(TEST_EMAIL)
    
    assert success is True
    assert user_service.get_user_by_email(TEST_EMAIL) is None