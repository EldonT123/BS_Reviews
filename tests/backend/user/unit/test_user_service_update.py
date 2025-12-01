import pytest
from backend.services import user_service
from backend.models.user_model import User


# ==================== Fixtures ====================

@pytest.fixture(autouse=True)
def reset_user_sessions():
    """Reset user sessions before each test."""
    user_service.user_sessions.clear()
    user_service.session_ids.clear()
    yield
    user_service.user_sessions.clear()
    user_service.session_ids.clear()

class TestUserTierUpdates:
    """Test user tier update functionality."""
    
    def test_update_user_tier(self):
        """Test updating a user's tier."""
        user_service.create_user(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            tier=User.TIER_SNAIL
        )
        
        success = user_service.update_user_tier(
            email="test@example.com",
            new_tier=User.TIER_BANANA_SLUG
        )
        
        assert success is True
        
        user = user_service.get_user_by_email("test@example.com")
        assert user.tier == User.TIER_BANANA_SLUG
    
    def test_update_nonexistent_user_tier(self):
        """Test updating tier of non-existent user fails."""
        success = user_service.update_user_tier(
            email="nonexistent@example.com",
            new_tier=User.TIER_BANANA_SLUG
        )
        
        assert success is False