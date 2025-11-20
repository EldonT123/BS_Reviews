# backend/models/user_model.py

class User:

    """Represents a user with tiered permissions."""

    # Tier constants
    TIER_SNAIL = "snail"
    TIER_SLUG = "slug"
    TIER_BANANA_SLUG = "banana_slug"

    def __init__(self, email: str, password_hash: str, tier: str = TIER_SNAIL):
        self.email = email
        self.password_hash = password_hash
        self.tier = tier

    # ==================== Tier Checks ====================

    def is_snail(self) -> bool:
        """Check if user is Snail tier (basic browsing only)."""
        return self.tier == self.TIER_SNAIL

    def is_slug(self) -> bool:
        """Check if user is Slug tier (can write reviews)."""
        return self.tier == self.TIER_SLUG

    def is_banana_slug(self) -> bool:
        """Check if user is Banana Slug tier (VIP features)."""
        return self.tier == self.TIER_BANANA_SLUG

    # ==================== Permission Checks ====================

    def can_browse(self) -> bool:
        """Everyone can browse movies and reviews."""
        return True

    def can_write_reviews(self) -> bool:
        """Only Slug tier and above can write reviews."""
        return self.tier in [self.TIER_SLUG, self.TIER_BANANA_SLUG]

    def can_rate_movies(self) -> bool:
        """Only Slug tier and above can rate movies."""
        return self.tier in [self.TIER_SLUG, self.TIER_BANANA_SLUG]

    def can_edit_own_reviews(self) -> bool:
        """Only Slug tier and above can edit their own reviews."""
        return self.tier in [self.TIER_SLUG, self.TIER_BANANA_SLUG]

    def has_priority_reviews(self) -> bool:
        """Banana Slugs get their reviews shown first."""
        return self.tier == self.TIER_BANANA_SLUG

    def get_tier_display_name(self) -> str:
        """Get user-friendly tier name."""
        tier_names = {
            self.TIER_SNAIL: "🐌 Snail",
            self.TIER_SLUG: "🐌 Slug",
            self.TIER_BANANA_SLUG: "🍌 Banana Slug",
        }
        return tier_names.get(self.tier, "Unknown")

    # ==================== Actions ====================

    def add_review(self, movie_name: str, rating: float, comment: str):
        """
        Allows Slug tier and above to post a review.
        Raises ValueError if user doesn't have permission.
        """
        if not self.can_write_reviews():
            raise ValueError(
                "Snail tier users cannot write reviews. "
                "Upgrade to Slug tier!"
            )

        from backend.services.review_service import add_review
        add_review(self.email, movie_name, rating, comment)

    def upgrade_tier(self, new_tier: str) -> bool:
        """Upgrade user to a new tier (admin function)."""
        valid_tiers = [self.TIER_SNAIL, self.TIER_SLUG, self.TIER_BANANA_SLUG]
        if new_tier not in valid_tiers:
            return False
        self.tier = new_tier
        return True

    # ==================== Utility ====================

    def to_dict(self) -> dict:
        """Convert user to dictionary for JSON responses."""
        return {
            "email": self.email,
            "tier": self.tier,
            "tier_display": self.get_tier_display_name(),
            "permissions": {
                "can_browse": self.can_browse(),
                "can_write_reviews": self.can_write_reviews(),
                "can_rate_movies": self.can_rate_movies(),
                "can_edit_own_reviews": self.can_edit_own_reviews(),
                "has_priority_reviews": self.has_priority_reviews()
            }
        }

    def __repr__(self):
        return f"User(email={self.email}, tier={self.tier})"
