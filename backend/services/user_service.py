# backend/services/user_service.py
"""Service layer for user management - handles all business logic."""
import csv
import os
import bcrypt
from typing import Optional, Dict
from backend.models.user_model import User

# Path configuration
USER_CSV_PATH = os.path.abspath(
    os.path.join(
            os.path.dirname(__file__),
            "../../database/users/user_information.csv"
        )
)

# Path configuration for bookmarks
BOOKMARK_CSV_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../database/users/user_bookmarks.csv"
    )
)

# ==================== CSV Operations ====================


def ensure_user_csv_exists():
    """Ensure the directory and CSV file exist,"""
    """and create headers if missing."""
    os.makedirs(os.path.dirname(USER_CSV_PATH), exist_ok=True)
    if not os.path.exists(USER_CSV_PATH):
        with open(USER_CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["user_email", "user_password", "user_tier"])


def ensure_bookmark_csv_exists():
    """Ensure the directory and CSV file exist,"""
    """and create headers if missing."""
    os.makedirs(os.path.dirname(BOOKMARK_CSV_PATH), exist_ok=True)
    if not os.path.exists(BOOKMARK_CSV_PATH):
        with open(BOOKMARK_CSV_PATH, "w", newline="",
                  encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["user_email", "movie_title"])


def read_users() -> Dict[str, tuple[str, str]]:
    """
    Read all users from CSV.
    Returns: Dict[email -> (password_hash, tier)]
    """
    users = {}
    if not os.path.exists(USER_CSV_PATH):
        return users

    with open(USER_CSV_PATH, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # Skip header row
        for row in reader:
            if len(row) >= 2:
                email = row[0].lower()
                password_hash = row[1]
                tier = row[2] if len(row) >= 3 else User.TIER_SNAIL
                users[email] = (password_hash, tier)

    return users


def save_user(email: str, password_hash: str, tier: str = User.TIER_SNAIL):
    """Save a new user to the CSV file."""
    ensure_user_csv_exists()
    with open(USER_CSV_PATH, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([email.lower(), password_hash, tier])


def get_user_by_email(email: str) -> Optional[User]:
    """Retrieve a user by email, returns None if not found."""
    users = read_users()
    user_data = users.get(email.lower())

    if not user_data:
        return None

    password_hash, tier = user_data
    return User(email.lower(), password_hash, tier)


def update_user_tier(email: str, new_tier: str) -> bool:
    """
    Update a user's tier.
    Returns True if successful, False if user not found.
    """
    users = read_users()
    email_lower = email.lower()

    if email_lower not in users:
        return False

    # Update tier
    password_hash, _ = users[email_lower]
    users[email_lower] = (password_hash, new_tier)

    # Rewrite CSV
    ensure_user_csv_exists()
    with open(USER_CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["user_email", "user_password", "user_tier"])
        for user_email, (pwd_hash, tier) in users.items():
            writer.writerow([user_email, pwd_hash, tier])

    return True


# ==================== Password Operations ====================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    truncated_password = password[:72]
    password_bytes = truncated_password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash."""
    password_bytes = plain_password[:72].encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hash_bytes)


# ==================== Business Logic ====================

def create_user(
        email: str,
        password: str,
        tier: str = User.TIER_SNAIL
        ) -> User:
    """
    Create a new user account.
    Raises ValueError if user already exists.
    """
    existing_user = get_user_by_email(email)
    if existing_user:
        raise ValueError("User already exists")

    password_hash = hash_password(password)
    save_user(email, password_hash, tier)

    return User(email.lower(), password_hash, tier)


def authenticate_user(email: str, password: str) -> User:
    """
    Authenticate a user with email and password.
    Raises ValueError if credentials are invalid.
    """
    user = get_user_by_email(email)

    if not user:
        raise ValueError("Invalid credentials")

    if not verify_password(password, user.password_hash):
        raise ValueError("Invalid credentials")

    return user


def user_exists(email: str) -> bool:
    """Check if a user exists by email."""
    return get_user_by_email(email) is not None


def get_all_users() -> list[User]:
    """Get all users."""
    users_data = read_users()
    return [
        User(email, password_hash, tier)
        for email, (password_hash, tier) in users_data.items()
    ]


def delete_user(email: str) -> bool:
    """
    Delete a user by email.
    Returns True if user was deleted, False if user not found.
    """
    users = read_users()
    email_lower = email.lower()

    if email_lower not in users:
        return False

    del users[email_lower]

    ensure_user_csv_exists()
    with open(USER_CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["user_email", "user_password", "user_tier"])
        for user_email, (password_hash, tier) in users.items():
            writer.writerow([user_email, password_hash, tier])

    return True

# ==================== Bookmark Operations ====================
# Retrieve bookmarks


def get_user_bookmarks(email: str) -> list[str]:
    """Return list of movie IDs bookmarked by a user."""
    """Bookmarks stored in separate CSV file"""
    ensure_bookmark_csv_exists()
    bookmarks = []

    with open(BOOKMARK_CSV_PATH, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # Skip header

        # Collect movie_ids belonging to the user
        for row in reader:
            if len(row) >= 2 and row[0].lower() == email.lower():
                bookmarks.append(row[1])

    return bookmarks

# Add a bookmark


def add_bookmark(email: str, movie_title: str) -> bool:
    """Add movie to users list of bookmarks
    Returns True: successfully added
            False: Movie was already bookmarked
    """
    ensure_bookmark_csv_exists()

    # Prevent duplicates
    existing = get_user_bookmarks(email)
    if movie_title in existing:
        return False  # already bookmarked

    # Append new bookmark
    with open(BOOKMARK_CSV_PATH, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([email.lower(), movie_title])

    return True

# Remove a bookmark


def remove_bookmark(email: str, movie_title: str) -> bool:
    """
    Remove movie from user's bookmarked list
    Returns True = bookmark was removed
            False = bookmark did not exist
    """
    ensure_bookmark_csv_exists()
    removed = False
    updated_rows = []

    # Read all rows, skip the one being removed
    with open(BOOKMARK_CSV_PATH, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # skip header

        for row in reader:
            if row[0].lower() == email.lower() and row[1] == movie_title:
                removed = True  # Found bookmark to remove
                continue        # Skip adding it to the new list
            updated_rows.append(row)

    # Rewrite the CSV without the deleted row
    with open(BOOKMARK_CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["user_email", "movie_title"])
        writer.writerow(updated_rows)

    return removed


def is_bookmarked(email: str, movie_title: str) -> bool:
    """ Return True if the movie_id is already bookmarked by the user"""
    return movie_title in get_user_bookmarks(email)
