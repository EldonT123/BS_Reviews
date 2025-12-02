# backend/services/user_service.py
"""Service layer for user management - handles all business logic."""
import csv
import os
import bcrypt
import secrets
from datetime import datetime, timedelta
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
# In-memory session storage (consider Redis or database for production)
user_sessions: Dict[str, tuple[str, datetime]] = {}  # token -> (email, expiry)
session_ids: Dict[str, str] = {}  # session_id -> token
SESSION_EXPIRY_HOURS = 24

# ==================== CSV Operations ====================


def ensure_user_csv_exists():
    """Ensure the directory and CSV file exist,"""
    """and create headers if missing."""
    os.makedirs(os.path.dirname(USER_CSV_PATH), exist_ok=True)
    if not os.path.exists(USER_CSV_PATH):
        with open(USER_CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                ["user_email", "username", "user_password", "user_tier"])


def ensure_bookmark_csv_exists():
    """Ensure the directory and CSV file exist,"""
    """and create headers if missing."""
    os.makedirs(os.path.dirname(BOOKMARK_CSV_PATH), exist_ok=True)
    if not os.path.exists(BOOKMARK_CSV_PATH):
        with open(BOOKMARK_CSV_PATH, "w", newline="",
                  encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["user_email", "movie_title"])


def read_users() -> Dict[str, tuple[str, str, str]]:
    """
    Read all users from CSV.
    Returns: Dict[email -> (username, password_hash, tier)]
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
                username = row[1]
                password_hash = row[2]
                tier = row[3] if len(row) >= 3 else User.TIER_SNAIL
                users[email] = (username, password_hash, tier)

    return users


def save_user(email: str, username: str,
              password_hash: str, tier: str = User.TIER_SNAIL):
    """Save a new user to the CSV file."""
    ensure_user_csv_exists()
    with open(USER_CSV_PATH, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([email.lower(), username, password_hash, tier])


def get_user_by_email(email: str) -> Optional[User]:
    """Retrieve a user by email, returns None if not found."""
    users = read_users()
    user_data = users.get(email)

    if not user_data:
        return None

    username, password_hash, tier = user_data
    return User(email.lower(), username, password_hash, tier)


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
    username, password_hash, _ = users[email_lower]
    users[email_lower] = (username, password_hash, new_tier)

    # Rewrite CSV
    ensure_user_csv_exists()
    with open(USER_CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            ["user_email", "username", "user_password", "user_tier"])
        for user_email, (username, pwd_hash, tier) in users.items():
            writer.writerow([user_email, username, pwd_hash, tier])

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


# ==================== Session Management ====================

def _generate_session_token() -> str:
    """Generate a secure random session token."""
    return secrets.token_urlsafe(32)


def _generate_session_id() -> str:
    """Generate a random short session ID (8 characters)."""
    return secrets.token_urlsafe(8)


def create_session(email: str) -> str:
    """
    Create a session token for a user.

    Args:
        email: User email address

    Returns:
        Session token string
    """
    token = _generate_session_token()
    expiry = datetime.now() + timedelta(hours=SESSION_EXPIRY_HOURS)
    user_sessions[token] = (email.lower(), expiry)
    return token


def create_session_id(email: str) -> str:
    """
    Create a random session ID for a user.

    This generates a short, random ID that's easier to type/copy
    than the full token.

    Args:
        email: User email address

    Returns:
        Random session ID string (8 characters)
    """
    token = create_session(email)
    session_id = _generate_session_id()

    # Ensure uniqueness (very unlikely to collide, but just in case)
    while session_id in session_ids:
        session_id = _generate_session_id()

    session_ids[session_id] = token
    return session_id


def verify_session(token: str) -> Optional[User]:
    """
    Verify session token and return user if valid.

    Args:
        token: Session token

    Returns:
        User object if session is valid, None otherwise
    """
    if token not in user_sessions:
        return None

    email, expiry = user_sessions[token]

    # Check if session is expired
    if datetime.now() > expiry:
        del user_sessions[token]  # Clean up expired session
        return None

    return get_user_by_email(email)


def verify_session_id(session_id: str) -> Optional[User]:
    """
    Verify session by ID instead of full token.

    Args:
        session_id: Short session ID

    Returns:
        User object if session is valid, None otherwise
    """
    if session_id not in session_ids:
        return None

    token = session_ids[session_id]
    return verify_session(token)


def revoke_session(token: str) -> bool:
    """
    Revoke a session token (for signout).

    Args:
        token: Session token to revoke

    Returns:
        True if session was revoked, False if session didn't exist
    """
    if token in user_sessions:
        del user_sessions[token]
        return True
    return False


def revoke_session_id(session_id: str) -> bool:
    """
    Revoke a session by ID.

    Args:
        session_id: Session ID to revoke

    Returns:
        True if session was revoked, False if session didn't exist
    """
    if session_id not in session_ids:
        return False

    token = session_ids[session_id]
    del session_ids[session_id]
    return revoke_session(token)


def revoke_all_user_sessions(email: str):
    """
    Revoke all session tokens for a specific user.

    Args:
        email: User email address
    """
    email_lower = email.lower()

    # Revoke all tokens
    tokens_to_revoke = [
        token for token, (token_email, _) in user_sessions.items()
        if token_email == email_lower
    ]
    for token in tokens_to_revoke:
        del user_sessions[token]

    # Revoke all session IDs pointing to those tokens
    session_ids_to_revoke = [
        sid for sid, token in session_ids.items()
        if token in tokens_to_revoke
    ]
    for sid in session_ids_to_revoke:
        del session_ids[sid]


def cleanup_expired_sessions():
    """Remove all expired sessions from memory."""
    now = datetime.now()
    expired_tokens = [
        token for token, (_, expiry) in user_sessions.items()
        if now > expiry
    ]

    # Clean up expired tokens
    for token in expired_tokens:
        del user_sessions[token]

    # Clean up session IDs pointing to expired tokens
    session_ids_to_remove = [
        sid for sid, token in session_ids.items()
        if token in expired_tokens
    ]
    for sid in session_ids_to_remove:
        del session_ids[sid]


# ==================== Business Logic ====================

def create_user(
        email: str,
        username: str,
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
    save_user(email, username, password_hash, tier)

    return User(email.lower(), username, password_hash, tier)


def authenticate_user(email: str, password: str) -> tuple[User, str]:
    """
    Authenticate a user with email and password, and create session.

    Args:
        email: User email
        password: User password

    Returns:
        Tuple of (User object, session ID)

    Raises:
        ValueError: If credentials are invalid
    """
    user = get_user_by_email(email)

    if not user:
        raise ValueError("Invalid credentials")

    if not verify_password(password, user.password_hash):
        raise ValueError("Invalid credentials")

    revoke_all_user_sessions(email)

    # Create session ID (random 8-character string)
    session_id = create_session_id(email)

    return user, session_id


def signout_user(session_id: str) -> bool:
    """
    Sign out a user by revoking their session ID.

    Args:
        session_id: Session ID to revoke

    Returns:
        True if signout was successful, False if session_id didn't exist
    """
    return revoke_session_id(session_id)


def user_exists(email: str) -> bool:
    """Check if a user exists by email."""
    return get_user_by_email(email) is not None


def get_all_users() -> list[User]:
    """Get all users."""
    users_data = read_users()
    return [
        User(email, username, password_hash, tier)
        for email, (username, password_hash, tier) in users_data.items()
    ]


def delete_user(email: str) -> bool:
    """
    Delete a user by email and revoke all their sessions.

    Args:
        email: User email address

    Returns:
        True if user was deleted, False if user not found
    """
    users = read_users()
    email_lower = email.lower()

    if email_lower not in users:
        return False

    # Revoke all sessions for this user
    revoke_all_user_sessions(email_lower)

    # Delete from CSV
    del users[email_lower]

    ensure_user_csv_exists()
    with open(USER_CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            ["user_email", "username", "user_password", "user_tier"])
        for user_email, (username, password_hash, tier) in users.items():
            writer.writerow([user_email, username, password_hash, tier])

    return True


def update_user_profile(
    current_email: str,
    new_email: str,
    new_username: Optional[str] = None,
    new_password: Optional[str] = None
) -> bool:

    users = read_users()
    current_email_lower = current_email.lower()

    if current_email_lower not in users:
        return False

    username, password_hash, tier = users[current_email_lower]

    # Update with new values or keep existing
    updated_username = new_username if new_username else username
    updated_password = hash_password(
        new_password) if new_password else password_hash
    new_email_lower = new_email.lower()

    # Delete old entry
    del users[current_email_lower]

    # Add updated entry with potentially new email
    users[new_email_lower] = (updated_username, updated_password, tier)

    # Rewrite CSV
    ensure_user_csv_exists()
    with open(USER_CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["user_email", "username",
                        "user_password", "user_tier"])
        for user_email, (username, pwd_hash, tier) in users.items():
            writer.writerow([user_email, username, pwd_hash, tier])

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
