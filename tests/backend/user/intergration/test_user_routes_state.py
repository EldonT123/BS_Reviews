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
    return User("test@example.com", "hashed_password", User.TIER_SNAIL)


# ==================== Login Tests ====================

class TestLogin:
    """Tests for /api/login endpoint with session ID."""

    def test_login_returns_session_id(self, client, mock_user):
        """Test that login returns a session ID instead of token."""
        with patch(
            'backend.services.user_service.authenticate_user'
        ) as mock_auth:
            mock_auth.return_value = (mock_user, "abc123XY")

            response = client.post(
                "/api/login",
                json={
                    "email": "test@example.com",
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

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        with patch(
            'backend.services.user_service.authenticate_user'
        ) as mock_auth:
            mock_auth.side_effect = ValueError("Invalid credentials")

            response = client.post(
                "/api/login",
                json={
                    "email": "test@example.com",
                    "password": "wrongpassword"
                }
            )

            assert response.status_code == 401
            assert "Invalid credentials" in response.json()["detail"]


# ==================== Check Session Tests ====================

class TestCheckSession:
    """Tests for /api/check-session/{session_id} endpoint."""

    def test_check_valid_session(self, client, mock_user):
        """Test checking a valid session ID."""
        with patch(
            'backend.services.user_service.verify_session_id'
        ) as mock_verify:
            mock_verify.return_value = mock_user

            response = client.get("/api/check-session/abc123XY")

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

            response = client.get("/api/check-session/invalid-id")

            assert response.status_code == 401
            assert "Invalid or expired session" in response.json()["detail"]

    def test_check_session_with_url_parameter(self, client, mock_user):
        """Test that session ID is passed via URL."""
        with patch(
            'backend.services.user_service.verify_session_id'
        ) as mock_verify:
            mock_verify.return_value = mock_user

            # Session ID is in the URL, not in request body
            response = client.get("/api/check-session/testSessionID")

            mock_verify.assert_called_once_with("testSessionID")
            assert response.status_code == 200


# ==================== Signout Tests ====================

class TestSignout:
    """Tests for /api/signout endpoint with session ID."""

    def test_signout_success(self, client):
        """Test successful signout with session ID."""
        with patch(
            'backend.services.user_service.signout_user'
        ) as mock_signout:
            mock_signout.return_value = True

            response = client.post(
                "/api/signout",
                json={"session_id": "abc123XY"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Successfully signed out"
            mock_signout.assert_called_once_with("abc123XY")

    def test_signout_invalid_session_id(self, client):
        """Test signout with invalid session ID."""
        with patch(
            'backend.services.user_service.signout_user'
        ) as mock_signout:
            mock_signout.return_value = False

            response = client.post(
                "/api/signout",
                json={"session_id": "invalid-id"}
            )

            assert response.status_code == 400
            assert "Invalid or expired session ID" in response.json()[
                "detail"
            ]

    def test_signout_missing_session_id(self, client):
        """Test signout without providing session ID."""
        response = client.post("/api/signout", json={})

        assert response.status_code == 422  # Validation error


# ==================== Complete Workflow Tests ====================

class TestUserWorkflow:
    """Tests for complete user workflow with session IDs."""

    def test_complete_login_check_signout_flow(self, client, mock_user):
        """Test complete user session workflow."""
        # Step 1: Login
        with patch(
            'backend.services.user_service.authenticate_user'
        ) as mock_auth:
            mock_auth.return_value = (mock_user, "session123")

            login_response = client.post(
                "/api/login",
                json={
                    "email": "test@example.com",
                    "password": "password123"
                }
            )
            assert login_response.status_code == 200
            session_id = login_response.json()["session_id"]
            assert session_id == "session123"

        # Step 2: Check session is valid
        with patch(
            'backend.services.user_service.verify_session_id'
        ) as mock_verify:
            mock_verify.return_value = mock_user

            check_response = client.get(f"/api/check-session/{session_id}")
            assert check_response.status_code == 200
            assert check_response.json()["logged_in"] is True

        # Step 3: Sign out
        with patch(
            'backend.services.user_service.signout_user'
        ) as mock_signout:
            mock_signout.return_value = True

            signout_response = client.post(
                "/api/signout",
                json={"session_id": session_id}
            )
            assert signout_response.status_code == 200

        # Step 4: Check session is now invalid
        with patch(
            'backend.services.user_service.verify_session_id'
        ) as mock_verify:
            mock_verify.return_value = None

            check_response = client.get(f"/api/check-session/{session_id}")
            assert check_response.status_code == 401

    def test_multiple_logins_different_session_ids(self, client, mock_user):
        """Test that multiple logins create different session IDs."""
        session_ids = []

        for i in range(3):
            with patch(
                'backend.services.user_service.authenticate_user'
            ) as mock_auth:
                mock_auth.return_value = (mock_user, f"session{i}")

                response = client.post(
                    "/api/login",
                    json={
                        "email": "test@example.com",
                        "password": "password123"
                    }
                )
                session_id = response.json()["session_id"]
                session_ids.append(session_id)

        # All session IDs should be different
        assert len(set(session_ids)) == 3
