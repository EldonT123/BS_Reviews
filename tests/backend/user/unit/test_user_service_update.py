"""
UNIT TESTS - update_user_profile Method
========================================
Self-contained tests with proper mocking - no actual CSV files or data.
"""

import pytest
import csv
from unittest.mock import Mock, patch, mock_open, MagicMock
from backend.services import user_service


# ==================== Fixtures ====================

@pytest.fixture
def mock_users_data():
    """Mock users dictionary as it would be read from CSV - NOW WITH TOKENS."""
    return {
        "test@example.com": ("testuser", "hashed_password_123", "snail", 0),
        "another@example.com": ("anotheruser", "hashed_password_456", "slug", 100),
        "admin@example.com": ("admin", "hashed_password_789", "banana_slug", 500)
    }


@pytest.fixture
def mock_empty_users():
    """Mock empty users dictionary."""
    return {}


# ==================== Update User Profile Tests ====================

class TestUpdateUserProfile:
    """Test update_user_profile method with proper mocking."""
    
    @patch('backend.services.user_service.read_users')
    @patch('backend.services.user_service.ensure_user_csv_exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('csv.writer')
    def test_update_email_only(self, mock_csv_writer, mock_file, mock_ensure_csv, mock_read_users, mock_users_data):
        """Test updating only the email address."""
        # Arrange
        mock_read_users.return_value = mock_users_data.copy()
        mock_writer_instance = Mock()
        mock_csv_writer.return_value = mock_writer_instance
        
        # Act
        result = user_service.update_user_profile(
            current_email="test@example.com",
            new_email="newemail@example.com"
        )
        
        # Assert
        assert result is True
        mock_read_users.assert_called_once()
        mock_ensure_csv.assert_called_once()
        mock_file.assert_called_once()
        
        # Verify CSV writer was called with header
        calls = mock_writer_instance.writerow.call_args_list
        assert calls[0][0][0] == ["user_email", "username", "user_password", "user_tier", "tokens"]
        
        # Verify the updated user data was written
        written_rows = [call[0][0] for call in calls[1:]]
        assert ["newemail@example.com", "testuser", "hashed_password_123", "snail", 0] in written_rows
    
    @patch('backend.services.user_service.read_users')
    @patch('backend.services.user_service.ensure_user_csv_exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('csv.writer')
    def test_update_username_only(self, mock_csv_writer, mock_file, mock_ensure_csv, mock_read_users, mock_users_data):
        """Test updating only the username."""
        # Arrange
        mock_read_users.return_value = mock_users_data.copy()
        mock_writer_instance = Mock()
        mock_csv_writer.return_value = mock_writer_instance
        
        # Act
        result = user_service.update_user_profile(
            current_email="test@example.com",
            new_email="test@example.com",
            new_username="newusername"
        )
        
        # Assert
        assert result is True
        
        # Verify the username was updated in written data
        written_rows = [call[0][0] for call in mock_writer_instance.writerow.call_args_list[1:]]
        assert ["test@example.com", "newusername", "hashed_password_123", "snail", 0] in written_rows
    
    @patch('backend.services.user_service.read_users')
    @patch('backend.services.user_service.hash_password')
    @patch('backend.services.user_service.ensure_user_csv_exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('csv.writer')
    def test_update_password_only(self, mock_csv_writer, mock_file, mock_ensure_csv, mock_hash, mock_read_users, mock_users_data):
        """Test updating only the password."""
        # Arrange
        mock_read_users.return_value = mock_users_data.copy()
        mock_hash.return_value = "new_hashed_password"
        mock_writer_instance = Mock()
        mock_csv_writer.return_value = mock_writer_instance
        
        # Act
        result = user_service.update_user_profile(
            current_email="test@example.com",
            new_email="test@example.com",
            new_password="NewPassword123!"
        )
        
        # Assert
        assert result is True
        mock_hash.assert_called_once_with("NewPassword123!")
        
        # Verify the password hash was updated
        written_rows = [call[0][0] for call in mock_writer_instance.writerow.call_args_list[1:]]
        assert ["test@example.com", "testuser", "new_hashed_password", "snail",0] in written_rows
    
    @patch('backend.services.user_service.read_users')
    @patch('backend.services.user_service.hash_password')
    @patch('backend.services.user_service.ensure_user_csv_exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('csv.writer')
    def test_update_all_fields(self, mock_csv_writer, mock_file, mock_ensure_csv, mock_hash, mock_read_users, mock_users_data):
        """Test updating email, username, and password all at once."""
        # Arrange
        mock_read_users.return_value = mock_users_data.copy()
        mock_hash.return_value = "new_hashed_password"
        mock_writer_instance = Mock()
        mock_csv_writer.return_value = mock_writer_instance
        
        # Act
        result = user_service.update_user_profile(
            current_email="test@example.com",
            new_email="newemail@example.com",
            new_username="newusername",
            new_password="NewPassword123!"
        )
        
        # Assert
        assert result is True
        mock_hash.assert_called_once_with("NewPassword123!")
        
        # Verify all fields were updated
        written_rows = [call[0][0] for call in mock_writer_instance.writerow.call_args_list[1:]]
        assert ["newemail@example.com", "newusername", "new_hashed_password", "snail",0] in written_rows
    
    @patch('backend.services.user_service.read_users')
    def test_update_nonexistent_user(self, mock_read_users, mock_users_data):
        """Test updating a user that doesn't exist returns False."""
        # Arrange
        mock_read_users.return_value = mock_users_data.copy()
        
        # Act
        result = user_service.update_user_profile(
            current_email="nonexistent@example.com",
            new_email="new@example.com"
        )
        
        # Assert
        assert result is False
    
    @patch('backend.services.user_service.read_users')
    @patch('backend.services.user_service.ensure_user_csv_exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('csv.writer')
    def test_update_preserves_tier(self, mock_csv_writer, mock_file, mock_ensure_csv, mock_read_users, mock_users_data):
        """Test that updating profile preserves the user's tier."""
        # Arrange
        mock_read_users.return_value = mock_users_data.copy()
        mock_writer_instance = Mock()
        mock_csv_writer.return_value = mock_writer_instance
        
        # Act
        result = user_service.update_user_profile(
            current_email="test@example.com",
            new_email="newemail@example.com",
            new_username="newusername"
        )
        
        # Assert
        assert result is True
        
        # Verify tier was preserved
        written_rows = [call[0][0] for call in mock_writer_instance.writerow.call_args_list[1:]]
        assert ["newemail@example.com", "newusername", "hashed_password_123", "snail", 0] in written_rows


if __name__ == "__main__":
    pytest.main([__file__, "-v"])