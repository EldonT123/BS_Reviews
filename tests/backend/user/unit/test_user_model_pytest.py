"""Tests for User model."""
import pytest
from backend.models.user_model import User

TEST_EMAIL = "test@email.com"
TEST_USERNAME = "testuser"
TEST_PASSWORD = "pass123!"

def test_user_repr():
    """Test User repr method."""
    user = User(
        email=TEST_EMAIL,
        username=TEST_USERNAME,
        password_hash=TEST_PASSWORD,
        tier=User.TIER_SLUG
    )
    
    assert repr(user) == f"User(email={TEST_EMAIL}, username={TEST_USERNAME}, tier=slug)"


def test_user_tier_display():
    """Test tier display names."""
    snail = User("snail@test.com", TEST_USERNAME, TEST_PASSWORD, User.TIER_SNAIL)
    slug = User("slug@test.com", TEST_USERNAME, TEST_PASSWORD, User.TIER_SLUG)
    banana = User("banana@test.com", TEST_USERNAME, TEST_PASSWORD, User.TIER_BANANA_SLUG)
    
    assert "Snail" in snail.get_tier_display_name()
    assert "Slug" in slug.get_tier_display_name()
    assert "Banana Slug" in banana.get_tier_display_name()


def test_add_review_permission_denied():
    """Test that Snail tier cannot write reviews."""
    snail = User("snail@test.com", "hash", User.TIER_SNAIL)
    
    with pytest.raises(ValueError, match="cannot write reviews"):
        snail.add_review("Test_Movie", 5.0, "Trying to review")


# ==================== UNIT TESTS - Permission Assertion Check's ====================

def test_user_tier_checks():
    """Users should correctly report their tier type through helper methods."""
    snail = User("snail@test.com", TEST_USERNAME, TEST_PASSWORD, User.TIER_SNAIL)
    slug = User("slug@test.com", TEST_USERNAME, TEST_PASSWORD, User.TIER_SLUG)
    banana = User("banana@test.com", TEST_USERNAME, TEST_PASSWORD, User.TIER_BANANA_SLUG)
    
    # Snail checks
    assert snail.is_snail() is True
    assert snail.is_slug() is False
    assert snail.is_banana_slug() is False

    # Slug checks
    assert slug.is_slug() is True
    assert slug.is_snail() is False
    assert slug.is_banana_slug() is False

    # Banana Slug checks
    assert banana.is_banana_slug() is True
    assert banana.is_slug() is False
    assert banana.is_snail() is False


def test_user_permissions():
    """Permission helpers should enforce the correct rules for each tier."""
    snail = User("snail@test.com", TEST_USERNAME, TEST_PASSWORD, User.TIER_SNAIL)
    slug = User("slug@test.com", TEST_USERNAME, TEST_PASSWORD, User.TIER_SLUG)
    banana = User("banana@test.com", TEST_USERNAME, TEST_PASSWORD, User.TIER_BANANA_SLUG)
    
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
    user = User(TEST_EMAIL, TEST_USERNAME, TEST_PASSWORD, User.TIER_SLUG)
    user_dict = user.to_dict()
    
    assert user_dict["email"] == TEST_EMAIL
    assert user_dict["username"] == TEST_USERNAME
    assert user_dict["tier"] == User.TIER_SLUG
    assert "permissions" in user_dict
    assert user_dict["permissions"]["can_write_reviews"] is True
