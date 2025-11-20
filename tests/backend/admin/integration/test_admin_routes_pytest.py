"""Tests for admin authentication routes and admin operations."""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import csv
from backend.main import app
from backend.services import admin_service, user_service
from backend.models.admin_model import Admin
from backend.models.user_model import User

client = TestClient(app)

TEST_ADMIN_EMAIL = "admin@example.com"
TEST_ADMIN_PASSWORD = "AdminPass123!"
TEST_USER_EMAIL = "user@example.com"
TEST_USER_PASSWORD = "UserPass123!"


# ==================== HELPER FUNCTIONS ====================

def create_admin_and_get_token(email=TEST_ADMIN_EMAIL, password=TEST_ADMIN_PASSWORD):
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


# ==================== INTEGRATION TESTS - Admin Signup Endpoint ====================

def test_admin_signup_success(temp_admin_csv):
    """Test successful admin signup."""
    response = client.post(
        "/api/admin/signup",
        json={"email": TEST_ADMIN_EMAIL, "password": TEST_ADMIN_PASSWORD}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "admin" in data
    assert "token" in data
    assert data["admin"]["email"] == TEST_ADMIN_EMAIL.lower()
    assert data["admin"]["role"] == "admin"


def test_admin_signup_duplicate_email(temp_admin_csv):
    """Test admin signup fails with duplicate email."""
    # First signup
    client.post(
        "/api/admin/signup",
        json={"email": TEST_ADMIN_EMAIL, "password": TEST_ADMIN_PASSWORD}
    )
    
    # Second signup with same email
    response = client.post(
        "/api/admin/signup",
        json={"email": TEST_ADMIN_EMAIL, "password": "DifferentPass456!"}
    )
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_admin_signup_case_insensitive_email(temp_admin_csv):
    """Test that admin email comparison is case-insensitive."""
    # Signup with lowercase
    client.post(
        "/api/admin/signup",
        json={"email": "admin@example.com", "password": TEST_ADMIN_PASSWORD}
    )
    
    # Try signup with uppercase
    response = client.post(
        "/api/admin/signup",
        json={"email": "ADMIN@EXAMPLE.COM", "password": "Different123!"}
    )
    
    assert response.status_code == 400


def test_admin_signup_invalid_email():
    """Test admin signup with invalid email format."""
    response = client.post(
        "/api/admin/signup",
        json={"email": "not-an-email", "password": TEST_ADMIN_PASSWORD}
    )
    
    assert response.status_code == 422


# ==================== INTEGRATION TESTS - Admin Login Endpoint ====================

def test_admin_login_success(temp_admin_csv):
    """Test successful admin login with correct credentials."""
    # Create admin first
    client.post(
        "/api/admin/signup",
        json={"email": TEST_ADMIN_EMAIL, "password": TEST_ADMIN_PASSWORD}
    )
    
    # Now login
    response = client.post(
        "/api/admin/login",
        json={"email": TEST_ADMIN_EMAIL, "password": TEST_ADMIN_PASSWORD}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "admin" in data
    assert "token" in data
    assert data["admin"]["role"] == "admin"
    assert data["admin"]["permissions"]["can_manage_users"] is True


def test_admin_login_wrong_password(temp_admin_csv):
    """Test admin login fails with wrong password."""
    # Create admin
    client.post(
        "/api/admin/signup",
        json={"email": TEST_ADMIN_EMAIL, "password": TEST_ADMIN_PASSWORD}
    )
    
    # Try login with wrong password
    response = client.post(
        "/api/admin/login",
        json={"email": TEST_ADMIN_EMAIL, "password": "WrongPassword456!"}
    )
    
    assert response.status_code == 401
    assert "Invalid admin credentials" in response.json()["detail"]


def test_admin_login_nonexistent_admin(temp_admin_csv):
    """Test admin login fails for non-existent admin."""
    response = client.post(
        "/api/admin/login",
        json={"email": "nonexistent@example.com", "password": TEST_ADMIN_PASSWORD}
    )
    
    assert response.status_code == 401


def test_admin_login_case_insensitive_email(temp_admin_csv):
    """Test that admin login works with different email casing."""
    # Signup with lowercase
    client.post(
        "/api/admin/signup",
        json={"email": "admin@example.com", "password": TEST_ADMIN_PASSWORD}
    )
    
    # Login with uppercase
    response = client.post(
        "/api/admin/login",
        json={"email": "ADMIN@EXAMPLE.COM", "password": TEST_ADMIN_PASSWORD}
    )
    
    assert response.status_code == 200


# ==================== INTEGRATION TESTS - User Management ====================

def test_admin_get_all_users(temp_admin_csv, temp_user_csv):
    """Test admin can view all users."""
    # Get admin token
    token = create_admin_and_get_token()
    headers = get_auth_headers(token)
    
    # Create some users
    client.post("/api/signup", json={"email": "user1@test.com", "password": TEST_USER_PASSWORD})
    client.post("/api/signup", json={"email": "user2@test.com", "password": TEST_USER_PASSWORD})
    
    response = client.get("/api/admin/users", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert data["total"] >= 2


def test_admin_upgrade_user_tier(temp_admin_csv, temp_user_csv):
    """Test admin upgrading user tier."""
    # Get admin token
    token = create_admin_and_get_token()
    headers = get_auth_headers(token)
    
    # Create a user
    client.post(
        "/api/signup",
        json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    )
    
    # Upgrade to Slug
    response = client.post(
        "/api/admin/users/upgrade-tier",
        headers=headers,
        json={"email": TEST_USER_EMAIL, "new_tier": User.TIER_SLUG}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["tier"] == User.TIER_SLUG


def test_admin_upgrade_invalid_tier(temp_admin_csv, temp_user_csv):
    """Test admin upgrade with invalid tier."""
    # Get admin token
    token = create_admin_and_get_token()
    headers = get_auth_headers(token)
    
    # Create a user
    client.post(
        "/api/signup",
        json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    )
    
    # Try invalid tier
    response = client.post(
        "/api/admin/users/upgrade-tier",
        headers=headers,
        json={"email": TEST_USER_EMAIL, "new_tier": "super_slug"}
    )
    
    assert response.status_code == 400


def test_admin_upgrade_nonexistent_user(temp_admin_csv):
    """Test admin upgrade fails for non-existent user."""
    # Get admin token
    token = create_admin_and_get_token()
    headers = get_auth_headers(token)
    
    response = client.post(
        "/api/admin/users/upgrade-tier",
        headers=headers,
        json={"email": "nonexistent@test.com", "new_tier": User.TIER_SLUG}
    )
    
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


def test_admin_delete_user(temp_admin_csv, temp_user_csv):
    """Test admin deleting a user."""
    # Get admin token
    token = create_admin_and_get_token()
    headers = get_auth_headers(token)
    
    # Create a user
    client.post(
        "/api/signup",
        json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    )
    
    # Delete the user
    import json
    response = client.request(
        "DELETE",
        "/api/admin/users",
        content=json.dumps({"email": TEST_USER_EMAIL}),
        headers={**headers, "Content-Type": "application/json"}
    )
    
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]
    
    # Verify user is deleted
    user = user_service.get_user_by_email(TEST_USER_EMAIL)
    assert user is None


def test_admin_delete_nonexistent_user(temp_admin_csv):
    """Test admin delete fails for non-existent user."""
    # Get admin token
    token = create_admin_and_get_token()
    headers = get_auth_headers(token)
    
    import json
    response = client.request(
        "DELETE",
        "/api/admin/users",
        content=json.dumps({"email": "nonexistent@test.com"}),
        headers={**headers, "Content-Type": "application/json"}
    )
    
    assert response.status_code == 404


# ==================== INTEGRATION TESTS - Admin Management ====================

def test_admin_get_all_admins(temp_admin_csv):
    """Test getting all admins."""
    # Create first admin and get token
    token = create_admin_and_get_token("admin1@test.com", TEST_ADMIN_PASSWORD)
    headers = get_auth_headers(token)
    
    # Create another admin
    client.post("/api/admin/signup", json={"email": "admin2@test.com", "password": TEST_ADMIN_PASSWORD})
    
    response = client.get("/api/admin/admins", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "admins" in data
    assert data["total"] >= 2


# ==================== INTEGRATION TESTS - End-to-End Flows ====================

def test_integration_admin_signup_then_login(temp_admin_csv):
    """Integration test: Complete admin signup and login flow."""
    email = "flowadmin@example.com"
    password = "FlowAdmin123!"
    
    # Step 1: Signup
    signup_response = client.post(
        "/api/admin/signup",
        json={"email": email, "password": password}
    )
    assert signup_response.status_code == 200
    assert signup_response.json()["admin"]["role"] == "admin"
    assert "token" in signup_response.json()
    
    # Step 2: Login with same credentials
    login_response = client.post(
        "/api/admin/login",
        json={"email": email, "password": password}
    )
    assert login_response.status_code == 200
    assert "token" in login_response.json()
    
    # Step 3: Try to signup again (should fail)
    duplicate_response = client.post(
        "/api/admin/signup",
        json={"email": email, "password": "NewPassword456!"}
    )
    assert duplicate_response.status_code == 400


def test_integration_admin_manages_multiple_users(temp_admin_csv, temp_user_csv):
    """Integration test: Admin managing multiple users."""
    # Get admin token
    token = create_admin_and_get_token()
    headers = get_auth_headers(token)
    
    users = [
        ("user1@example.com", "Password1!"),
        ("user2@example.com", "Password2!"),
        ("user3@example.com", "Password3!")
    ]
    
    # Create all users
    for email, password in users:
        response = client.post(
            "/api/signup",
            json={"email": email, "password": password}
        )
        assert response.status_code == 200
    
    # Admin upgrades different users to different tiers
    client.post(
        "/api/admin/users/upgrade-tier",
        headers=headers,
        json={"email": users[0][0], "new_tier": User.TIER_SLUG}
    )
    client.post(
        "/api/admin/users/upgrade-tier",
        headers=headers,
        json={"email": users[1][0], "new_tier": User.TIER_BANANA_SLUG}
    )
    
    # Verify all users exist with correct tiers
    response = client.get("/api/admin/users", headers=headers)
    assert response.status_code == 200
    user_list = response.json()["users"]
    
    tier_map = {u["email"]: u["tier"] for u in user_list}
    assert tier_map[users[0][0]] == User.TIER_SLUG
    assert tier_map[users[1][0]] == User.TIER_BANANA_SLUG
    assert tier_map[users[2][0]] == User.TIER_SNAIL
    
    # Admin deletes one user
    import json
    client.request(
        "DELETE",
        "/api/admin/users",
        content=json.dumps({"email": users[2][0]}),
        headers={**headers, "Content-Type": "application/json"}
    )
    
    # Verify user count decreased
    response = client.get("/api/admin/users", headers=headers)
    assert response.json()["total"] == 2


def test_integration_admin_password_security(temp_admin_csv):
    """Integration test: Verify admin passwords are hashed in storage."""
    password = "SecureAdminPass123!"
    
    # Create admin
    client.post(
        "/api/admin/signup",
        json={"email": TEST_ADMIN_EMAIL, "password": password}
    )
    
    # Read CSV directly and verify password is hashed
    from backend.services.admin_service import ADMIN_CSV_PATH
    csv_path = Path(ADMIN_CSV_PATH)
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            if row[0] == TEST_ADMIN_EMAIL.lower():
                stored_password = row[1]
                # Password should be hashed (bcrypt hashes start with $2b$)
                assert stored_password.startswith('$2b$')
                assert stored_password != password
                break


def test_integration_separate_admin_and_user_accounts(temp_admin_csv, temp_user_csv):
    """Integration test: Verify admin and user accounts are separate."""
    email = "same@example.com"
    
    # Create user with this email
    user_response = client.post("/api/signup", json={"email": email, "password": "UserPass123!"})
    assert user_response.status_code == 200
    
    # Create admin with same email (should work - different systems)
    admin_response = client.post("/api/admin/signup", json={"email": email, "password": "AdminPass123!"})
    assert admin_response.status_code == 200
    
    # Verify both exist independently
    assert user_service.user_exists(email) is True
    assert admin_service.admin_exists(email) is True


def test_admin_authentication_required(temp_admin_csv, temp_user_csv):
    """Test that protected endpoints require authentication."""
    # Try to access protected endpoints without token
    response = client.get("/api/admin/users")
    assert response.status_code == 401
    
    response = client.get("/api/admin/admins")
    assert response.status_code == 401
    
    response = client.post(
        "/api/admin/users/upgrade-tier",
        json={"email": "test@test.com", "new_tier": "slug"}
    )
    assert response.status_code == 401
