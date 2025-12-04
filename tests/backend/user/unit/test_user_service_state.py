"""Updated unit tests for session management with session IDs."""
import pytest
from unittest.mock import patch
from datetime import datetime, timedelta
from backend.services import user_service
from backend.models.user_model import User


@pytest.fixture(autouse=True)
def clear_sessions():
    """Fixture: Clear session storage before each test."""
    user_service.user_sessions.clear()
    user_service.session_ids.clear()
    yield
    user_service.user_sessions.clear()
    user_service.session_ids.clear()


@pytest.fixture
def mock_user_data():
    """Mock users dictionary with tokens."""
    return {
        "test@example.com": (
            "testuser", "hashed_password_123", "snail", 0, "False"),
        "session@example.com": (
            "sessionuser", "hashed_password_456", "slug", 100, "False")
    }


class TestSessionManagement:
    """Tests for session token and session ID management."""

    def test_create_session(self):
        """Positive path:
        Test creating a session token."""
        email = "test@example.com"
        token = user_service.create_session(email)

        assert token is not None
        assert len(token) > 0
        assert token in user_service.user_sessions

    def test_create_session_id(self):
        """Positive path:
        Test creating a random session ID."""
        email = "test@example.com"
        session_id = user_service.create_session_id(email)

        assert session_id is not None
        assert len(session_id) > 0
        assert session_id in user_service.session_ids

    def test_session_id_is_random(self):
        """Edge case:
        Test that session IDs are randomly generated."""
        email = "test@example.com"
        session_id1 = user_service.create_session_id(email)
        session_id2 = user_service.create_session_id(email)

        # Different sessions should have different IDs
        assert session_id1 != session_id2

    def test_session_id_uniqueness(self):
        """Edge case:
        Test that duplicate session IDs are handled."""
        # This tests the while loop in create_session_id
        # that ensures uniqueness
        email = "test@example.com"
        session_ids = set()

        for _ in range(10):
            sid = user_service.create_session_id(email)
            assert sid not in session_ids
            session_ids.add(sid)

# ==================== TESTS - SESSION VERIFICATION ====================

    def test_verify_valid_session(self, mock_user_data):
        """Positive path:
        Test verifying a valid session token."""
        email = "test@example.com"
        token = user_service.create_session(email)

        with patch.object(
            user_service,
            'read_users',
            return_value=mock_user_data
        ):
            user = user_service.verify_session(token)

            assert user is not None
            assert user.email == email

    def test_verify_valid_session_id(self, mock_user_data):
        """Positive path:
        Test verifying a valid session ID."""
        email = "test@example.com"
        session_id = user_service.create_session_id(email)

        with patch.object(
            user_service,
            'read_users',
            return_value=mock_user_data
        ):
            user = user_service.verify_session_id(session_id)

            assert user is not None
            assert user.email == email

    def test_verify_invalid_session(self):
        """Edge Case:
        Test verifying an invalid session token."""
        user = user_service.verify_session("invalid-token")
        assert user is None

    def test_verify_invalid_session_id(self):
        """Edge Case:
        Test verifying an invalid session ID."""
        user = user_service.verify_session_id("invalid-id")
        assert user is None

    def test_verify_expired_session(self, mock_user_data):
        """Edge case:
        Test that expired sessions are rejected."""
        email = "test@example.com"
        token = user_service.create_session(email)

        # Manually expire the session
        expired_time = datetime.now() - timedelta(hours=25)
        user_service.user_sessions[token] = (email, expired_time)

        user = user_service.verify_session(token)

        assert user is None
        assert token not in user_service.user_sessions

    def test_verify_expired_session_via_id(self, mock_user_data):
        """Edge case:
        Test that expired sessions via ID are rejected."""
        email = "test@example.com"
        session_id = user_service.create_session_id(email)
        token = user_service.session_ids[session_id]

        # Manually expire the session
        expired_time = datetime.now() - timedelta(hours=25)
        user_service.user_sessions[token] = (email, expired_time)

        user = user_service.verify_session_id(session_id)

        assert user is None
        assert token not in user_service.user_sessions

# ==================== TESTS - SESSION REVOCATION ====================

    def test_revoke_session(self):
        """Positive path:
        Revoking a session token."""
        email = "test@example.com"
        token = user_service.create_session(email)

        success = user_service.revoke_session(token)

        assert success is True
        assert token not in user_service.user_sessions

    def test_revoke_session_id(self):
        """Positive path:
        Test revoking a session ID."""
        email = "test@example.com"
        session_id = user_service.create_session_id(email)
        token = user_service.session_ids[session_id]

        success = user_service.revoke_session_id(session_id)

        assert success is True
        assert session_id not in user_service.session_ids
        assert token not in user_service.user_sessions

    def test_revoke_nonexistent_session(self):
        """Edge case:
        Test revoking a non-existent session."""
        success = user_service.revoke_session("nonexistent-token")
        assert success is False

    def test_revoke_nonexistent_session_id(self):
        """Edge case:
        Test revoking a non-existent session ID."""
        success = user_service.revoke_session_id("nonexistent-id")
        assert success is False

    def test_revoke_all_user_sessions(self):
        """Positive path:
        Test revoking all sessions for a user."""
        email = "test@example.com"
        session_id1 = user_service.create_session_id(email)
        session_id2 = user_service.create_session_id(email)
        session_id3 = user_service.create_session_id("other@example.com")

        token1 = user_service.session_ids[session_id1]
        token2 = user_service.session_ids[session_id2]
        token3 = user_service.session_ids[session_id3]

        user_service.revoke_all_user_sessions(email)

        # User's sessions should be revoked
        assert token1 not in user_service.user_sessions
        assert token2 not in user_service.user_sessions
        assert session_id1 not in user_service.session_ids
        assert session_id2 not in user_service.session_ids

        # Other user's session should remain
        assert token3 in user_service.user_sessions
        assert session_id3 in user_service.session_ids

    def test_cleanup_expired_sessions(self):
        """Edge case:
        Test cleanup of expired sessions and IDs."""
        email1 = "test1@example.com"
        email2 = "test2@example.com"

        session_id1 = user_service.create_session_id(email1)
        session_id2 = user_service.create_session_id(email2)

        token1 = user_service.session_ids[session_id1]
        token2 = user_service.session_ids[session_id2]

        # Manually expire session 1
        expired_time = datetime.now() - timedelta(hours=25)
        user_service.user_sessions[token1] = (email1, expired_time)

        user_service.cleanup_expired_sessions()

        # Expired session and its ID should be removed
        assert token1 not in user_service.user_sessions
        assert session_id1 not in user_service.session_ids

        # Valid session should remain
        assert token2 in user_service.user_sessions
        assert session_id2 in user_service.session_ids

# ==================== TESTS - AUTHENTICATE USER ====================


class TestAuthenticateUser:
    """Tests for authenticate_user with session ID."""

    def test_authenticate_returns_session_id(self):
        """Positive path:
        Test that authenticate returns a session ID."""
        password = "password123"
        hashed = user_service.hash_password(password)
        mock_user = User("test@example.com", "testuser", hashed, User.TIER_SNAIL)

        with patch.object(
            user_service,
            'get_user_by_email',
            return_value=mock_user
        ):
            user, session_id = user_service.authenticate_user(
                "test@example.com",
                password
            )

            assert user.email == "test@example.com"
            assert session_id is not None
            assert len(session_id) > 0
            assert session_id in user_service.session_ids

    def test_authenticate_creates_random_session_ids(self):
        """Edge case:
        Test that each login creates a unique session ID."""
        password = "password123"
        hashed = user_service.hash_password(password)
        mock_user = User("test@example.com", "testuser", hashed, User.TIER_SNAIL)

        with patch.object(
            user_service,
            'get_user_by_email',
            return_value=mock_user
        ):
            _, session_id1 = user_service.authenticate_user(
                "test@example.com",
                password
            )
            _, session_id2 = user_service.authenticate_user(
                "test@example.com",
                password
            )

            # Each login should get a different session ID
            assert session_id1 != session_id2

# ==================== TESTS - SIGNOUT ====================


class TestSignoutUser:
    """Tests for signout_user with session ID."""

    def test_signout_with_session_id(self):
        """Positive path:
        Test signing out using session ID."""
        email = "test@example.com"
        session_id = user_service.create_session_id(email)

        success = user_service.signout_user(session_id)

        assert success is True
        assert session_id not in user_service.session_ids

    def test_signout_with_invalid_session_id(self):
        """Edge case:
        Test signing out with invalid session ID."""
        success = user_service.signout_user("invalid-id")
        assert success is False
