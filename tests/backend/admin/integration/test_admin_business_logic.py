"""Tests for admin service business logic."""
import pytest
from backend.services import admin_service
from backend.models.admin_model import Admin

TEST_ADMIN_EMAIL = "admin@example.com"
TEST_ADMIN_PASSWORD = "AdminPass123!"


# ==================== INTEGRATION TESTS - Admin Service Business Logic ====================

def test_create_admin(temp_admin_csv):
    """Integration test - Positive path:
    Test admin creation."""
    admin, token = admin_service.create_admin(TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)
    
    assert admin.email == TEST_ADMIN_EMAIL.lower()
    assert admin.password_hash != TEST_ADMIN_PASSWORD
    assert token is not None
    assert len(token) > 0


def test_create_admin_duplicate(temp_admin_csv):
    """Integration Test - Edge Case:
    Test that creating duplicate admin raises error."""
    admin_service.create_admin(TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)
    
    with pytest.raises(ValueError, match="already exists"):
        admin_service.create_admin(TEST_ADMIN_EMAIL, "DifferentPass123!")


def test_authenticate_admin_success(temp_admin_csv):
    """Integration Test - Positive path:
    Test successful admin authentication."""
    admin_service.create_admin(TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)
    
    admin, token = admin_service.authenticate_admin(TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)
    
    assert admin is not None
    assert admin.email == TEST_ADMIN_EMAIL.lower()
    assert token is not None
    assert len(token) > 0


def test_authenticate_admin_wrong_password(temp_admin_csv):
    """Integration test - Edge case:
    Test authentication fails with wrong password."""
    admin_service.create_admin(TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)
    
    with pytest.raises(ValueError, match="Invalid credentials"):
        admin_service.authenticate_admin(TEST_ADMIN_EMAIL, "WrongPassword123!")


def test_authenticate_admin_not_found(temp_admin_csv):
    """Integration test - Edge caseTest authentication fails for non-existent admin."""
    with pytest.raises(ValueError, match="Invalid credentials"):
        admin_service.authenticate_admin("nonexistent@test.com", TEST_ADMIN_PASSWORD)


def test_admin_exists(temp_admin_csv):
    """Integration test - Positive path/ edge case
    Test checking if admin exists."""
    assert admin_service.admin_exists(TEST_ADMIN_EMAIL) is False
    
    admin_service.create_admin(TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)
    
    assert admin_service.admin_exists(TEST_ADMIN_EMAIL) is True


def test_get_all_admins(temp_admin_csv):
    """Integration test - Positive path
    Test getting all admins."""
    admin_service.create_admin("admin1@test.com", TEST_ADMIN_PASSWORD)
    admin_service.create_admin("admin2@test.com", TEST_ADMIN_PASSWORD)
    
    admins = admin_service.get_all_admins()
    
    assert len(admins) == 2
    assert all(isinstance(admin, Admin) for admin in admins)


def test_delete_admin(temp_admin_csv):
    """Integration test -  Positive path:
    Test deleting an admin."""
    admin_service.create_admin(TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)
    
    success = admin_service.delete_admin(TEST_ADMIN_EMAIL)
    
    assert success is True
    assert admin_service.get_admin_by_email(TEST_ADMIN_EMAIL) is None


def test_delete_nonexistent_admin(temp_admin_csv):
    """Integration test - Edge case:
    Test deleting non-existent admin returns False."""
    success = admin_service.delete_admin("nonexistent@test.com")
    
    assert success is False


def test_get_admin_by_email(temp_admin_csv):
    """Integration test - Positive path:
    Test retrieving admin by email."""
    admin_service.create_admin(TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)
    
    admin = admin_service.get_admin_by_email(TEST_ADMIN_EMAIL)
    
    assert admin is not None
    assert admin.email == TEST_ADMIN_EMAIL.lower()


def test_get_admin_by_email_not_found(temp_admin_csv):
    """Integration test - Edge case:
    Test that get_admin_by_email returns None for non-existent admin."""
    admin = admin_service.get_admin_by_email("doesnotexist@test.com")
    
    assert admin is None


def test_token_generation(temp_admin_csv):
    """Integration test - Positive Path:
    Test that tokens are generated correctly."""
    admin1, token1 = admin_service.create_admin("admin1@test.com", TEST_ADMIN_PASSWORD)
    admin2, token2 = admin_service.create_admin("admin2@test.com", TEST_ADMIN_PASSWORD)
    
    # Tokens should be different
    assert token1 != token2
    
    # Tokens should be reasonably long (secure)
    assert len(token1) > 20
    assert len(token2) > 20


def test_token_verification(temp_admin_csv):
    """Integration test - Positive path / Edge case
    Test token verification."""
    admin, token = admin_service.create_admin(TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)
    
    # Verify valid token
    verified_admin = admin_service.verify_admin_token(token)
    assert verified_admin is not None
    assert verified_admin.email == admin.email
    
    # Verify invalid token
    invalid_admin = admin_service.verify_admin_token("invalid_token_12345")
    assert invalid_admin is None


def test_token_revocation(temp_admin_csv):
    """Integration Test - Positive path/ Edge case
    Test token revocation."""
    admin, token = admin_service.create_admin(TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)
    
    # Token should work initially
    assert admin_service.verify_admin_token(token) is not None
    
    # Revoke token
    success = admin_service.revoke_token(token)
    assert success is True
    
    # Token should no longer work
    assert admin_service.verify_admin_token(token) is None
    
    # Revoking again should return False
    assert admin_service.revoke_token(token) is False


def test_delete_admin_revokes_tokens(temp_admin_csv):
    """Integration test - Positive path / Edge case:
    Test that deleting admin revokes all their tokens."""
    admin, token = admin_service.create_admin(TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)
    
    # Get another token for same admin
    _, token2 = admin_service.authenticate_admin(TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)
    
    # Both tokens should work
    assert admin_service.verify_admin_token(token) is not None
    assert admin_service.verify_admin_token(token2) is not None
    
    # Delete admin
    admin_service.delete_admin(TEST_ADMIN_EMAIL)
    
    # Both tokens should be revoked
    assert admin_service.verify_admin_token(token) is None
    assert admin_service.verify_admin_token(token2) is None
