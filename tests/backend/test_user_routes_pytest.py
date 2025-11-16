"""Tests for user authentication routes."""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import csv
import json
from backend.main import app
from backend.routes.user_routes import get_password_hash, verify_password

client = TestClient(app)

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "ValidPass123!"


# ==================== UNIT TESTS - Password Functions ====================

def test_password_hash_returns_string():
    """Test that get_password_hash returns a hashed string."""
    hashed = get_password_hash(TEST_PASSWORD)
    
    assert isinstance(hashed, str)
    assert len(hashed) > 0
    assert hashed != TEST_PASSWORD


def test_password_hash_different_for_same_password():
    """Test that same password generates different hashes due to salt."""
    hash1 = get_password_hash(TEST_PASSWORD)
    hash2 = get_password_hash(TEST_PASSWORD)
    
    assert hash1 != hash2


def test_verify_password_correct():
    """Test that verify_password returns True for correct password."""
    hashed = get_password_hash(TEST_PASSWORD)
    
    assert verify_password(TEST_PASSWORD, hashed) is True


def test_verify_password_incorrect():
    """Test that verify_password returns False for wrong password."""
    hashed = get_password_hash(TEST_PASSWORD)
    wrong_password = "WrongPassword456!"
    
    assert verify_password(wrong_password, hashed) is False


def test_password_truncation_long_password():
    """Test that passwords longer than 72 bytes are handled correctly."""
    long_password = "a" * 100
    hashed = get_password_hash(long_password)
    
    assert verify_password(long_password, hashed) is True


# ==================== UNIT TESTS - CSV Operations ====================

def test_read_users_empty_file(temp_user_csv):
    """Test reading from empty CSV file."""
    from backend.routes.user_routes import read_users
    
    users = read_users()
    assert users == {}


def test_read_users_with_data(temp_user_csv):
    """Test reading users from populated CSV."""
    from backend.routes.user_routes import read_users, append_user
    
    # Add test users
    append_user("user1@test.com", "hash1")
    append_user("user2@test.com", "hash2")
    
    users = read_users()
    assert "user1@test.com" in users
    assert "user2@test.com" in users
    assert users["user1@test.com"] == "hash1"


def test_read_users_case_insensitive(temp_user_csv):
    """Test that email keys are stored in lowercase."""
    from backend.routes.user_routes import read_users, append_user
    
    append_user("Test@Example.COM", "hashed123")
    users = read_users()
    
    assert "test@example.com" in users
    assert "Test@Example.COM" not in users


def test_append_user_creates_entry(temp_user_csv):
    """Test that append_user adds user to CSV."""
    from backend.routes.user_routes import append_user, read_users
    
    append_user("newuser@test.com", "hashedpass789")
    users = read_users()
    
    assert "newuser@test.com" in users
    assert users["newuser@test.com"] == "hashedpass789"


# ==================== INTEGRATION TESTS - Signup Endpoint ====================

def test_signup_success(temp_user_csv):
    """Test successful user signup."""
    response = client.post(
        "/api/signup",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    
    assert response.status_code == 200
    assert response.json() == {"message": "Signup successful"}


def test_signup_duplicate_email(temp_user_csv):
    """Test signup fails with duplicate email."""
    # First signup
    client.post(
        "/api/signup",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    
    # Second signup with same email
    response = client.post(
        "/api/signup",
        json={"email": TEST_EMAIL, "password": "DifferentPass456!"}
    )
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_signup_case_insensitive_email(temp_user_csv):
    """Test that email comparison is case-insensitive."""
    # Signup with lowercase
    client.post(
        "/api/signup",
        json={"email": "user@example.com", "password": TEST_PASSWORD}
    )
    
    # Try signup with uppercase
    response = client.post(
        "/api/signup",
        json={"email": "USER@EXAMPLE.COM", "password": "Different123!"}
    )
    
    assert response.status_code == 400


def test_signup_invalid_email():
    """Test signup with invalid email format."""
    response = client.post(
        "/api/signup",
        json={"email": "not-an-email", "password": TEST_PASSWORD}
    )
    
    assert response.status_code == 422


def test_signup_missing_password():
    """Test signup with missing password field."""
    response = client.post(
        "/api/signup",
        json={"email": TEST_EMAIL}
    )
    
    assert response.status_code == 422


# ==================== INTEGRATION TESTS - Login Endpoint ====================

def test_login_success(temp_user_csv):
    """Test successful login with correct credentials."""
    # Create user first
    client.post(
        "/api/signup",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    
    # Now login
    response = client.post(
        "/api/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    
    assert response.status_code == 200
    assert response.json() == {"message": "Login successful"}


def test_login_wrong_password(temp_user_csv):
    """Test login fails with wrong password."""
    # Create user
    client.post(
        "/api/signup",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    
    # Try login with wrong password
    response = client.post(
        "/api/login",
        json={"email": TEST_EMAIL, "password": "WrongPassword456!"}
    )
    
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


def test_login_nonexistent_user(temp_user_csv):
    """Test login fails for non-existent user."""
    response = client.post(
        "/api/login",
        json={"email": "nonexistent@example.com", "password": TEST_PASSWORD}
    )
    
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


def test_login_case_insensitive_email(temp_user_csv):
    """Test that login works with different email casing."""
    # Signup with lowercase
    client.post(
        "/api/signup",
        json={"email": "user@example.com", "password": TEST_PASSWORD}
    )
    
    # Login with uppercase
    response = client.post(
        "/api/login",
        json={"email": "USER@EXAMPLE.COM", "password": TEST_PASSWORD}
    )
    
    assert response.status_code == 200


def test_login_invalid_email_format():
    """Test login with invalid email format."""
    response = client.post(
        "/api/login",
        json={"email": "not-an-email", "password": TEST_PASSWORD}
    )
    
    assert response.status_code == 422


# ==================== INTEGRATION TESTS - End-to-End Flows ====================

def test_integration_signup_then_login(temp_user_csv):
    """Integration test: Complete signup and login flow."""
    email = "flow@example.com"
    password = "FlowTest123!"
    
    # Step 1: Signup
    signup_response = client.post(
        "/api/signup",
        json={"email": email, "password": password}
    )
    assert signup_response.status_code == 200
    
    # Step 2: Login with same credentials
    login_response = client.post(
        "/api/login",
        json={"email": email, "password": password}
    )
    assert login_response.status_code == 200
    
    # Step 3: Try to signup again (should fail)
    duplicate_response = client.post(
        "/api/signup",
        json={"email": email, "password": "NewPassword456!"}
    )
    assert duplicate_response.status_code == 400
    
    # Step 4: Login with wrong password (should fail)
    wrong_login_response = client.post(
        "/api/login",
        json={"email": email, "password": "WrongPassword789!"}
    )
    assert wrong_login_response.status_code == 401


def test_integration_multiple_users(temp_user_csv):
    """Integration test: Managing multiple users."""
    users = [
        ("user1@example.com", "Password1!"),
        ("user2@example.com", "Password2!"),
        ("user3@example.com", "Password3!")
    ]
    
    # Signup all users
    for email, password in users:
        response = client.post(
            "/api/signup",
            json={"email": email, "password": password}
        )
        assert response.status_code == 200
    
    # Login with each user
    for email, password in users:
        response = client.post(
            "/api/login",
            json={"email": email, "password": password}
        )
        assert response.status_code == 200
    
    # Verify user count in CSV
    from backend.routes.user_routes import read_users
    all_users = read_users()
    assert len(all_users) >= 3


def test_integration_password_security(temp_user_csv):
    """Integration test: Verify passwords are hashed in storage."""
    password = "SecurePassword123!"
    
    # Create user
    client.post(
        "/api/signup",
        json={"email": TEST_EMAIL, "password": password}
    )
    
    # Read CSV directly and verify password is hashed
    from backend.routes.user_routes import USER_CSV_PATH
    csv_path = Path(USER_CSV_PATH)
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            if row[0] == TEST_EMAIL.lower():
                stored_password = row[1]
                # Password should be hashed (bcrypt hashes start with $2b$)
                assert stored_password.startswith('$2b$')
                assert stored_password != password
                break