"""Tests for user authentication routes and services.
Mocking not added to test fastapi"""
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

# ==================== UNIT TESTS - CSV Operations ====================

def test_read_users_empty_file(temp_user_csv):
    """Unit test - Edge case:
    Test reading from empty CSV file."""
    users = user_service.read_users()
    assert users == {}


def test_read_users_with_data(temp_user_csv):
    """Unit test - Positive path:
    Test reading users from populated CSV."""
    # Add test users
    user_service.save_user("user1@test.com", "hash1", User.TIER_SNAIL)
    user_service.save_user("user2@test.com", "hash2", User.TIER_SLUG)
    
    users = user_service.read_users()
    assert "user1@test.com" in users
    assert "user2@test.com" in users
    assert users["user1@test.com"][0] == "hash1"  # password_hash
    assert users["user1@test.com"][1] == User.TIER_SNAIL  # tier


def test_read_users_case_insensitive(temp_user_csv):
    """Unit test: Edge Case:
    Test that email keys are stored in lowercase."""
    user_service.save_user("Test@Example.COM", "hashed123", User.TIER_SNAIL)
    users = user_service.read_users()
    
    assert "test@example.com" in users
    assert "Test@Example.COM" not in users


def test_save_user_creates_entry(temp_user_csv):
    """Unit test - Positive path:
    Test that save_user adds user to CSV."""
    user_service.save_user("newuser@test.com", "hashedpass789", User.TIER_SLUG)
    users = user_service.read_users()
    
    assert "newuser@test.com" in users
    assert users["newuser@test.com"][0] == "hashedpass789"
    assert users["newuser@test.com"][1] == User.TIER_SLUG


def test_get_user_by_email(temp_user_csv):
    """Unit test - Positive path:
    Test retrieving a user by email."""
    user_service.create_user("findme@test.com", TEST_PASSWORD, User.TIER_BANANA_SLUG)
    
    user = user_service.get_user_by_email("findme@test.com")
    
    assert user is not None
    assert user.email == "findme@test.com"
    assert user.tier == User.TIER_BANANA_SLUG


def test_get_user_by_email_not_found(temp_user_csv):
    """Unit test - Edge case:
    Test that get_user_by_email returns None for non-existent user."""
    user = user_service.get_user_by_email("doesnotexist@test.com")
    assert user is None