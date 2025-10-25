import json
import hashlib
from datetime import datetime, date
from pathlib import Path
from abc import ABC, abstractmethod
import uuid

# ==========================
# User Base Class
# ==========================
class User(ABC):
    def __init__(
        self,
        user_id: str,
        username: str,
        date_of_birth: str,
        email: str,
        password: str = None,
        password_hash: str = None,
        role: str = "",
        date_created: str = None,
        last_login: str = None,
    ):
        self.user_id = user_id or str(uuid.uuid4())
        self.username = username
        self.date_of_birth = date_of_birth
        self.email = email
        self.role = role
        self.date_created = date_created or datetime.now().strftime("%Y-%m-%d")
        self.last_login = last_login

        if password_hash:
            self.password_hash = password_hash
        elif password:
            self.password_hash = self._hash_password(password)
        else:
            raise ValueError("Either password or password_hash must be provided")

    def _hash_password(self, password: str) -> str:
        """Hash the password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str) -> bool:
        """Check if the provided password matches the stored hash."""
        return self.password_hash == self._hash_password(password)

    @abstractmethod
    def get_role(self) -> str:
        """Abstract method to be implemented by subclasses."""
        pass

    def to_dict(self) -> dict:
        """Convert user to JSON-compatible dictionary."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "date_of_birth": self.date_of_birth,
            "email": self.email,
            "password_hash": self.password_hash,
            "role": self.get_role(),
            "date_created": self.date_created,
            "last_login": self.last_login,
        }


# ==========================
# Admin Class
# ==========================
class Admin(User):
    def __init__(self, username, password=None, password_hash=None, email="", date_of_birth="", date_created=None, last_login=None):
        super().__init__(
            user_id=str(uuid.uuid4()),
            username=username,
            date_of_birth=date_of_birth,
            email=email,
            password=password,
            password_hash=password_hash,
            role="Admin",
            date_created=date_created,
            last_login=last_login
        )

    def get_role(self) -> str:
        return "Admin"

    def add_movie(self):
        return "Movie added"

    def remove_movie(self):
        return "Movie removed"

    def edit_movie(self):
        return "Movie edited"

    def remove_review(self):
        return "Review removed"

    def remove_user(self):
        return "User removed"

    def apply_penalty(self):
        return "User penalized"


# ==========================
# MovieGoer Class
# ==========================
class MovieGoer(User):
    def __init__(self, username, password=None, password_hash=None, email="", date_of_birth="", user_rank="Slime", date_created=None, last_login=None, bookmarks= None):
        super().__init__(
            user_id=str(uuid.uuid4()),
            username=username,
            date_of_birth=date_of_birth,
            email=email,
            password=password,
            password_hash=password_hash,
            role="MovieGoer",
            date_created=date_created,
            last_login=last_login
        )
        self.user_rank = user_rank
        self.bookmarks = bookmarks or [] #new attr.

    def get_role(self) -> str:
        return "MovieGoer"

    def set_user_rank(self, new_rank: str):
        valid_ranks = ["Slime", "Banana", "Banana Bunch", "Banana Tree"]
        if new_rank not in valid_ranks:
            print(f"Invalid rank. Choose one of: {', '.join(valid_ranks)}")
            return False
        self.user_rank = new_rank
        print(f"{self.username}'s rank updated to {self.user_rank}.")
        return True

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["user_rank"] = self.user_rank
        data["bookmarks"] = self.bookmarks
        return data

    def review_movie(self):
        return "Movie reviewed"

    def rate_movie(self):
        return "Movie rated"

#bookmark methods
    def add_bookmark(self, movie_title: str):
        if movie_title in self.bookmarks: 
            print(f" '{movie_title}' is already bookmarked.")
            return False
        self.bookmarks.append(movie_title)
        print(f"'{movie_title}' has been added to your bookmarked movies.")
        return True
    
    def remove_bookmark(self, movie_title: str):
        if movie_title not in self.bookmarks:
            print(f"'{movie_title}' not found in bookmarks")
            return False
        self.bookmarks.remove(movie_title)
        print(f" '{movie_title}' removed from bookmarked movies.")
        return True
    
    def view_bookmarks(self):
        if not self.bookmarks:
            print(" No bookmarks yet.")
            return []
        print ("\n Bookmarked Movies:")
        for i, movie in enumerate(self.bookmarks, start = 1):
            print(f"{i}. {movie}")
        return self.bookmarks


# ==========================
# AuthService Class
# ==========================
class AuthService:
    def __init__(self, filepath="users.json"):
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            self.filepath.write_text("[]")

    def _load_users(self) -> list:
        with open(self.filepath, "r") as f:
            return json.load(f)

    def _save_users(self, users: list):
        with open(self.filepath, "w") as f:
            json.dump(users, f, indent=4)

    def register_user(self, user: User) -> bool:
        users = self._load_users()
        if any(u["username"] == user.username for u in users):
            print("Username already exists.")
            return False
        users.append(user.to_dict())
        self._save_users(users)
        print(f"User '{user.username}' registered as {user.get_role()}.")
        return True

    def login(self, username: str, password: str) -> User | None:
        users = self._load_users()
        for u in users:
            if u["username"] == username:
                if u["role"] == "Admin":
                    user = Admin(
                        username=u["username"],
                        email=u["email"],
                        date_of_birth=u["date_of_birth"],
                        password_hash=u["password_hash"],
                        date_created=u.get("date_created"),
                        last_login=u.get("last_login")
                    )
                else:
                    user = MovieGoer(
                        username=u["username"],
                        email=u["email"],
                        date_of_birth=u["date_of_birth"],
                        password_hash=u["password_hash"],
                        user_rank=u.get("user_rank", "Slime"),
                        date_created=u.get("date_created"),
                        last_login=u.get("last_login"),
                        bookmarks = u.get("bookmarks", [])
                    )

                if user.verify_password(password):
                    user.last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    u["last_login"] = user.last_login
                    self._save_users(users)
                    print(f"Login successful: {username} ({u['role']})")
                    return user
                else:
                    print("Invalid password.")
                    return None
        print("User not found.")
        return None


# ==========================
# AccountManager Class
# ==========================
class AccountManager:
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
    def create_account(self, username: str, password: str, email: str, date_of_birth: str, role: str = "MovieGoer"):
        """Create a new user account and save it."""
        if role.lower() == "admin":
            user = Admin(
                username=username,
                password=password,
                email=email,
                date_of_birth=date_of_birth
            )
        else:
            user = MovieGoer(
                username=username,
                password=password,
                email=email,
                date_of_birth=date_of_birth
            )

        success = self.auth_service.register_user(user)
        if success:
            print(f"Account created for '{username}' as {role}.")
        else:
            print(f"Account creation failed — username '{username}' already exists.")
        return success

    def delete_account(self, username: str):
        """Delete a user account by username."""
        users = self.auth_service._load_users()
        updated_users = [u for u in users if u["username"] != username]

        if len(updated_users) == len(users):
            print(f"User '{username}' not found.")
            return False

        self.auth_service._save_users(updated_users)
        print(f"User '{username}' has been deleted.")
        return True

    def reset_password(self, username: str, new_password: str):
        """Reset a user's password to a new one."""
        users = self.auth_service._load_users()
        for u in users:
            if u["username"] == username:
                new_hash = hashlib.sha256(new_password.encode()).hexdigest()
                u["password_hash"] = new_hash
                self.auth_service._save_users(users)
                print(f"Password for '{username}' has been reset.")
                return True
        print(f"User '{username}' not found.")
        return False
