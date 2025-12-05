"""
Unit tests for admin penalty system.
Tests individual functions with mocked dependencies.
"""
import pytest
from unittest.mock import patch, MagicMock
from backend.services import admin_service, user_service, review_service
from backend.models.user_model import User
from backend.models.admin_model import Admin


# ==================== Fixtures ====================

@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    return User(
        email="test@example.com",
        username="testuser",
        password_hash="hashed_password",
        tier=User.TIER_SLUG,
        tokens=100,
        review_banned=False
    )


@pytest.fixture
def mock_admin():
    """Create a mock admin for testing."""
    return Admin(
        email="admin@example.com",
        password_hash="hashed_admin_password"
    )


# ==================== Token Penalty Tests ====================

class TestTokenPenalties:
    """Test token removal penalties."""

    @patch('backend.services.user_service.read_users')
    @patch('backend.services.user_service.rewrite_user_csv')
    def test_deduct_tokens_success(self, mock_rewrite, mock_read):
        """Test successfully deducting tokens from user."""
        # Arrange
        mock_read.return_value = {
            "test@example.com": ("testuser", "hash", "slug", 100, False)
        }

        # Act
        result = user_service.deduct_tokens_from_user("test@example.com", 50)

        # Assert
        assert result is True
        mock_rewrite.assert_called_once()
        # Verify the new balance is correct
        call_args = mock_rewrite.call_args[0][0]
        assert call_args["test@example.com"][3] == 50  # New token balance

    @patch('backend.services.user_service.read_users')
    def test_deduct_tokens_insufficient_balance(self, mock_read):
        """Test deducting more tokens than user has."""
        # Arrange
        mock_read.return_value = {
            "test@example.com": ("testuser", "hash", "slug", 30, False)
        }

        # Act
        result = user_service.deduct_tokens_from_user("test@example.com", 50)

        # Assert
        assert result is False

    @patch('backend.services.user_service.read_users')
    def test_deduct_tokens_user_not_found(self, mock_read):
        """Test deducting tokens from non-existent user."""
        # Arrange
        mock_read.return_value = {}

        # Act
        result = user_service.deduct_tokens_from_user(
            "nonexistent@example.com", 10)

        # Assert
        assert result is False

    @patch('backend.services.user_service.read_users')
    @patch('backend.services.user_service.rewrite_user_csv')
    def test_update_user_tokens(self, mock_rewrite, mock_read):
        """Test updating user token balance."""
        # Arrange
        mock_read.return_value = {
            "test@example.com": ("testuser", "hash", "slug", 100, False)
        }

        # Act
        result = user_service.update_user_tokens("test@example.com", 75)

        # Assert
        assert result is True
        call_args = mock_rewrite.call_args[0][0]
        assert call_args["test@example.com"][3] == 75


# ==================== Review Ban Tests ====================

class TestReviewBanPenalties:
    """Test review ban penalties."""

    @patch('backend.services.user_service.read_users')
    @patch('backend.services.user_service.rewrite_user_csv')
    def test_ban_user_from_reviews(self, mock_rewrite, mock_read):
        """Test banning a user from writing reviews."""
        # Arrange
        mock_read.return_value = {
            "test@example.com": ("testuser", "hash", "slug", 100, False)
        }

        # Act
        result = user_service.update_review_ban_status(
            "test@example.com", True)

        # Assert
        assert result is True
        call_args = mock_rewrite.call_args[0][0]
        assert call_args["test@example.com"][4] is True  # review_banned

    @patch('backend.services.user_service.read_users')
    @patch('backend.services.user_service.rewrite_user_csv')
    def test_unban_user_from_reviews(self, mock_rewrite, mock_read):
        """Test unbanning a user from writing reviews."""
        # Arrange
        mock_read.return_value = {
            "test@example.com": ("testuser", "hash", "slug", 100, True)
        }

        # Act
        result = user_service.update_review_ban_status(
            "test@example.com", False)

        # Assert
        assert result is True
        call_args = mock_rewrite.call_args[0][0]
        assert call_args["test@example.com"][4] is False  # review_banned

    def test_user_can_write_reviews_when_not_banned(self, mock_user):
        """Test that non-banned users can write reviews."""
        # Arrange
        mock_user.review_banned = False
        mock_user.tier = User.TIER_SLUG

        # Act
        result = mock_user.can_write_reviews()

        # Assert
        assert result is True

    def test_user_cannot_write_reviews_when_banned(self, mock_user):
        """Test that banned users cannot write reviews."""
        # Arrange
        mock_user.review_banned = True
        mock_user.tier = User.TIER_SLUG

        # Act
        result = mock_user.can_write_reviews()

        # Assert
        assert result is False

    @patch('backend.services.review_service.os.listdir')
    @patch('backend.services.review_service.os.path.exists')
    @patch('backend.services.review_service.os.path.isdir')
    @patch('backend.services.review_service.read_reviews')
    @patch('backend.services.review_service.write_reviews')
    def test_mark_all_reviews_penalized(self, mock_write, mock_read,
                                        mock_isdir, mock_exists, mock_listdir):
        """Test marking all user reviews as penalized."""
        # Arrange
        mock_listdir.return_value = ["Inception", "The Matrix", ".gitkeep"]
        mock_isdir.side_effect = lambda x: ".gitkeep" not in x
        mock_exists.return_value = True

        # Mock read_reviews to return different data for each movie
        def read_reviews_side_effect(movie_name):
            return [
                {
                    "Email": "test@example.com",
                    "Review": f"Great {movie_name}!",
                    "Penalized": "No",
                    "Hidden": "No"
                },
                {
                    "Email": "other@example.com",
                    "Review": "Loved it!",
                    "Penalized": "No",
                    "Hidden": "No"
                }
            ]

        mock_read.side_effect = read_reviews_side_effect
        mock_write.return_value = True

        # Act
        result = review_service.mark_all_reviews_penalized("test@example.com")

        # Assert
        assert result["success"] is True
        assert result["reviews_marked"] == 2  # One per movie
        assert len(result["movies_affected"]) == 2
        assert "Inception" in result["movies_affected"]
        assert "The Matrix" in result["movies_affected"]

        # Verify write_reviews was called for each movie
        assert mock_write.call_count == 2


# ==================== Full Ban Tests ====================

class TestFullBanPenalties:
    """Test permanent ban penalties."""

    @patch('backend.services.admin_service.ensure_banned_emails_csv_exists')
    @patch('backend.services.admin_service.read_banned_emails')
    def test_is_email_banned_true(self, mock_read, mock_ensure):
        """Test checking if an email is banned."""
        # Arrange
        mock_read.return_value = {
            "banned@example.com": ("2024-01-01", "admin@example.com", "Spam")
        }

        # Act
        result = admin_service.is_email_banned("banned@example.com")

        # Assert
        assert result is True

    @patch('backend.services.admin_service.read_banned_emails')
    def test_is_email_banned_false(self, mock_read):
        """Test checking if an email is not banned."""
        # Arrange
        mock_read.return_value = {}

        # Act
        result = admin_service.is_email_banned("clean@example.com")

        # Assert
        assert result is False

    @patch('backend.services.admin_service.read_banned_emails')
    def test_get_banned_email_info(self, mock_read):
        """Test retrieving banned email information."""
        # Arrange
        mock_read.return_value = {
            "banned@example.com": ("2024-01-01 10:00:00",
                                   "admin@example.com", "Spam")
        }

        # Act
        result = admin_service.get_banned_email_info("banned@example.com")

        # Assert
        assert result is not None
        assert result["email"] == "banned@example.com"
        assert result["banned_by"] == "admin@example.com"
        assert result["reason"] == "Spam"

    @patch('backend.services.admin_service.read_banned_emails')
    @patch('backend.services.admin_service.ensure_banned_emails_csv_exists')
    @patch('builtins.open', new_callable=MagicMock)
    def test_add_banned_email(self, mock_open, mock_ensure, mock_read):
        """Test adding an email to the ban list."""
        # Arrange
        mock_read.return_value = {}

        # Act
        admin_service.add_banned_email(
            "newban@example.com",
            "admin@example.com",
            "Policy violation"
        )

        # Assert
        mock_open.assert_called_once()
        mock_ensure.assert_called_once()

    @patch('backend.services.admin_service.read_banned_emails')
    @patch('backend.services.admin_service.ensure_banned_emails_csv_exists')
    @patch('builtins.open', new_callable=MagicMock)
    def test_remove_banned_email(self, mock_open, mock_ensure, mock_read):
        """Test removing an email from the ban list."""
        # Arrange
        mock_read.return_value = {
            "banned@example.com": ("2024-01-01", "admin@example.com", "Spam")
        }

        # Act
        result = admin_service.remove_banned_email("banned@example.com")

        # Assert
        assert result is True

    @patch('backend.services.admin_service.read_banned_emails')
    def test_remove_banned_email_not_found(self, mock_read):
        """Test removing an email that isn't banned."""
        # Arrange
        mock_read.return_value = {}

        # Act
        result = admin_service.remove_banned_email("notbanned@example.com")

        # Assert
        assert result is False

    @patch('backend.services.admin_service.is_email_banned')
    @patch('backend.services.admin_service.add_banned_email')
    @patch('backend.services.user_service.get_user_by_email')
    @patch('backend.services.user_service.delete_user')
    @patch('backend.services.user_service.revoke_all_user_sessions')
    @patch('backend.services.review_service.mark_all_reviews_penalized')
    def test_ban_user_complete_process(self, mock_mark_reviews, mock_revoke,
                                       mock_delete, mock_get_user,
                                       mock_add_banned,
                                       mock_is_banned, mock_user):
        """Test the complete ban user process."""
        # Arrange
        mock_is_banned.return_value = False
        mock_get_user.return_value = mock_user
        mock_mark_reviews.return_value = {
            "success": True,
            "reviews_marked": 3,
            "movies_affected": ["Movie1", "Movie2"]
        }
        mock_delete.return_value = True

        # Act
        result = admin_service.ban_user(
            "test@example.com",
            "admin@example.com",
            "Spam and abuse"
        )

        # Assert
        assert result["success"] is True
        assert result["details"]["email_blacklisted"] is True
        assert result["details"]["account_deleted"] is True
        assert result["details"]["sessions_revoked"] is True
        assert result["details"]["reviews_penalized"] == 3
        mock_add_banned.assert_called_once_with(
            "test@example.com",
            "admin@example.com",
            "Spam and abuse"
        )

    @patch('backend.services.admin_service.is_email_banned')
    @patch('backend.services.user_service.get_user_by_email')
    def test_ban_user_already_banned(self, mock_get_user,
                                     mock_is_banned, mock_user):
        """Test banning a user that is already banned."""
        # Arrange
        mock_is_banned.return_value = True
        mock_get_user.return_value = mock_user

        # Act
        result = admin_service.ban_user(
            "test@example.com",
            "admin@example.com",
            "Test"
        )

        # Assert
        assert result["success"] is False
        assert "already banned" in result["message"]

    @patch('backend.services.user_service.get_user_by_email')
    def test_ban_user_not_found(self, mock_get_user):
        """Test banning a non-existent user."""
        # Arrange
        mock_get_user.return_value = None

        # Act
        result = admin_service.ban_user(
            "nonexistent@example.com",
            "admin@example.com",
            "Test"
        )

        # Assert
        assert result["success"] is False
        assert "not found" in result["message"]


# ==================== User Creation with Ban Check Tests ====================

class TestUserCreationWithBanCheck:
    """Test that banned emails cannot create new accounts."""

    @patch('backend.services.admin_service.is_email_banned')
    @patch('backend.services.admin_service.get_banned_email_info')
    def test_create_user_with_banned_email(self, mock_get_info,
                                           mock_is_banned):
        """Test that creating a user with a banned email raises an error."""
        # Arrange
        mock_is_banned.return_value = True
        mock_get_info.return_value = {
            "email": "banned@example.com",
            "reason": "Spam"
        }

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            user_service.create_user(
                "banned@example.com",
                "testuser",
                "password123"
            )

        assert "permanently banned" in str(exc_info.value)

    @patch('backend.services.admin_service.is_email_banned')
    @patch('backend.services.user_service.get_user_by_email')
    @patch('backend.services.user_service.save_user')
    @patch('backend.services.user_service.hash_password')
    def test_create_user_with_clean_email(self, mock_hash, mock_save,
                                          mock_get_user, mock_is_banned):
        """Test that creating a user with a clean email succeeds."""
        # Arrange
        mock_is_banned.return_value = False
        mock_get_user.return_value = None
        mock_hash.return_value = "hashed_password"

        # Act
        user = user_service.create_user(
            "clean@example.com",
            "testuser",
            "password123"
        )

        # Assert
        assert user.email == "clean@example.com"
        assert user.username == "testuser"
        mock_save.assert_called_once()


# ==================== CSV Operations Tests ====================

class TestCSVOperations:
    """Test CSV file operations for ban management."""

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=MagicMock)
    def test_ensure_banned_emails_csv_exists(self, mock_open, mock_exists):
        """Test creation of banned emails CSV file."""
        # Arrange
        mock_exists.return_value = False

        # Act
        admin_service.ensure_banned_emails_csv_exists()

        # Assert
        mock_open.assert_called_once()

    @patch('backend.services.admin_service.read_banned_emails')
    def test_get_all_banned_emails(self, mock_read):
        """Test retrieving all banned emails."""
        # Arrange
        mock_read.return_value = {
            "banned1@example.com": ("2024-01-01",
                                    "admin1@example.com", "Spam"),
            "banned2@example.com": ("2024-01-02",
                                    "admin2@example.com", "Abuse")
        }

        # Act
        result = admin_service.get_all_banned_emails()

        # Assert
        assert len(result) == 2
        assert result[0]["email"] == "banned1@example.com"
        assert result[1]["email"] == "banned2@example.com"


# ==================== User Model Tests ====================

class TestUserModelPenaltyChecks:
    """Test User model methods related to penalties."""

    def test_user_to_dict_includes_review_banned(self, mock_user):
        """Test that user dict includes review_banned field."""
        # Act
        user_dict = mock_user.to_dict()

        # Assert
        assert "review_banned" in user_dict
        assert user_dict["review_banned"] is False

    def test_banned_user_cannot_rate_movies(self, mock_user):
        """Test that banned users cannot rate movies."""
        # Arrange
        mock_user.review_banned = True

        # Act
        result = mock_user.can_rate_movies()

        # Assert
        assert result is False

    def test_banned_user_cannot_edit_reviews(self, mock_user):
        """Test that banned users cannot edit their reviews."""
        # Arrange
        mock_user.review_banned = True

        # Act
        result = mock_user.can_edit_own_reviews()

        # Assert
        assert result is False

    def test_snail_tier_cannot_write_reviews(self, mock_user):
        """Test that Snail tier users cannot write reviews."""
        # Arrange
        mock_user.tier = User.TIER_SNAIL
        mock_user.review_banned = False

        # Act
        result = mock_user.can_write_reviews()

        # Assert
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
