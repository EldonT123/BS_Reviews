# backend/services/admin_service.py
"""Service layer for admin management - handles all business logic."""
import csv
import os
import bcrypt
from typing import Optional, Dict
from backend.models.admin_model import Admin

# Path configuration
ADMIN_CSV_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../database/admins/admin_information.csv")
)

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


# ==================== Business Logic ====================

def create_admin(email: str, password: str) -> Admin:
    """
    Create a new admin account.
    Raises ValueError if admin already exists.
    """
    existing_admin = get_admin_by_email(email)
    if existing_admin:
        raise ValueError("Admin already exists")
    
    password_hash = hash_password(password)
    save_admin(email, password_hash)
    
    return Admin(email.lower(), password_hash)


def authenticate_admin(email: str, password: str) -> Admin:
    """
    Authenticate an admin with email and password.
    Raises ValueError if credentials are invalid.
    """
    admin = get_admin_by_email(email)
    
    if not admin:
        raise ValueError("Invalid credentials")
    
    if not verify_password(password, admin.password_hash):
        raise ValueError("Invalid credentials")
    
    return admin


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
    Delete an admin by email.
    Returns True if admin was deleted, False if admin not found.
    """
    admins = read_admins()
    email_lower = email.lower()
    
    if email_lower not in admins:
        return False
    
    del admins[email_lower]
    
    ensure_admin_csv_exists()
    with open(ADMIN_CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["admin_email", "admin_password"])
        for admin_email, password_hash in admins.items():
            writer.writerow([admin_email, password_hash])
    
    return True
