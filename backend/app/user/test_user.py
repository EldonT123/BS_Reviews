import pytest
import os
from datetime import date
from auth_service import AuthService, AccountManager, MovieGoer, Admin

TEST_JSON = "test_users.json"

# --------------------------
# Fixtures
# --------------------------
@pytest.fixture
def auth_service():
    # Ensure clean JSON file
    if os.path.exists(TEST_JSON):
        os.remove(TEST_JSON)
    service = AuthService(TEST_JSON)
    yield service
    # Cleanup after tests
    if os.path.exists(TEST_JSON):
        os.remove(TEST_JSON)

@pytest.fixture
def account_manager(auth_service):
    return AccountManager(auth_service)

# --------------------------
# Tests
# --------------------------

def test_create_moviegoer(account_manager):
    result = account_manager.create_account(
        username="john_doe",
        password="password123",
        email="john@example.com",
        date_of_birth="2000-01-01",
        role="MovieGoer"
    )
    assert result is True

def test_create_admin(account_manager):
    result = account_manager.create_account(
        username="admin1",
        password="adminpass",
        email="admin@example.com",
        date_of_birth="1990-05-05",
        role="Admin"
    )
    assert result is True

def test_login_success(account_manager, auth_service):
    account_manager.create_account(
        username="jane_doe",
        password="securepass",
        email="jane@example.com",
        date_of_birth="2001-02-02",
        role="MovieGoer"
    )
    user = auth_service.login("jane_doe", "securepass")
    assert user is not None
    assert user.username == "jane_doe"
    assert isinstance(user, MovieGoer)

def test_login_wrong_password(account_manager, auth_service):
    account_manager.create_account(
        username="mark",
        password="mypassword",
        email="mark@example.com",
        date_of_birth="1995-06-06",
        role="MovieGoer"
    )
    user = auth_service.login("mark", "wrongpass")
    assert user is None

def test_reset_password(account_manager, auth_service):
    account_manager.create_account(
        username="alice",
        password="oldpass",
        email="alice@example.com",
        date_of_birth="1998-03-03",
        role="MovieGoer"
    )
    result = account_manager.reset_password("alice", "newpass")
    assert result is True

    # Login with new password
    user = auth_service.login("alice", "newpass")
    assert user is not None

def test_delete_account(account_manager, auth_service):
    account_manager.create_account(
        username="bob",
        password="bobpass",
        email="bob@example.com",
        date_of_birth="1992-04-04",
        role="MovieGoer"
    )
    deleted = account_manager.delete_account("bob")
    assert deleted is True

    # Check login fails
    user = auth_service.login("bob", "bobpass")
    assert user is None

def test_set_user_rank(account_manager, auth_service):
    account_manager.create_account(
        username="charlie",
        password="charpass",
        email="charlie@example.com",
        date_of_birth="2002-07-07",
        role="MovieGoer"
    )
    user = auth_service.login("charlie", "charpass")
    assert isinstance(user, MovieGoer)
    
    # Change rank
    result = user.set_user_rank("Banana Tree")
    assert result is True
    assert user.user_rank == "Banana Tree"

def test_admin_methods():
    admin = Admin(username="admin2", password="admin2pass", email="admin2@example.com", date_of_birth="1985-12-12")
    assert admin.add_movie() == "Movie added"
    assert admin.remove_movie() == "Movie removed"
    assert admin.edit_movie() == "Movie edited"
    assert admin.remove_review() == "Review removed"
    assert admin.remove_user() == "User removed"
    assert admin.apply_penalty() == "User penalized"
