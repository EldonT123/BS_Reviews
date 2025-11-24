"""Tests for Admin model."""
import pytest
from unittest.mock import Mock, patch
from backend.models.admin_model import Admin
from backend.models.user_model import User


def test_admin_repr():
    """Unit test - positive path
    Test Admin repr method."""
    admin = Admin(
        email="admin@example.com",
        password_hash="hashed_password"
    )
    
    assert repr(admin) == "Admin(email=admin@example.com)"


def test_admin_to_dict():
    """Unit test - edge case
    Test Admin to_dict method."""
    admin = Admin("admin@test.com", "hash")
    admin_dict = admin.to_dict()
    
    assert admin_dict["email"] == "admin@test.com"
    assert admin_dict["role"] == "admin"
    assert "permissions" in admin_dict
    assert admin_dict["permissions"]["can_manage_users"] is True
    assert admin_dict["permissions"]["can_upgrade_tiers"] is True
    assert admin_dict["permissions"]["can_delete_users"] is True
    assert admin_dict["permissions"]["can_view_all_users"] is True
    assert admin_dict["permissions"]["can_manage_movies"] is True
    assert admin_dict["permissions"]["can_moderate_reviews"] is True


# ==================== UNIT TESTS - Permission Checks ====================

def test_admin_permissions():
    """Unit test - positive path
    Test that all admin permission checks return True."""
    admin = Admin("admin@test.com", "hash")
    
    assert admin.can_manage_users() is True
    assert admin.can_upgrade_tiers() is True
    assert admin.can_delete_users() is True
    assert admin.can_view_all_users() is True
    assert admin.can_manage_movies() is True
    assert admin.can_moderate_reviews() is True


# ==================== UNIT TESTS - Admin Actions ====================

@patch('backend.services.user_service.update_user_tier')
def test_admin_upgrade_user_tier_success(mock_update_tier):
    """Unit Test - Positive path
    Test admin can upgrade user tier"""
    # Arrange
    mock_update_tier.return_value = True
    admin = Admin("admin@test.com", "hash")
    
    # Act
    success = admin.upgrade_user_tier("user@test.com", User.TIER_SLUG)
    
    # Assert
    assert success is True
    mock_update_tier.assert_called_once_with("user@test.com", User.TIER_SLUG)


@patch('backend.services.user_service.update_user_tier')
def test_admin_upgrade_user_tier_failure(mock_update_tier):
    """Unit test - edge case:
    Test admin upgrade fails for non-existent user"""
    # Arrange
    mock_update_tier.return_value = False
    admin = Admin("admin@test.com", "hash")
    
    # Act
    success = admin.upgrade_user_tier("nonexistent@test.com", User.TIER_SLUG)
    
    # Assert
    assert success is False
    mock_update_tier.assert_called_once_with("nonexistent@test.com", User.TIER_SLUG)


@patch('backend.services.user_service.delete_user')
def test_admin_delete_user_success(mock_delete_user):
    """Unit Test - positive path
    admin can delete user"""
    # Arrange
    mock_delete_user.return_value = True
    admin = Admin("admin@test.com", "hash")
    
    # Act
    success = admin.delete_user("user@test.com")
    
    # Assert
    assert success is True
    mock_delete_user.assert_called_once_with("user@test.com")


@patch('backend.services.user_service.delete_user')
def test_admin_delete_user_failure(mock_delete_user):
    """Unit test - Edge case
    Test admin delete fails for non-existent user"""
    # Arrange
    mock_delete_user.return_value = False
    admin = Admin("admin@test.com", "hash")
    
    # Act
    success = admin.delete_user("nonexistent@test.com")
    
    # Assert
    assert success is False
    mock_delete_user.assert_called_once_with("nonexistent@test.com")


@patch('backend.services.user_service.get_all_users')
def test_admin_get_all_users(mock_get_all_users):
    """Unit test - Positive path
    Test admin can get all users"""
    # Arrange
    mock_user1 = Mock(spec=User)
    mock_user1.email = "user1@test.com"
    mock_user2 = Mock(spec=User)
    mock_user2.email = "user2@test.com"
    mock_get_all_users.return_value = [mock_user1, mock_user2]
    
    admin = Admin("admin@test.com", "hash")
    
    # Act
    users = admin.get_all_users()
    
    # Assert
    assert len(users) == 2
    assert users[0].email == "user1@test.com"
    assert users[1].email == "user2@test.com"
    mock_get_all_users.assert_called_once()


@patch('backend.services.user_service.get_all_users')
def test_admin_get_all_users_empty(mock_get_all_users):
    """Unit test - Edge case
    Test admin get all users when no users exist"""
    # Arrange
    mock_get_all_users.return_value = []
    admin = Admin("admin@test.com", "hash")
    
    # Act
    users = admin.get_all_users()
    
    # Assert
    assert len(users) == 0
    assert users == []
    mock_get_all_users.assert_called_once()

