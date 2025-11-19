# backend/models/admin_model.py

class Admin:
    """Represents an admin with special admin privileges."""

    def __init__(self, email: str, password_hash: str):
        self.email = email
        self.password_hash = password_hash

    # ==================== Permission Checks ====================

    def can_manage_users(self) -> bool:
        """Admins can manage all users."""
        return True

    def can_upgrade_tiers(self) -> bool:
        """Admins can upgrade user tiers."""
        return True

    def can_delete_users(self) -> bool:
        """Admins can delete users."""
        return True

    def can_view_all_users(self) -> bool:
        """Admins can view all users."""
        return True

    def can_manage_movies(self) -> bool:
        """Admins can add/edit/delete movies."""
        return True

    def can_moderate_reviews(self) -> bool:
        """Admins can delete or edit any review."""
        return True

    # ==================== Actions ====================

    def upgrade_user_tier(self, user_email: str, new_tier: str) -> bool:
        """
        Upgrade a user's tier.
        Returns True if successful, False otherwise.
        """
        from backend.services.user_service import update_user_tier
        return update_user_tier(user_email, new_tier)

    def delete_user(self, user_email: str) -> bool:
        """
        Delete a user account.
        Returns True if successful, False otherwise.
        """
        from backend.services.user_service import delete_user
        return delete_user(user_email)

    def get_all_users(self) -> list:
        """Get all users in the system."""
        from backend.services.user_service import get_all_users
        return get_all_users()

    # ==================== Utility ====================

    def to_dict(self) -> dict:
        """Convert admin to dictionary for JSON responses."""
        return {
            "email": self.email,
            "role": "admin",
            "permissions": {
                "can_manage_users": self.can_manage_users(),
                "can_upgrade_tiers": self.can_upgrade_tiers(),
                "can_delete_users": self.can_delete_users(),
                "can_view_all_users": self.can_view_all_users(),
                "can_manage_movies": self.can_manage_movies(),
                "can_moderate_reviews": self.can_moderate_reviews()
            }
        }

    def __repr__(self):
        return f"Admin(email={self.email})"
