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

# ==================== UNIT TESTS - Password Functions ====================

def test_password_hash_returns_string():
    """Test that hash_password returns a hashed string."""
    hashed = user_service.hash_password(TEST_PASSWORD)
    
    assert isinstance(hashed, str)
    assert len(hashed) > 0
    assert hashed != TEST_PASSWORD


def test_password_hash_different_for_same_password():
    """Test that same password generates different hashes due to salt."""
    hash1 = user_service.hash_password(TEST_PASSWORD)
    hash2 = user_service.hash_password(TEST_PASSWORD)
    
    assert hash1 != hash2


def test_verify_password_correct():
    """Test that verify_password returns True for correct password."""
    hashed = user_service.hash_password(TEST_PASSWORD)
    
    assert user_service.verify_password(TEST_PASSWORD, hashed) is True


def test_verify_password_incorrect():
    """Test that verify_password returns False for wrong password."""
    hashed = user_service.hash_password(TEST_PASSWORD)
    wrong_password = "WrongPassword456!"
    
    assert user_service.verify_password(wrong_password, hashed) is False


def test_password_truncation_long_password():
    """Test that passwords longer than 72 bytes are handled correctly."""
    long_password = "a" * 100
    hashed = user_service.hash_password(long_password)
    
    assert user_service.verify_password(long_password, hashed) is True
