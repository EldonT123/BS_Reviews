from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
import csv
import os
import bcrypt

router = APIRouter()

# Safer path resolution (handles relative paths properly)
USER_CSV_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../database/users/user_information.csv")
)

class UserAuth(BaseModel):
    email: EmailStr
    password: str


def ensure_user_csv_exists():
    """Ensure the directory and CSV file exist, and create headers if missing."""
    os.makedirs(os.path.dirname(USER_CSV_PATH), exist_ok=True)
    if not os.path.exists(USER_CSV_PATH):
        with open(USER_CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["user_email", "user_password"])  # Add headers


def read_users():
    users = {}
    if not os.path.exists(USER_CSV_PATH):
        return users
    with open(USER_CSV_PATH, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # Skip header row
        for row in reader:
            if len(row) >= 2:
                users[row[0].lower()] = row[1]
    return users

def append_user(email: str, hashed_password: str):
    with open(USER_CSV_PATH, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([email.lower(), hashed_password])

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash."""
    # Encode the password to bytes (bcrypt requires bytes)
    password_bytes = plain_password[:72].encode('utf-8')
    # Encode the stored hash to bytes
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hash_bytes)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    # Truncate to 72 bytes (bcrypt's limit)
    truncated_password = password[:72]
    # Encode to bytes
    password_bytes = truncated_password.encode('utf-8')
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Return as string for storage
    return hashed.decode('utf-8')

@router.post("/signup")
async def signup(user: UserAuth):
    users = read_users()
    if user.email.lower() in users:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    
    # Hash the plain password before storing
    hashed_password = get_password_hash(user.password)
    append_user(user.email, hashed_password)
    return {"message": "Signup successful"}

@router.post("/login")
async def login(user: UserAuth):
    users = read_users()
    hashed_password = users.get(user.email.lower())
    if not hashed_password or not verify_password(user.password, hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    return {"message": "Login successful"}