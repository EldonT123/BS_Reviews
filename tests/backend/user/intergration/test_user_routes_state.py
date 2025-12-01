"""Updated integration tests for user routes with session IDs."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.models.user_model import User
from backend.services import user_service


@pytest.fixture
def client():
    """Create a test client."""
    from backend.main import app
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_sessions():
    """Clear session storage before each test."""
    user_service.user_sessions.clear()
    user_service.session_ids.clear()
    yield
    user_service.user_sessions.clear()
    user_service.session_ids.clear()


@pytest.fixture
def mock_user():
    """Fixture with a mock user."""
    return User("test@example.com", "testuser", "hashed_password", User.TIER_SNAIL)


@pytest.fixture
def mock_slug_user():
    """Fixture with a mock Slug tier user."""
    return User("slug@example.com", "sluguser", "hashed_password", User.TIER_SLUG)

# ==================== Login Tests ====================

class TestLogin:
    """Tests for /api/login endpoint with session ID."""

    def test_login_returns_session_id(self, client, mock_user):
        """Test that login returns a session ID and revokes old sessions."""
        with patch(
            'backend.services.user_service.authenticate_user'
        ) as mock_auth:
            mock_auth.return_value = (mock_user, "abc123XY")

            response = client.post(
                "/api/users/login",
                json={
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": "password123"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "Welcome back" in data["message"]
            assert data["user"]["email"] == "test@example.com"
            assert "session_id" in data
            assert data["session_id"] == "abc123XY"
            assert "token" not in data  # Should NOT return token

    def test_login_revokes_existing_sessions(self, client, mock_user):
        """Test that login revokes all existing sessions for the user."""
        with patch(
            'backend.services.user_service.authenticate_user'
        ) as mock_auth, \
             patch(
            'backend.services.user_service.revoke_all_user_sessions'
        ) as mock_revoke:
            mock_auth.return_value = (mock_user, "new_session")

            response = client.post(
                "/api/users/login",
                json={
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": "password123"
                }
            )

            assert response.status_code == 200

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        with patch(
            'backend.services.user_service.authenticate_user'
        ) as mock_auth:
            mock_auth.side_effect = ValueError("Invalid credentials")

            response = client.post(
                "/api/users/login",
                json={
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": "wrongpassword"
                }
            )

            assert response.status_code == 401
            assert "Invalid credentials" in response.json()["detail"]


# ==================== Check Session Tests ====================

class TestCheckSession:
    """Tests for /api/users/check-session/{session_id} endpoint."""

    def test_check_valid_session(self, client, mock_user):
        """Test checking a valid session ID."""
        with patch(
            'backend.services.user_service.verify_session_id'
        ) as mock_verify:
            mock_verify.return_value = mock_user

            response = client.get("/api/users/check-session/abc123XY")

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Session is valid"
            assert data["logged_in"] is True
            assert data["user"]["email"] == "test@example.com"

    def test_check_invalid_session(self, client):
        """Test checking an invalid session ID."""
        with patch(
            'backend.services.user_service.verify_session_id'
        ) as mock_verify:
            mock_verify.return_value = None

            response = client.get("/api/users/check-session/invalid-id")

            assert response.status_code == 401
            assert "Invalid or expired session" in response.json()["detail"]

    def test_check_session_with_url_parameter(self, client, mock_user):
        """Test that session ID is passed via URL."""
        with patch(
            'backend.services.user_service.verify_session_id'
        ) as mock_verify:
            mock_verify.return_value = mock_user

            # Session ID is in the URL, not in request body
            response = client.get("/api/users/check-session/testSessionID")

            mock_verify.assert_called_once_with("testSessionID")
            assert response.status_code == 200


# ==================== Signout Tests ====================

class TestSignout:
    """Tests for /api/users/signout endpoint with session ID."""

    def test_signout_success_with_auth(self, client, mock_user):
        """Test successful signout with valid authentication."""
        with patch(
            'backend.services.user_service.verify_session_id'
        ) as mock_verify, \
             patch(
            'backend.services.user_service.signout_user'
        ) as mock_signout:
            mock_verify.return_value = mock_user
            mock_signout.return_value = True

            response = client.post(
                "/api/users/signout",
                json={"session_id": "abc123XY"},
                headers={"Authorization": "Bearer abc123XY"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Successfully signed out"
            mock_signout.assert_called_once_with("abc123XY")

    def test_signout_without_auth_header(self, client):
        """Test signout fails without Authorization header."""
        response = client.post(
            "/api/users/signout",
            json={"session_id": "abc123XY"}
        )

        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    def test_signout_with_invalid_session(self, client):
        """Test signout with invalid session in header."""
        with patch(
            'backend.services.user_service.verify_session_id'
        ) as mock_verify:
            mock_verify.return_value = None

            response = client.post(
                "/api/users/signout",
                json={"session_id": "abc123XY"},
                headers={"Authorization": "Bearer invalid"}
            )

            assert response.status_code == 401
            assert "Invalid or expired session" in response.json()["detail"]


# ==================== Complete Workflow Tests ====================

class TestUserWorkflow:
    """Tests for complete user workflow with session IDs."""

    def test_complete_authenticated_workflow(self, client, mock_user):
        """Test complete user workflow: login -> check profile -> signout."""
        session_id = "session123"

        # Step 1: Login
        with patch(
            'backend.services.user_service.authenticate_user'
        ) as mock_auth:
            mock_auth.return_value = (mock_user, session_id)

            login_response = client.post(
                "/api/users/login",
                json={
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": "password123"
                }
            )
            assert login_response.status_code == 200
            returned_session_id = login_response.json()["session_id"]
            assert returned_session_id == session_id

        # Step 2: Use authenticated feature (get own profile)
        with patch(
            'backend.services.user_service.verify_session_id'
        ) as mock_verify:
            mock_verify.return_value = mock_user

            profile_response = client.get(
                "/api/users/profile/me",
                headers={"Authorization": f"Bearer {session_id}"}
            )
            assert profile_response.status_code == 200
            assert profile_response.json()["user"]["email"] == "test@example.com"

        # Step 3: Sign out
        with patch(
            'backend.services.user_service.verify_session_id'
        ) as mock_verify, \
             patch(
            'backend.services.user_service.signout_user'
        ) as mock_signout:
            mock_verify.return_value = mock_user
            mock_signout.return_value = True

            signout_response = client.post(
                "/api/users/signout",
                json={"session_id": session_id},
                headers={"Authorization": f"Bearer {session_id}"}
            )
            assert signout_response.status_code == 200

        # Step 4: Verify cannot use features after signout
        with patch(
            'backend.services.user_service.verify_session_id'
        ) as mock_verify:
            mock_verify.return_value = None

            profile_response = client.get(
                "/api/users/profile/me",
                headers={"Authorization": f"Bearer {session_id}"}
            )
            assert profile_response.status_code == 401

    def test_multiple_logins_different_session_ids(self, client, mock_user):
        """Test that multiple logins create different session IDs."""
        session_ids = []

        for i in range(3):
            with patch(
                'backend.services.user_service.authenticate_user'
            ) as mock_auth:
                mock_auth.return_value = (mock_user, f"session{i}")

                response = client.post(
                    "/api/users/login",
                    json={
                        "email": "test@example.com",
                        "username": "testuser",
                        "password": "password123"
                    }
                )
                session_id = response.json()["session_id"]
                session_ids.append(session_id)

        # All session IDs should be different
        assert len(set(session_ids)) == 3
