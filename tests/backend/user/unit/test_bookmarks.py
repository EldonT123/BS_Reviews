"""Test for movie bookmark functionality in user_service."""
import csv
import tempfile
import pytest

# important service youre testing
from backend.services import user_service


@pytest.fixture
# Fixture/ Environment Setup

def temp_user_and_bookmark_files(monkeypatch):
    """
    Creates temporary CSV files for users and bookmarks so tests do not modify real data. 
    Monkeypatches the service paths
    """
    # Create temp files
    temp_users = tempfile.NamedTemporaryFile(delete=False)
    temp_bookmarks = tempfile.NamedTemporaryFile(delete=False)

    # Write CSV headers
    with open (temp_users.name, "w", newline = "", encoding = "utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["user_email", "user_username", "user_password", "user_tier"])

    with open(temp_bookmarks.name, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["user_email", "movie_title"])

    # Monkeypatch service constants
    monkeypatch.setattr(user_service, "USER_CSV_PATH", temp_users.name)
    monkeypatch.setattr(user_service, "BOOKMARK_CSV_PATH", temp_bookmarks.name)

    return temp_users.name, temp_bookmarks.name


@pytest.fixture
# Fixture/ preparation


def create_test_user(temp_user_and_bookmark_files):
    """Fixture: Creates a test user in the temp CSV."""
    user_service.create_user(
        email="test@example.com",
        username="testuser",
        password="password123",
        tier="Snail"
    )
    return "test@example.com"

# Bookmark Tests
# Functional test (behaviour end to end) and 
# File I/O integration test (writes/reads temp CSV files)


def test_add_bookmark(create_test_user):
    """Unit test - Positive path:
    Test adding a new bookmark."""
    result = user_service.add_bookmark("test@example.com", "Avengers Endgame")
    assert result is True

    bookmarks = user_service.get_user_bookmarks("test@example.com")
    assert bookmarks == ["Avengers Endgame"]

# Unit test (Validates logic to prevent duplicates), 
# Functional test (verifies expected behaviour), and 
# File I/O integration test


def test_add_duplicate_bookmark(create_test_user):
    """Unit test - Edge case:
    Adding the same movie again should fail."""
    user_service.add_bookmark("test@example.com", "Avengers Endgame")
    result = user_service.add_bookmark("test@example.com", "Avengers Endgame")

    assert result is False  # duplicate not added

    bookmarks = user_service.get_user_bookmarks("test@example.com")
    assert bookmarks == ["Avengers Endgame"]

# Functional test and File I/O integration test

def test_remove_bookmark(create_test_user):
    """Unit test - Positive path:
    Removing a bookmark should work."""
    user_service.add_bookmark("test@example.com", "Avengers Endgame")

    result = user_service.remove_bookmark(
        "test@example.com", "Avengers Endgame")
    assert result is True

    bookmarks = user_service.get_user_bookmarks("test@example.com")
    assert bookmarks == []

# Unit test (tests how logic handles non-existent items),
# Functional test (ensure correct boolean return behaviour)

def test_remove_missing_bookmark(create_test_user):
    """Unit test - Edge case:
    Removing a non-existent bookmark should return False."""
    result = user_service.remove_bookmark(
        "test@example.com", "Thor Ragnarok")
    assert result is False

# Unit test (logic checks boolean result),
# Functional Test (verifies lookup behaviour)

def test_is_bookmarked(create_test_user):
    """Unit test - Positive/Edge check:
    Check if bookmark exists."""
    user_service.add_bookmark("test@example.com", "Avengers Endgame")

    assert user_service.is_bookmarked(
        "test@example.com", "Avengers Endgame") is True
    assert user_service.is_bookmarked(
        "test@example.com", "Thor Ragnarok") is False

# Functional tests (returns full lists of bookmarks)
# File I/O integration test

def test_get_bookmarks(create_test_user):
    """Unit test/ Positive path:
    Should return all bookmarked movie titles."""
    user_service.add_bookmark("test@example.com", "Avengers Endgame")
    user_service.add_bookmark("test@example.com", "Forrest Gump")

    bookmarks = user_service.get_user_bookmarks("test@example.com")
    assert set(bookmarks) == {"Avengers Endgame", "Forrest Gump"}
