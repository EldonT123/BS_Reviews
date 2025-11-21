# backend/services/settings_service.py
"""Service layer for user settings management."""
import csv
import os
import bcrypt
from typing import Optional, Dict
from backend.services import user_service

# Path configuration
USER_CSV_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../database/users/user_information.csv"
    )
)


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


# ==================== Settings Operations ====================

def change_email(
    current_email: str,
    new_email: str,
    current_password: str
) -> bool:
    """
    Change user's email address.

    Args:
        current_email: Current email address
        new_email: New email address
        current_password: Current password for verification

    Returns:
        True if email was changed successfully

    Raises:
        ValueError: If validation fails or user not found
    """
    # Verify current user exists and password is correct
    user = user_service.get_user_by_email(current_email)
    if not user:
        raise ValueError("User not found")

    if not verify_password(current_password, user.password_hash):
        raise ValueError("Invalid password")

    # Check if new email is already taken
    new_email_lower = new_email.lower()
    if user_service.user_exists(new_email_lower):
        raise ValueError("Email already in use")

    # Read all users
    users = user_service.read_users()
    current_email_lower = current_email.lower()

    if current_email_lower not in users:
        raise ValueError("User not found")

    # Get user data and remove old entry
    password_hash, tier = users[current_email_lower]
    del users[current_email_lower]

    # Add user with new email
    users[new_email_lower] = (password_hash, tier)

    # Rewrite CSV with updated email
    user_service.ensure_user_csv_exists()
    with open(USER_CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["user_email", "user_password", "user_tier"])
        for user_email, (pwd_hash, user_tier) in users.items():
            writer.writerow([user_email, pwd_hash, user_tier])

    return True


def change_password(
    email: str,
    current_password: str,
    new_password: str
) -> bool:
    """
    Change user's password.

    Args:
        email: User's email address
        current_password: Current password for verification
        new_password: New password to set

    Returns:
        True if password was changed successfully

    Raises:
        ValueError: If validation fails or user not found
    """
    # Verify user exists and current password is correct
    user = user_service.get_user_by_email(email)
    if not user:
        raise ValueError("User not found")

    if not verify_password(current_password, user.password_hash):
        raise ValueError("Current password is incorrect")

    # Validate new password (optional - add your own rules)
    if len(new_password) < 1:
        raise ValueError("New password cannot be empty")

    if new_password == current_password:
        raise ValueError(
            "New password must be different from current password"
        )

    # Hash new password
    new_password_hash = hash_password(new_password)

    # Read all users
    users = user_service.read_users()
    email_lower = email.lower()

    if email_lower not in users:
        raise ValueError("User not found")

    # Update password while keeping tier
    _, tier = users[email_lower]
    users[email_lower] = (new_password_hash, tier)

    # Rewrite CSV with updated password
    user_service.ensure_user_csv_exists()
    with open(USER_CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["user_email", "user_password", "user_tier"])
        for user_email, (password_hash, user_tier) in users.items():
            writer.writerow([user_email, password_hash, user_tier])

    return True


def get_user_settings(email: str) -> Optional[Dict]:
    """
    Get user's settings information (email and tier).

    Args:
        email: User's email address

    Returns:
        Dictionary with user settings or None if not found
    """
    user = user_service.get_user_by_email(email)

    if not user:
        return None

    return user.to_dict()