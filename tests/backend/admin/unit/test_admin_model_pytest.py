"""Tests for Admin model."""
import pytest
from backend.models.admin_model import Admin
from backend.services import admin_service, user_service
from backend.models.user_model import User


def test_admin_repr():
    """Test Admin repr method."""
    admin = Admin(
        email="admin@example.com",
        password_hash="hashed_password"
    )
    
    assert repr(admin) == "Admin(email=admin@example.com)"


def test_admin_to_dict():
    """Test Admin to_dict method."""
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
    """Test that all admin permission checks return True."""
    admin = Admin("admin@test.com", "hash")
    
    assert admin.can_manage_users() is True
    assert admin.can_upgrade_tiers() is True
    assert admin.can_delete_users() is True
    assert admin.can_view_all_users() is True
    assert admin.can_manage_movies() is True
    assert admin.can_moderate_reviews() is True


# ==================== UNIT TESTS - Admin Actions ====================

def test_admin_upgrade_user_tier(temp_admin_csv, temp_user_csv):
    """Test admin can upgrade user tier."""
    # Create a user
    user_service.create_user("user@test.com", "UserPass123!", User.TIER_SNAIL)
    
    # Create admin
    admin = Admin("admin@test.com", "hash")
    
    # Upgrade user
    success = admin.upgrade_user_tier("user@test.com", User.TIER_SLUG)
    
    assert success is True
    
    # Verify upgrade
    user = user_service.get_user_by_email("user@test.com")
    assert user.tier == User.TIER_SLUG


def test_admin_upgrade_user_tier_nonexistent_user(temp_admin_csv, temp_user_csv):
    """Test admin upgrade fails for non-existent user."""
    admin = Admin("admin@test.com", "hash")
    
    success = admin.upgrade_user_tier("nonexistent@test.com", User.TIER_SLUG)
    
    assert success is False


def test_admin_delete_user(temp_admin_csv, temp_user_csv):
    """Test admin can delete user."""
    # Create a user
    user_service.create_user("user@test.com", "UserPass123!", User.TIER_SNAIL)
    
    # Create admin
    admin = Admin("admin@test.com", "hash")
    
    # Delete user
    success = admin.delete_user("user@test.com")
    
    assert success is True
    assert user_service.get_user_by_email("user@test.com") is None


def test_admin_delete_user_nonexistent(temp_admin_csv, temp_user_csv):
    """Test admin delete fails for non-existent user."""
    admin = Admin("admin@test.com", "hash")
    
    success = admin.delete_user("nonexistent@test.com")
    
    assert success is False


def test_admin_get_all_users(temp_admin_csv, temp_user_csv):
    """Test admin can get all users."""
    # Create some users
    user_service.create_user("user1@test.com", "Pass123!", User.TIER_SNAIL)
    user_service.create_user("user2@test.com", "Pass123!", User.TIER_SLUG)
    
    # Create admin
    admin = Admin("admin@test.com", "hash")
    
    # Get all users
    users = admin.get_all_users()
    
    assert len(users) == 2
    assert all(isinstance(user, User) for user in users)
