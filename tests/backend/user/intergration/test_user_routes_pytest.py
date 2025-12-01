"""Tests for user authentication routes and services."""
from fastapi.testclient import TestClient
from pathlib import Path
import csv
from backend.main import app
from backend.models.user_model import User

client = TestClient(app)

TEST_EMAIL = "test@example.com"
TEST_USERNAME = "testuser"
TEST_PASSWORD = "ValidPass123!"
TEST_ADMIN_PASSWORD = "AdminPass123!"

# ==================== HELPER FUNCTIONS ====================


def create_admin_and_get_token(
        email="admin@example.com", password=TEST_ADMIN_PASSWORD):
    """Helper function to create admin and return authentication token."""
    response = client.post(
        "/api/admin/signup",
        json={"email": email, "password": password}
    )
    if response.status_code == 200:
        return response.json()["token"]
    # If signup fails (already exists), try login
    response = client.post(
        "/api/admin/login",
        json={"email": email, "password": password}
    )
    return response.json()["token"]


def get_auth_headers(token):
    """Helper function to create authentication headers."""
    return {"X-Admin-Token": token}

# ==================== INTEGRATION TESTS - Signup Endpoint ====================


def test_signup_success(temp_user_csv):
    """Positive path: Test successful user signup."""
    response = client.post(
        "/api/users/signup",
        json={"email": TEST_EMAIL, "username": TEST_USERNAME, "password": TEST_PASSWORD}
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "user" in data
    assert data["user"]["email"] == TEST_EMAIL.lower()
    assert data["user"]["tier"] == User.TIER_SNAIL  # New users start as Snail


def test_signup_duplicate_email(temp_user_csv):
    """Negative path: Test signup fails with duplicate email."""
    # First signup
    client.post(
        "/api/users/signup",
        json={"email": TEST_EMAIL, "username": TEST_USERNAME, "password": TEST_PASSWORD}
    )

    # Second signup with same email
    response = client.post(
        "/api/users/signup",
        json={"email": TEST_EMAIL, "username": TEST_USERNAME, "password": "DifferentPass456!"}
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_signup_case_insensitive_email(temp_user_csv):
    """Edge case: Test that email comparison is case-insensitive."""
    # Signup with lowercase
    client.post(
        "/api/users/signup",
        json={"email": "user@example.com", "username": TEST_USERNAME, "password": TEST_PASSWORD}
    )

    # Try signup with uppercase
    response = client.post(
        "/api/users/signup",
        json={"email": "USER@EXAMPLE.COM", "username": TEST_USERNAME, "password": "Different123!"}
    )

    assert response.status_code == 400


def test_signup_invalid_email():
    """Edge case: Test signup with invalid email format."""
    response = client.post(
        "/api/users/signup",
        json={"email": "not-an-email", "username": TEST_USERNAME, "password": TEST_PASSWORD}
    )

    assert response.status_code == 422


def test_signup_missing_password():
    """Edge case: Test signup with missing password field."""
    response = client.post(
        "/api/users/signup",
        json={"email": TEST_EMAIL, "username": TEST_USERNAME}
    )
    
    assert response.status_code == 422


def test_signup_missing_username():
    """Test signup with missing username field."""
    response = client.post(
        "/api/users/signup",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )

    assert response.status_code == 422


# ==================== INTEGRATION TESTS - Login Endpoint ====================


def test_login_success(temp_user_csv):
    """Positive path: Test successful login with correct credentials."""
    # Create user first
    client.post(
        "/api/users/signup",
        json={"email": TEST_EMAIL, "username": TEST_USERNAME, "password": TEST_PASSWORD}
    )

    # Now login
    response = client.post(
        "/api/users/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "user" in data
    assert data["user"]["tier"] == User.TIER_SNAIL


def test_login_wrong_password(temp_user_csv):
    """Negative path: Test login fails with wrong password."""
    # Create user
    client.post(
        "/api/users/signup",
        json={"email": TEST_EMAIL, "username": TEST_USERNAME, "password": TEST_PASSWORD}
    )

    # Try login with wrong password
    response = client.post(
        "/api/users/login",
        json={"email": TEST_EMAIL, "password": "WrongPassword456!"}
    )

    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


def test_login_nonexistent_user(temp_user_csv):
    """Negative path: Test login fails for non-existent user."""
    response = client.post(
        "/api/users/login",
        json={"email": "nonexistent@example.com", "password": TEST_PASSWORD}
    )

    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


def test_login_case_insensitive_email(temp_user_csv):
    """Edge case: Test that login works with different email casing."""
    # Signup with lowercase
    client.post(
        "/api/users/signup",
        json={"email": "user@example.com", "username": TEST_USERNAME, "password": TEST_PASSWORD}
    )

    # Login with uppercase
    response = client.post(
        "/api/users/login",
        json={"email": "USER@EXAMPLE.COM", "password": TEST_PASSWORD}
    )

    assert response.status_code == 200


def test_login_invalid_email_format():
    """Edge case: Test login with invalid email format."""
    response = client.post(
        "/api/users/login",
        json={"email": "not-an-email", "password": TEST_PASSWORD}
    )

    assert response.status_code == 422


# ==================== INTEGRATION TESTS - Tier System ====================


def test_get_tier_info():
    """Test getting tier information."""
    response = client.get("/api/users/tiers")
    
    assert response.status_code == 200
    data = response.json()
    assert "tiers" in data
    assert len(data["tiers"]) == 3  # Snail, Slug, Banana Slug


def test_get_user_profile(temp_user_csv):
    """Positive path: Test getting user profile - requires authentication."""
    # Create a user and login
    client.post(
        "/api/users/signup",
        json={"email": TEST_EMAIL, "username": TEST_USERNAME, "password": TEST_PASSWORD}
    )

    # Login to get session
    login_response = client.post(
        "/api/users/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    session_id = login_response.json()["session_id"]

    # Get profile with authentication
    response = client.get(
        f"/api/users/profile/{TEST_EMAIL}",
        headers={"Authorization": f"Bearer {session_id}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "user" in data
    assert data["user"]["email"] == TEST_EMAIL.lower()


def test_get_user_profile_not_found(temp_user_csv):
    """Negative path: Test getting profile for
    non-existent user - requires authentication."""
    # Create a user and login to get authentication
    client.post(
        "/api/users/signup",
        json={"email": TEST_EMAIL, "username": TEST_USERNAME, "password": TEST_PASSWORD}
    )

    login_response = client.post(
        "/api/users/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    session_id = login_response.json()["session_id"]

    # Try to get profile for non-existent user (with valid authentication)
    response = client.get(
        "/api/users/profile/nonexistent@test.com",
        headers={"Authorization": f"Bearer {session_id}"}
    )

    assert response.status_code == 404


# ==================== INTEGRATION TESTS - Admin Routes ====================


def test_admin_upgrade_invalid_tier(temp_user_csv, temp_admin_csv):
    """Negative path: Test admin upgrade with invalid tier."""
    # Get admin token
    token = create_admin_and_get_token()
    headers = get_auth_headers(token)

    # Create a user
    client.post(
        "/api/users/signup",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )

    # Try invalid tier
    response = client.post(
        "/api/admin/users/upgrade-tier",
        headers=headers,
        json={"email": TEST_EMAIL, "new_tier": "super_slug"}
    )

    assert response.status_code == 400


def test_get_all_users(temp_user_csv, temp_admin_csv):
    """Positive path: Test getting all users."""
    # Get admin token
    token = create_admin_and_get_token()
    headers = get_auth_headers(token)

    # Create some users
    client.post("/api/users/signup", json={"email": "user1@test.com", "username": TEST_USERNAME, "password": TEST_PASSWORD})
    client.post("/api/users/signup", json={"email": "user2@test.com", "username": TEST_USERNAME, "password": TEST_PASSWORD})
    
    response = client.get("/api/admin/users", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert data["total"] >= 2


# ==================== INTEGRATION TESTS - End-to-End Flows ===================


def test_integration_signup_then_login(temp_user_csv):
    """Integration test: Complete signup and login flow."""
    
    # Step 1: Signup
    signup_response = client.post(
        "/api/users/signup",
        json={"email": TEST_EMAIL, "username": TEST_USERNAME, "password": TEST_PASSWORD}
    )
    assert signup_response.status_code == 200
    assert signup_response.json()["user"]["tier"] == User.TIER_SNAIL

    # Step 2: Login with same credentials
    login_response = client.post(
        "/api/users/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert login_response.status_code == 200

    # Step 3: Try to signup again (should fail)
    duplicate_response = client.post(
        "/api/users/signup",
        json={"email": TEST_EMAIL, "username": TEST_USERNAME, "password": "NewPassword456!"}
    )
    assert duplicate_response.status_code == 400

    # Step 4: Login with wrong password (should fail)
    wrong_login_response = client.post(
        "/api/users/login",
        json={"email": TEST_EMAIL, "password": "WrongPassword789!"}
    )
    assert wrong_login_response.status_code == 401


def test_integration_tier_progression(temp_user_csv, temp_admin_csv):
    """Positive path: User tier progression through admin actions."""
    # Get admin token
    token = create_admin_and_get_token()
    headers = get_auth_headers(token)

    # Signup (Snail tier)
    signup_response = client.post(
        "/api/users/signup",
        json={"email": TEST_EMAIL, "username": TEST_USERNAME, "password": TEST_PASSWORD}
    )
    assert signup_response.json()["user"]["tier"] == User.TIER_SNAIL
    assert signup_response.json()[
        "user"]["permissions"]["can_write_reviews"] is False

    # Upgrade to Slug (via admin endpoint)
    upgrade_response = client.post(
        "/api/admin/users/upgrade-tier",
        headers=headers,
        json={"email": TEST_EMAIL, "new_tier": User.TIER_SLUG}
    )
    assert upgrade_response.status_code == 200

    # Login and check new permissions
    login_response = client.post(
        "/api/users/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert login_response.json()["user"][
        "tier"] == User.TIER_SLUG
    assert login_response.json()[
        "user"]["permissions"]["can_write_reviews"] is True
    assert login_response.json()[
        "user"]["permissions"]["has_priority_reviews"] is False

    # Upgrade to Banana Slug
    upgrade_response = client.post(
        "/api/admin/users/upgrade-tier",
        headers=headers,
        json={"email": TEST_EMAIL, "new_tier": User.TIER_BANANA_SLUG}
    )
    assert upgrade_response.status_code == 200

    # Login and check VIP permissions
    login_response = client.post(
        "/api/users/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert login_response.json()[
        "user"]["tier"] == User.TIER_BANANA_SLUG
    assert login_response.json()[
        "user"]["permissions"]["has_priority_reviews"] is True


def test_integration_multiple_users(temp_user_csv, temp_admin_csv):
    """Positive path: Managing multiple users."""
    # Get admin token
    token = create_admin_and_get_token()
    headers = get_auth_headers(token)

    users = [
        ("user1@example.com", "user1", "Password1!", User.TIER_SNAIL),
        ("user2@example.com", "user2", "Password2!", User.TIER_SLUG),
        ("user3@example.com", "user3", "Password3!", User.TIER_BANANA_SLUG)
    ]

    # Signup all users
    for email, username, password, _ in users:
        response = client.post(
            "/api/users/signup",
            json={"email": email, "username": username, "password": password}
        )
        assert response.status_code == 200

    # Upgrade tiers via admin
    for email, _, _, tier in users:
        if tier != User.TIER_SNAIL:
            upgrade_response = client.post(
                "/api/admin/users/upgrade-tier",
                headers=headers,
                json={"email": email, "new_tier": tier}
            )
            assert upgrade_response.status_code == 200

    # Login with each user and verify tier
    for email, username, password, expected_tier in users:
        response = client.post(
            "/api/users/login",
            json={"email": email, "password": password}
        )

        assert response.status_code == 200
        assert response.json()["user"]["tier"] == expected_tier


def test_integration_password_security(temp_user_csv):
    """Edge case: Verify passwords are hashed in storage."""
    password = "SecurePassword123!"

    # Create user
    client.post(
        "/api/users/signup",
        json={"email": TEST_EMAIL, "username": TEST_USERNAME, "password": password}
    )

    # Read CSV directly and verify password is hashed
    from backend.services.user_service import USER_CSV_PATH
    csv_path = Path(USER_CSV_PATH)

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            if row[0] == TEST_EMAIL.lower():
                stored_password = row[2]
                # Password should be hashed (bcrypt hashes start with $2b$)
                assert stored_password.startswith('$2b$')
                assert stored_password != password
                break
