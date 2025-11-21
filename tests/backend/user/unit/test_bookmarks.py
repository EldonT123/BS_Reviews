import os
import csv 
import tempfile
import pytest

#important service youre testing
from backend.services import user_service

@pytest.fixture
def temp_user_and_bookmark_files(monkeypatch):
    """
    Creates temporary CSV files for users and bookmarks so tests do not modify real data. 
    Monkeypatches the service paths
    """

    #create temp files
    temp_users = tempfile.NamedTemporaryFile(delete=False)
    temp_bookmarks = tempfile.NamedTemporaryFile(delete=False)

    #Write CSV headers
    with open (temp_users.name, "w", newline = "", encoding = "utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["user_email", "user_password", "user_tier"])

    with open(temp_bookmarks.name, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["user_email", "movie_id"])
    
    #monkeypatch service constants 
    monkeypatch.setattr(user_service, "USER_CSV_PATH", temp_users.name)
    monkeypatch.setattr(user_service, "BOOKMARK_CSV_PATH", temp_bookmarks.name)

    return temp_users.name, temp_bookmarks.name


@pytest.fixture
def create_test_user(temp_user_and_bookmark_files):
    """
    Creates a test user in the temp CSV.
    """
    user_service.create_user(
        email="test@example.com",
        password="password123",
        tier="Snail"
    )
    return "test@example.com"

#Bookmark Tests

def test_add_bookmark(create_test_user):
    """Test adding a new bookmark."""
    result = user_service.add_bookmark("test@example.com", "MOV001")
    assert result is True

    bookmarks = user_service.get_user_bookmarks("test@example.com")
    assert bookmarks == ["MOV001"]


def test_add_duplicate_bookmark(create_test_user):
    """Adding the same movie again should fail."""
    user_service.add_bookmark("test@example.com", "MOV001")
    result = user_service.add_bookmark("test@example.com", "MOV001")

    assert result is False  # duplicate not added

    bookmarks = user_service.get_user_bookmarks("test@example.com")
    assert bookmarks == ["MOV001"]


def test_remove_bookmark(create_test_user):
    """Removing a bookmark should work."""
    user_service.add_bookmark("test@example.com", "MOV001")

    result = user_service.remove_bookmark("test@example.com", "MOV001")
    assert result is True

    bookmarks = user_service.get_user_bookmarks("test@example.com")
    assert bookmarks == []


def test_remove_missing_bookmark(create_test_user):
    """Removing a non-existent bookmark should return False."""
    result = user_service.remove_bookmark("test@example.com", "MOV999")
    assert result is False


def test_is_bookmarked(create_test_user):
    """Check if bookmark exists."""
    user_service.add_bookmark("test@example.com", "MOV001")

    assert user_service.is_bookmarked("test@example.com", "MOV001") is True
    assert user_service.is_bookmarked("test@example.com", "MOV999") is False


def test_get_bookmarks(create_test_user):
    """Should return all bookmarked movie IDs."""
    user_service.add_bookmark("test@example.com", "MOV001")
    user_service.add_bookmark("test@example.com", "MOV002")

    bookmarks = user_service.get_user_bookmarks("test@example.com")
    assert set(bookmarks) == {"MOV001", "MOV002"}