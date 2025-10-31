import pytest 
import os

from auth_service import MovieGoer, AuthService, AccountManager

TEST_JSON = "test_users.json"

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

@pytest.fixture
def movie_goer(account_manager, auth_service):
    account_manager.create_account(
        username="john_doe",
        password="password123",
        email="john@example.com",
        date_of_birth="2000-01-01",
        role="MovieGoer"
        )
    return  auth_service.login("john_doe", "password123")
    

def test_add(movie_goer):
    user = movie_goer

    result = user.add_bookmark("Avengers")

    assert result == True
