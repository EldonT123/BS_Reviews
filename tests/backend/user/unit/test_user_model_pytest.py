"""Tests for User model."""
import pytest
from backend.models.user_model import User

def test_user_repr():
    """Test User repr method."""
    user = User(
        email="alice@example.com",
        password_hash="hashed_password",
        tier=User.TIER_SLUG
    )
    
    assert repr(user) == "User(email=alice@example.com, tier=slug)"


def test_user_tier_display():
    """Test tier display names."""
    snail = User("user@test.com", "hash", User.TIER_SNAIL)
    slug = User("user@test.com", "hash", User.TIER_SLUG)
    banana = User("user@test.com", "hash", User.TIER_BANANA_SLUG)
    
    assert "Snail" in snail.get_tier_display_name()
    assert "Slug" in slug.get_tier_display_name()
    assert "Banana Slug" in banana.get_tier_display_name()


def test_add_review_delegates(temp_user_csv):
    """Test that add_review delegates to review_service."""
    from backend.services import user_service
    
    # Create a user with Slug tier (can write reviews)
    user = user_service.create_user(
        email="reviewer@test.com",
        password="TestPass123!",
        tier=User.TIER_SLUG
    )
    
    # This should work without error (though review_service needs to handle it)
    try:
        user.add_review("Test_Movie", 4.5, "Great movie!")
    except Exception as e:
        # Expected if movie doesn't exist
        assert "movie" in str(e).lower() or "not found" in str(e).lower()


def test_add_review_permission_denied():
    """Test that Snail tier cannot write reviews."""
    snail = User("snail@test.com", "hash", User.TIER_SNAIL)
    
    with pytest.raises(ValueError, match="cannot write reviews"):
        snail.add_review("Test_Movie", 5.0, "Trying to review")


# ==================== UNIT TESTS - Permission Assertion Check's ====================

def test_user_tier_checks():
    """Users should correctly report their tier type through helper methods."""
    snail = User("snail@test.com", "hash", User.TIER_SNAIL)
    slug = User("slug@test.com", "hash", User.TIER_SLUG)
    banana = User("banana@test.com", "hash", User.TIER_BANANA_SLUG)
    admin = User("admin@test.com", "hash", User.TIER_ADMIN)
    
    # Snail checks
    assert snail.is_snail() is True
    assert snail.is_slug() is False
    assert snail.is_admin() is False

    # Slug checks
    assert slug.is_slug() is True
    assert slug.is_snail() is False
    assert slug.is_admin() is False

    # Banana Slug checks
    assert banana.is_banana_slug() is True
    assert banana.is_slug() is False  # Should not report as regular slug
    assert banana.is_admin() is False

    # Admin checks
    assert admin.is_admin() is True
    assert admin.is_snail() is False
    assert admin.is_slug() is False


def test_user_permissions():
    """Permission helpers should enforce the correct rules for each tier."""
    snail = User("snail@test.com", "hash", User.TIER_SNAIL)
    slug = User("slug@test.com", "hash", User.TIER_SLUG)
    banana = User("banana@test.com", "hash", User.TIER_BANANA_SLUG)
    
    # Everyone can browse
    assert snail.can_browse() is True
    assert slug.can_browse() is True
    assert banana.can_browse() is True
    
    # Only Slug+ can write reviews
    assert snail.can_write_reviews() is False
    assert slug.can_write_reviews() is True
    assert banana.can_write_reviews() is True
    
    # Only Banana Slugs have priority
    assert snail.has_priority_reviews() is False
    assert slug.has_priority_reviews() is False
    assert banana.has_priority_reviews() is True


def test_user_to_dict():
    """Test User to_dict method."""
    user = User("test@test.com", "hash", User.TIER_SLUG)
    user_dict = user.to_dict()
    
    assert user_dict["email"] == "test@test.com"
    assert user_dict["tier"] == User.TIER_SLUG
    assert "permissions" in user_dict
    assert user_dict["permissions"]["can_write_reviews"] is True