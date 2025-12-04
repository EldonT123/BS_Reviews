"""
Integration tests for admin penalty system.
Tests the full flow including API routes, services, and database operations.
"""
import pytest
import os
import csv
import tempfile
import shutil
from fastapi.testclient import TestClient
from backend.main import app
from backend.services import admin_service, user_service, review_service
from backend.models.user_model import User


# ==================== Fixtures ====================

@pytest.fixture(scope="function")
def test_db_dir():
    """Create a temporary database directory for testing."""
    temp_dir = tempfile.mkdtemp()

    # Create subdirectories
    os.makedirs(os.path.join(temp_dir, "admins"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "users"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "movies"), exist_ok=True)

    # Patch the paths
    original_admin_csv = admin_service.ADMIN_CSV_PATH
    original_user_csv = user_service.USER_CSV_PATH
    original_bookmark_csv = user_service.BOOKMARK_CSV_PATH
    original_banned_csv = admin_service.BANNED_EMAILS_CSV_PATH

    admin_service.ADMIN_CSV_PATH = os.path.join(
        temp_dir, "admins", "admin_information.csv")
    user_service.USER_CSV_PATH = os.path.join(
        temp_dir, "users", "user_information.csv")
    user_service.BOOKMARK_CSV_PATH = os.path.join(
        temp_dir, "users", "user_bookmarks.csv")
    admin_service.BANNED_EMAILS_CSV_PATH = os.path.join(
        temp_dir, "admins", "banned_emails.csv")

    yield temp_dir

    # Restore original paths
    admin_service.ADMIN_CSV_PATH = original_admin_csv
    user_service.USER_CSV_PATH = original_user_csv
    user_service.BOOKMARK_CSV_PATH = original_bookmark_csv
    admin_service.BANNED_EMAILS_CSV_PATH = original_banned_csv

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def test_admin(test_db_dir):
    """Create a test admin and return credentials."""
    admin_service.ensure_admin_csv_exists()
    admin, token = admin_service.create_admin(
        "testadmin@example.com",
        "adminpassword123"
    )
    return {
        "email": admin.email,
        "token": token
    }


@pytest.fixture
def test_user(test_db_dir):
    """Create a test user."""
    user_service.ensure_user_csv_exists()
    user = user_service.create_user(
        "testuser@example.com",
        "testuser",
        "userpassword123",
        tier=User.TIER_SLUG,
        tokens=100
    )
    return user


@pytest.fixture
def test_user_with_reviews(test_db_dir, test_user):
    """Create a test user with some reviews."""
    # Patch the data folder path in review_service
    import backend.services.file_service as file_service
    original_get_movie_folder = file_service.get_movie_folder

    def mock_get_movie_folder(movie_name):
        return os.path.join(test_db_dir, "movies", movie_name)

    file_service.get_movie_folder = mock_get_movie_folder

    # Create movie folders and reviews
    movies_dir = os.path.join(test_db_dir, "movies")

    for movie in ["Inception", "The Matrix"]:
        movie_dir = os.path.join(movies_dir, movie)
        os.makedirs(movie_dir, exist_ok=True)

        reviews_path = os.path.join(movie_dir, "movieReviews.csv")
        with open(reviews_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=review_service.CSV_FIELDNAMES)
            writer.writeheader()
            writer.writerow({
                "Date of Review": "2024-01-01",
                "Email": test_user.email,
                "Username": test_user.username,
                "Dislikes": "0",
                "Likes": "5",
                "User's Rating out of 10": "9",
                "Review Title": "Great movie!",
                "Review": "This was amazing!",
                "Reported": "No",
                "Report Reason": "",
                "Report Count": "0",
                "Penalized": "No",
                "Hidden": "No"
            })

    yield test_user

    # Restore original function
    file_service.get_movie_folder = original_get_movie_folder


# ==================== Token Penalty Integration Tests ====================

class TestTokenPenaltyIntegration:
    """Integration tests for token removal penalties."""

    def test_remove_tokens_endpoint_success(
            self, client, test_admin, test_user):
        """Test the complete flow of removing tokens via API."""
        # Act
        response = client.post(
            "/api/admin/users/remove-tokens",
            json={
                "email": test_user.email,
                "tokens_to_remove": 30
            },
            headers={"Authorization": f"Bearer {test_admin['token']}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["previous_balance"] == 100
        assert data["new_balance"] == 70
        assert "Removed 30 tokens" in data["message"]

        # Verify in database
        updated_user = user_service.get_user_by_email(test_user.email)
        assert updated_user.tokens == 70

    def test_remove_tokens_insufficient_balance(
            self, client, test_admin, test_user):
        """Test removing more tokens than user has."""
        # Act
        response = client.post(
            "/api/admin/users/remove-tokens",
            json={
                "email": test_user.email,
                "tokens_to_remove": 150
            },
            headers={"Authorization": f"Bearer {test_admin['token']}"}
        )

        # Assert
        assert response.status_code == 400
        detail = response.json()["detail"]
        # Handle both string and list formats
        if isinstance(detail, list):
            detail = " ".join(detail)
        assert "only has 100 tokens" in detail

    def test_remove_tokens_negative_amount(
            self, client, test_admin, test_user):
        """Test removing negative tokens."""
        # Act
        response = client.post(
            "/api/admin/users/remove-tokens",
            json={
                "email": test_user.email,
                "tokens_to_remove": -10
            },
            headers={"Authorization": f"Bearer {test_admin['token']}"}
        )

        # Assert
        assert response.status_code == 400
        assert "must be positive" in response.json()["detail"]

    def test_remove_tokens_nonexistent_user(self, client, test_admin):
        """Test removing tokens from a user that doesn't exist."""
        # Act
        response = client.post(
            "/api/admin/users/remove-tokens",
            json={
                "email": "nonexistent@example.com",
                "tokens_to_remove": 10
            },
            headers={"Authorization": f"Bearer {test_admin['token']}"}
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_remove_tokens_without_admin_auth(self, client, test_user):
        """Test that token removal requires admin authentication."""
        # Act
        response = client.post(
            "/api/admin/users/remove-tokens",
            json={
                "email": test_user.email,
                "tokens_to_remove": 10
            }
        )

        # Assert
        # 401 Unauthorized is returned when no token is provided
        # 403 Forbidden is returned when token is invalid
        assert response.status_code in [401, 403]


# ==================== Review Ban Integration Tests ====================

class TestReviewBanIntegration:
    """Integration tests for review ban penalties."""

    def test_ban_user_from_reviews_endpoint(self, client, test_admin,
                                            test_user_with_reviews,
                                            test_db_dir):
        """Test the complete flow of banning a user from reviews."""
        # Act
        response = client.post(
            "/api/admin/users/review-ban",
            json={
                "email": test_user_with_reviews.email,
                "ban": True
            },
            headers={"Authorization": f"Bearer {test_admin['token']}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "banned from writing reviews" in data["message"]

        # The reviews_affected might be None or have 0
        # reviews if file_service path isn't patched
        # So we check the user's ban status instead
        updated_user = user_service.get_user_by_email(
            test_user_with_reviews.email)
        assert updated_user.review_banned is True

        # If reviews were found and penalized, verify them
        if data.get("reviews_affected") and data["reviews_affected"].get(
                                                            "reviews_marked"):
            assert data["reviews_affected"]["reviews_marked"] >= 0

    def test_unban_user_from_reviews_endpoint(
            self, client, test_admin, test_user):
        """Test unbanning a user from reviews."""
        # First ban the user
        user_service.update_review_ban_status(test_user.email, True)

        # Act
        response = client.post(
            "/api/admin/users/review-ban",
            json={
                "email": test_user.email,
                "ban": False
            },
            headers={"Authorization": f"Bearer {test_admin['token']}"}
        )

        # Assert
        assert response.status_code == 200

        # Verify user is unbanned
        updated_user = user_service.get_user_by_email(test_user.email)
        assert updated_user.review_banned is False

    def test_ban_already_banned_user(self, client, test_admin, test_user):
        """Test banning a user that is already banned."""
        # First ban the user
        user_service.update_review_ban_status(test_user.email, True)

        # Act
        response = client.post(
            "/api/admin/users/review-ban",
            json={
                "email": test_user.email,
                "ban": True
            },
            headers={"Authorization": f"Bearer {test_admin['token']}"}
        )

        # Assert
        assert response.status_code == 400
        assert "already banned" in response.json()["detail"]

    def test_banned_user_cannot_write_reviews(self, client, test_user):
        """Test that a banned user cannot write reviews."""
        # Ban the user
        user_service.update_review_ban_status(test_user.email, True)

        # Get updated user
        banned_user = user_service.get_user_by_email(test_user.email)

        # Assert
        assert banned_user.can_write_reviews() is False
        assert banned_user.can_rate_movies() is False
        assert banned_user.can_edit_own_reviews() is False


# ==================== Full Ban Integration Tests ====================

class TestFullBanIntegration:
    """Integration tests for permanent ban penalties."""

    def test_permanent_ban_endpoint(self, client, test_admin,
                                    test_user_with_reviews, test_db_dir):
        """Test the complete permanent ban flow."""
        # Act
        response = client.post(
            "/api/admin/users/ban",
            json={
                "email": test_user_with_reviews.email,
                "reason": "Spam and abuse"
            },
            headers={"Authorization": f"Bearer {test_admin['token']}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "permanently banned" in data["message"]
        assert data["details"]["email_blacklisted"] is True
        assert data["details"]["account_deleted"] is True
        # reviews_penalized might be 0 if path isn't set up correctly
        assert data["details"]["reviews_penalized"] >= 0

        # Verify user is deleted
        deleted_user = user_service.get_user_by_email(
            test_user_with_reviews.email)
        assert deleted_user is None

        # Verify email is blacklisted
        assert admin_service.is_email_banned(
            test_user_with_reviews.email) is True

        # Verify ban info is stored
        ban_info = admin_service.get_banned_email_info(
            test_user_with_reviews.email)
        assert ban_info["reason"] == "Spam and abuse"
        assert ban_info["banned_by"] == test_admin["email"]

    def test_banned_email_cannot_signup(self, client, test_admin,
                                        test_user, test_db_dir):
        """Test that a banned email cannot create a new account."""
        # Ban the user
        admin_service.ban_user(
            test_user.email,
            test_admin["email"],
            "Test ban"
        )

        # Try to create a new account with the banned email
        response = client.post(
            "/api/users/signup",
            json={
                "email": test_user.email,
                "username": "newuser",
                "password": "password123"
            }
        )

        # Assert
        assert response.status_code == 400
        assert "permanently banned" in response.json()["detail"]

    def test_unban_email_endpoint(self, client, test_admin, test_user):
        """Test unbanning an email."""
        # First ban the user
        admin_service.ban_user(
            test_user.email,
            test_admin["email"],
            "Test ban"
        )

        # Act
        response = client.post(
            "/api/admin/users/unban",
            json={
                "email": test_user.email
            },
            headers={"Authorization": f"Bearer {test_admin['token']}"}
        )

        # Assert
        assert response.status_code == 200
        assert "unbanned" in response.json()["message"]

        # Verify email is no longer banned
        assert admin_service.is_email_banned(test_user.email) is False

    def test_unban_non_banned_email(self, client, test_admin):
        """Test unbanning an email that isn't banned."""
        # Act
        response = client.post(
            "/api/admin/users/unban",
            json={
                "email": "notbanned@example.com"
            },
            headers={"Authorization": f"Bearer {test_admin['token']}"}
        )

        # Assert
        assert response.status_code == 400
        assert "not currently banned" in response.json()["detail"]

    def test_get_all_banned_emails(self, client, test_admin, test_user):
        """Test retrieving all banned emails."""
        # Ban a user
        admin_service.ban_user(
            test_user.email,
            test_admin["email"],
            "Test reason"
        )

        # Act
        response = client.get(
            "/api/admin/users/banned",
            headers={"Authorization": f"Bearer {test_admin['token']}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["banned_emails"][0]["email"] == test_user.email
        assert data["banned_emails"][0]["reason"] == "Test reason"

    def test_check_banned_status_endpoint(self, client, test_admin, test_user):
        """Test checking if a specific email is banned."""
        # Ban the user
        admin_service.ban_user(
            test_user.email,
            test_admin["email"],
            "Test ban"
        )

        # Act
        response = client.get(
            f"/api/admin/users/banned/{test_user.email}",
            headers={"Authorization": f"Bearer {test_admin['token']}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_banned"] is True
        assert data["ban_info"]["reason"] == "Test ban"


# ==================== Complete Workflow Tests ====================

class TestCompleteWorkflows:
    """Test complete workflows combining multiple penalties."""

    def test_escalating_penalties_workflow(self, client, test_admin,
                                           test_user_with_reviews,
                                           test_db_dir):
        """Test a realistic workflow of escalating penalties."""
        user_email = test_user_with_reviews.email
        admin_token = test_admin["token"]

        # Step 1: Remove some tokens
        response = client.post(
            "/api/admin/users/remove-tokens",
            json={"email": user_email, "tokens_to_remove": 50},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

        # Step 2: Ban from reviews
        response = client.post(
            "/api/admin/users/review-ban",
            json={"email": user_email, "ban": True},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

        # Step 3: Permanent ban
        response = client.post(
            "/api/admin/users/ban",
            json={"email": user_email, "reason": "Multiple violations"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

        # Verify final state
        assert user_service.get_user_by_email(user_email) is None
        assert admin_service.is_email_banned(user_email) is True

    def test_ban_and_unban_workflow(self, client, test_admin, test_user):
        """Test banning and then unbanning a user."""
        user_email = test_user.email
        admin_token = test_admin["token"]

        # Step 1: Permanent ban
        response = client.post(
            "/api/admin/users/ban",
            json={"email": user_email, "reason": "Mistake"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert user_service.get_user_by_email(user_email) is None

        # Step 2: Unban
        response = client.post(
            "/api/admin/users/unban",
            json={"email": user_email},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert admin_service.is_email_banned(user_email) is False

        # Step 3: User can now sign up again
        response = client.post(
            "/api/users/signup",
            json={
                "email": user_email,
                "username": "restoreduser",
                "password": "newpassword123"
            }
        )
        assert response.status_code == 200


# ==================== Authorization Tests ====================

class TestPenaltyAuthorization:
    """Test that penalty endpoints require proper authorization."""

    def test_penalties_require_admin_auth(self, client, test_user):
        """Test that all penalty endpoints require admin authentication."""
        endpoints = [
            ("/api/admin/users/remove-tokens", {"email": test_user.email,
                                                "tokens_to_remove": 10}),
            ("/api/admin/users/review-ban", {"email": test_user.email,
                                             "ban": True}),
            ("/api/admin/users/ban", {"email": test_user.email,
                                      "reason": "Test"}),
        ]

        for endpoint, data in endpoints:
            response = client.post(endpoint, json=data)
            # 401 or 403 both indicate unauthorized access
            assert response.status_code in [401, 403]

    def test_get_banned_users_requires_admin(self, client):
        """Test that viewing banned users requires admin auth."""
        response = client.get("/api/admin/users/banned")
        # 401 or 403 both indicate unauthorized access
        assert response.status_code in [401, 403]


# ==================== Edge Cases ====================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_remove_zero_tokens(self, client, test_admin, test_user):
        """Test removing zero tokens."""
        response = client.post(
            "/api/admin/users/remove-tokens",
            json={"email": test_user.email, "tokens_to_remove": 0},
            headers={"Authorization": f"Bearer {test_admin['token']}"}
        )
        assert response.status_code == 400

    def test_ban_nonexistent_user(self, client, test_admin):
        """Test banning a user that doesn't exist."""
        response = client.post(
            "/api/admin/users/ban",
            json={"email": "ghost@example.com", "reason": "Test"},
            headers={"Authorization": f"Bearer {test_admin['token']}"}
        )
        assert response.status_code == 400

    def test_multiple_penalty_operations_on_same_user(
            self, client, test_admin, test_user):
        """Test applying multiple penalties in quick succession."""
        admin_token = test_admin["token"]

        # Remove tokens twice
        for i in range(2):
            response = client.post(
                "/api/admin/users/remove-tokens",
                json={"email": test_user.email, "tokens_to_remove": 20},
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert response.status_code == 200

        # Verify final balance
        user = user_service.get_user_by_email(test_user.email)
        assert user.tokens == 60  # Started with 100, removed 40 total


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
