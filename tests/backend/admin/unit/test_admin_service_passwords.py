"""Tests for admin service password operations."""
import pytest
from backend.services import admin_service


TEST_ADMIN_PASSWORD = "AdminPass123!"


# ==================== UNIT TESTS - Password Functions ====================

def test_admin_password_hash_returns_string():
    """Unit tests - Positive path:
    Test that hash_password returns a hashed string."""
    hashed = admin_service.hash_password(TEST_ADMIN_PASSWORD)
    
    assert isinstance(hashed, str)
    assert len(hashed) > 0
    assert hashed != TEST_ADMIN_PASSWORD


def test_admin_password_hash_different_for_same_password():
    """Unit test - Positive path/ Security edge case:
    Test that same password generates different hashes due to salt."""
    hash1 = admin_service.hash_password(TEST_ADMIN_PASSWORD)
    hash2 = admin_service.hash_password(TEST_ADMIN_PASSWORD)
    
    assert hash1 != hash2


def test_admin_verify_password_correct():
    """Unit test - Positive path
    Test that verify_password returns True for correct password."""
    hashed = admin_service.hash_password(TEST_ADMIN_PASSWORD)
    
    assert admin_service.verify_password(TEST_ADMIN_PASSWORD, hashed) is True


def test_admin_verify_password_incorrect():
    """Unit tets - Edge case:
    Test that verify_password returns False for wrong password."""
    hashed = admin_service.hash_password(TEST_ADMIN_PASSWORD)
    wrong_password = "WrongPassword456!"
    
    assert admin_service.verify_password(wrong_password, hashed) is False


def test_admin_password_truncation_long_password():
    """Unit test - Edge case
    Test that passwords longer than 72 bytes are handled correctly."""
    long_password = "a" * 100
    hashed = admin_service.hash_password(long_password)
    
    assert admin_service.verify_password(long_password, hashed) is True


def test_admin_password_hash_bcrypt_format():
    """Unit test - Positive path/ format check:
    Test that password hash uses bcrypt format."""
    hashed = admin_service.hash_password(TEST_ADMIN_PASSWORD)
    
    # Bcrypt hashes start with $2b$ (or $2a$ or $2y$)
    assert hashed.startswith('$2b$') or hashed.startswith('$2a$') or hashed.startswith('$2y$')
    # Bcrypt hashes are 60 characters long
    assert len(hashed) == 60
