# backend/services/admin_service.py
"""Service layer for admin management - handles all business logic."""
import csv
import os
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from backend.models.admin_model import Admin

# Path configuration
ADMIN_CSV_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../database/admins/admin_information.csv")
)

# In-memory token storage (consider Redis or database for production)
admin_tokens: Dict[str, tuple[str, datetime]] = {}  # token -> (email, expiry)
TOKEN_EXPIRY_HOURS = 24

# ==================== CSV Operations ====================

def ensure_admin_csv_exists():
    """Ensure the directory and CSV file exist, and create headers if missing."""
    os.makedirs(os.path.dirname(ADMIN_CSV_PATH), exist_ok=True)
    if not os.path.exists(ADMIN_CSV_PATH):
        with open(ADMIN_CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["admin_email", "admin_password"])


def read_admins() -> Dict[str, str]:
    """
    Read all admins from CSV.
    Returns: Dict[email -> password_hash]
    """
    admins = {}
    if not os.path.exists(ADMIN_CSV_PATH):
        return admins
    
    with open(ADMIN_CSV_PATH, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # Skip header row
        for row in reader:
            if len(row) >= 2:
                email = row[0].lower()
                password_hash = row[1]
                admins[email] = password_hash
    
    return admins


def save_admin(email: str, password_hash: str):
    """Save a new admin to the CSV file."""
    ensure_admin_csv_exists()
    with open(ADMIN_CSV_PATH, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([email.lower(), password_hash])


def get_admin_by_email(email: str) -> Optional[Admin]:
    """Retrieve an admin by email, returns None if not found."""
    admins = read_admins()
    password_hash = admins.get(email.lower())
    
    if not password_hash:
        return None
    
    return Admin(email.lower(), password_hash)


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


# ==================== Token Operations ====================

def _generate_token() -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)


def generate_admin_token(email: str) -> str:
    """
    Generate an authentication token for an admin.
    
    Args:
        email: Admin email address
        
    Returns:
        Authentication token string
    """
    token = _generate_token()
    expiry = datetime.now() + timedelta(hours=TOKEN_EXPIRY_HOURS)
    admin_tokens[token] = (email.lower(), expiry)
    return token


def verify_admin_token(token: str) -> Optional[Admin]:
    """
    Verify admin token and return admin if valid.
    
    Args:
        token: Authentication token
        
    Returns:
        Admin object if token is valid, None otherwise
    """
    if token not in admin_tokens:
        return None
    
    email, expiry = admin_tokens[token]
    
    # Check if token is expired
    if datetime.now() > expiry:
        del admin_tokens[token]  # Clean up expired token
        return None
    
    return get_admin_by_email(email)


def revoke_token(token: str) -> bool:
    """
    Revoke an admin token (for logout).
    
    Args:
        token: Authentication token to revoke
        
    Returns:
        True if token was revoked, False if token didn't exist
    """
    if token in admin_tokens:
        del admin_tokens[token]
        return True
    return False


def cleanup_expired_tokens():
    """Remove all expired tokens from memory."""
    now = datetime.now()
    expired_tokens = [
        token for token, (_, expiry) in admin_tokens.items()
        if now > expiry
    ]
    for token in expired_tokens:
        del admin_tokens[token]


# ==================== Business Logic ====================

def create_admin(email: str, password: str) -> tuple[Admin, str]:
    """
    Create a new admin account and generate authentication token.
    
    Args:
        email: Admin email address
        password: Admin password (will be hashed)
        
    Returns:
        Tuple of (Admin object, authentication token)
        
    Raises:
        ValueError: If admin already exists
    """
    existing_admin = get_admin_by_email(email)
    if existing_admin:
        raise ValueError("Admin already exists")
    
    password_hash = hash_password(password)
    save_admin(email, password_hash)
    
    admin = Admin(email.lower(), password_hash)
    token = generate_admin_token(email)
    
    return admin, token


def authenticate_admin(email: str, password: str) -> tuple[Admin, str]:
    """
    Authenticate an admin with email and password, and generate token.
    
    Args:
        email: Admin email address
        password: Admin password
        
    Returns:
        Tuple of (Admin object, authentication token)
        
    Raises:
        ValueError: If credentials are invalid
    """
    admin = get_admin_by_email(email)
    
    if not admin:
        raise ValueError("Invalid credentials")
    
    if not verify_password(password, admin.password_hash):
        raise ValueError("Invalid credentials")
    
    token = generate_admin_token(email)
    return admin, token


def admin_exists(email: str) -> bool:
    """Check if an admin exists by email."""
    return get_admin_by_email(email) is not None


def get_all_admins() -> list[Admin]:
    """Get all admins."""
    admins_data = read_admins()
    return [
        Admin(email, password_hash)
        for email, password_hash in admins_data.items()
    ]


def delete_admin(email: str) -> bool:
    """
    Delete an admin by email and revoke all their tokens.
    
    Args:
        email: Admin email address
        
    Returns:
        True if admin was deleted, False if admin not found
    """
    admins = read_admins()
    email_lower = email.lower()
    
    if email_lower not in admins:
        return False
    
    # Revoke all tokens for this admin
    tokens_to_revoke = [
        token for token, (token_email, _) in admin_tokens.items()
        if token_email == email_lower
    ]
    for token in tokens_to_revoke:
        del admin_tokens[token]
    
    # Remove from CSV
    del admins[email_lower]
    
    ensure_admin_csv_exists()
    with open(ADMIN_CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["admin_email", "admin_password"])
        for admin_email, password_hash in admins.items():
            writer.writerow([admin_email, password_hash])
    
    return True
