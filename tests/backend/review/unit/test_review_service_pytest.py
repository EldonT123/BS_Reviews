# tests/test_review_service.py
"""Unit tests for review service with proper mocking."""
import pytest
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime
from backend.services import review_service
from backend.models.user_model import User


# ==================== Fixtures ====================

@pytest.fixture
def sample_reviews():
    """Fixture- Sample review data for testing."""
    return [
        {
            "Date of Review": "2024-01-15",
            "User": "alice@example.com",
            "Usefulness Vote": "10",
            "Total Votes": "12",
            "User's Rating out of 10": "8.5",
            "Review Title": "Great movie!",
            "Review": "Really enjoyed this film."
        },
        {
            "Date of Review": "2024-01-16",
            "User": "bob@example.com",
            "Usefulness Vote": "5",
            "Total Votes": "8",
            "User's Rating out of 10": "7.0",
            "Review Title": "Pretty good",
            "Review": "Solid entertainment."
        },
        {
            "Date of Review": "2024-01-17",
            "User": "charlie@example.com",
            "Usefulness Vote": "0",
            "Total Votes": "0",
            "User's Rating out of 10": "9.0",
            "Review Title": "",
            "Review": ""  # Rating only, no comment
        }
    ]


@pytest.fixture
def banana_slug_user():
    """Fixture - Create a Banana Slug tier user."""
    return User(
        "vip@example.com",
        "hashed_password",
        User.TIER_BANANA_SLUG
    )


@pytest.fixture
def slug_user():
    """Fixture - Create a Slug tier user."""
    return User(
        "regular@example.com",
        "hashed_password",
        User.TIER_SLUG
    )


@pytest.fixture
def snail_user():
    """Fixture - Create a Snail tier user."""
    return User(
        "viewer@example.com",
        "hashed_password",
        User.TIER_SNAIL
    )


# ==================== Read Operations Tests ====================
# All functional unit tests

class TestReadReviews:
    """Tests for reading reviews from CSV."""

    @patch('backend.services.review_service.os.path.exists')
    @patch('backend.services.review_service.file_service.get_movie_folder')
    def test_read_reviews_no_file(self, mock_get_folder, mock_exists):
        """Functional test: Should return empty list if review file doesn't exist."""
        mock_get_folder.return_value = "/fake/path/movie"
        mock_exists.return_value = False

        result = review_service.read_reviews("Test Movie")

        assert result == []
        mock_exists.assert_called_once()

    @patch('backend.services.review_service.os.path.exists')
    @patch('backend.services.review_service.file_service.get_movie_folder')
    @patch('builtins.open', new_callable=mock_open, read_data="Date of Review,User,Usefulness Vote,Total Votes,User's Rating out of 10,Review Title,Review\n2024-01-15,alice@example.com,10,12,8.5,Great!,Love it\n")
    def test_read_reviews_success(self, mock_file, mock_get_folder, mock_exists):
        """Functional test: Should successfully read reviews from CSV."""
        mock_get_folder.return_value = "/fake/path/movie"
        mock_exists.return_value = True

        result = review_service.read_reviews("Test Movie")

        assert len(result) == 1
        assert result[0]["User"] == "alice@example.com"
        assert result[0]["User's Rating out of 10"] == "8.5"

    @patch('backend.services.review_service.read_reviews')
    def test_get_review_by_user_found(self, mock_read, sample_reviews):
        """Functional test: Should find a specific user's review."""
        mock_read.return_value = sample_reviews

        result = review_service.get_review_by_user("Test Movie", "alice@example.com")

        assert result is not None
        assert result["User"] == "alice@example.com"
        assert result["Review Title"] == "Great movie!"

    @patch('backend.services.review_service.read_reviews')
    def test_get_review_by_user_not_found(self, mock_read, sample_reviews):
        """Functional test: Should return None if user hasn't reviewed."""
        mock_read.return_value = sample_reviews

        result = review_service.get_review_by_user("Test Movie", "nobody@example.com")

        assert result is None

    @patch('backend.services.review_service.read_reviews')
    def test_get_review_by_user_case_insensitive(self, mock_read, sample_reviews):
        """Functional test: Should match user email case-insensitively."""
        mock_read.return_value = sample_reviews

        result = review_service.get_review_by_user("Test Movie", "ALICE@EXAMPLE.COM")

        assert result is not None
        assert result["User"] == "alice@example.com"

    @patch('backend.services.review_service.get_review_by_user')
    def test_user_has_reviewed_true(self, mock_get):
        """Functional test: Should return True if user has reviewed."""
        mock_get.return_value = {"User": "alice@example.com"}

        result = review_service.user_has_reviewed("Test Movie", "alice@example.com")

        assert result is True

    @patch('backend.services.review_service.get_review_by_user')
    def test_user_has_reviewed_false(self, mock_get):
        """Functional test: Should return False if user hasn't reviewed."""
        mock_get.return_value = None

        result = review_service.user_has_reviewed("Test Movie", "alice@example.com")

        assert result is False


# ==================== Write Operations Tests ====================

class TestAddReview:
    """Tests for adding new reviews."""

    @patch('backend.services.review_service.os.path.exists')
    @patch('backend.services.review_service.os.path.getsize')
    @patch('backend.services.review_service.file_service.get_movie_folder')
    @patch('backend.services.review_service.file_service.create_movie_folder')
    @patch('builtins.open', new_callable=mock_open)
    def test_add_review_new_file(self, mock_file, mock_create, mock_get_folder, mock_getsize, mock_exists):
        """Functional test: Should create file with header when adding first review."""
        mock_get_folder.return_value = "/fake/path/movie"
        mock_exists.side_effect = [False, False]  # folder doesn't exist, file doesn't exist

        result = review_service.add_review(
            username="alice@example.com",
            movie_name="Test Movie",
            rating=8.5,
            comment="Great film!",
            review_title="Loved it"
        )

        assert result is True
        mock_create.assert_called_once()
        mock_file.assert_called_once()

    @patch('backend.services.review_service.os.path.exists')
    @patch('backend.services.review_service.os.path.getsize')
    @patch('backend.services.review_service.file_service.get_movie_folder')
    @patch('builtins.open', new_callable=mock_open)
    def test_add_review_existing_file(self, mock_file, mock_get_folder, mock_getsize, mock_exists):
        """Functional test: Should append to existing file without header."""
        mock_get_folder.return_value = "/fake/path/movie"
        mock_exists.return_value = True
        mock_getsize.return_value = 100  # File has content

        result = review_service.add_review(
            username="bob@example.com",
            movie_name="Test Movie",
            rating=7.0,
            comment="Pretty good"
        )

        assert result is True
        mock_file.assert_called_once()

    @patch('backend.services.review_service.os.path.exists')
    @patch('backend.services.review_service.os.path.getsize')
    @patch('backend.services.review_service.file_service.get_movie_folder')
    @patch('builtins.open', new_callable=mock_open)
    def test_add_review_rating_only(self, mock_file, mock_get_folder, mock_getsize, mock_exists):
        """Functional test: Should allow adding rating without comment."""
        mock_get_folder.return_value = "/fake/path/movie"
        mock_exists.return_value = True
        mock_getsize.return_value = 100  # File has content

        result = review_service.add_review(
            username="charlie@example.com",
            movie_name="Test Movie",
            rating=9.0,
            comment=""  # No comment, just rating
        )

        assert result is True

    @patch('backend.services.review_service.datetime')
    @patch('backend.services.review_service.os.path.exists')
    @patch('backend.services.review_service.os.path.getsize')
    @patch('backend.services.review_service.file_service.get_movie_folder')
    @patch('builtins.open', new_callable=mock_open)
    def test_add_review_auto_date(self, mock_file, mock_get_folder, mock_getsize, mock_exists, mock_datetime):
        """Functional test: Should automatically set current date if not provided."""
        mock_get_folder.return_value = "/fake/path/movie"
        mock_exists.return_value = True
        mock_getsize.return_value = 100  # File has content
        mock_datetime.now.return_value.strftime.return_value = "2024-01-20"

        result = review_service.add_review(
            username="alice@example.com",
            movie_name="Test Movie",
            rating=8.0,
            comment="Good"
        )

        assert result is True
        mock_datetime.now.assert_called_once()


class TestUpdateReview:
    """Tests for updating existing reviews."""

    @patch('backend.services.review_service.read_reviews')
    def test_update_review_no_reviews(self, mock_read):
        """Functional test: Should return False if no reviews exist."""
        mock_read.return_value = []

        result = review_service.update_review(
            username="alice@example.com",
            movie_name="Test Movie",
            rating=9.0,
            comment="Updated"
        )

        assert result is False

    @patch('backend.services.review_service.read_reviews')
    @patch('backend.services.review_service.file_service.get_movie_folder')
    @patch('builtins.open', new_callable=mock_open)
    def test_update_review_success(self, mock_file, mock_get_folder, mock_read, sample_reviews):
        """Functional test: Should successfully update existing review."""
        mock_read.return_value = sample_reviews.copy()
        mock_get_folder.return_value = "/fake/path/movie"

        result = review_service.update_review(
            username="alice@example.com",
            movie_name="Test Movie",
            rating=9.5,
            comment="Even better on rewatch!",
            review_title="Updated title"
        )

        assert result is True

    @patch('backend.services.review_service.read_reviews')
    def test_update_review_user_not_found(self, mock_read, sample_reviews):
        """Functional test: Should return False if user hasn't reviewed."""
        mock_read.return_value = sample_reviews

        result = review_service.update_review(
            username="nobody@example.com",
            movie_name="Test Movie",
            rating=5.0,
            comment="Nope"
        )

        assert result is False


class TestDeleteReview:
    """Tests for deleting reviews."""

    @patch('backend.services.review_service.read_reviews')
    def test_delete_review_no_reviews(self, mock_read):
        """Functional test: Should return False if no reviews exist."""
        mock_read.return_value = []

        result = review_service.delete_review("alice@example.com", "Test Movie")

        assert result is False

    @patch('backend.services.review_service.read_reviews')
    @patch('backend.services.review_service.file_service.get_movie_folder')
    @patch('builtins.open', new_callable=mock_open)
    def test_delete_review_success(self, mock_file, mock_get_folder, mock_read, sample_reviews):
        """Functional test: Should successfully delete user's review."""
        mock_read.return_value = sample_reviews.copy()
        mock_get_folder.return_value = "/fake/path/movie"

        result = review_service.delete_review("alice@example.com", "Test Movie")

        assert result is True

    @patch('backend.services.review_service.read_reviews')
    def test_delete_review_user_not_found(self, mock_read, sample_reviews):
        """Functional test: Should return False if user hasn't reviewed."""
        mock_read.return_value = sample_reviews

        result = review_service.delete_review("nobody@example.com", "Test Movie")

        assert result is False


# ==================== Calculations & Statistics Tests ====================

class TestCalculations:
    """Tests for rating calculations."""

    @patch('backend.services.review_service.read_reviews')
    def test_recalc_average_rating_no_reviews(self, mock_read):
        """Edge case, negative path
        Should return 0 if no reviews exist."""
        mock_read.return_value = []

        result = review_service.recalc_average_rating("Test Movie")

        assert result == 0.0

    @patch('backend.services.review_service.read_reviews')
    def test_recalc_average_rating_success(self, mock_read, sample_reviews):
        """Functional, positive path
        Should calculate correct average rating."""
        mock_read.return_value = sample_reviews

        result = review_service.recalc_average_rating("Test Movie")

        # (8.5 + 7.0 + 9.0) / 3 = 8.166...
        assert abs(result - 8.166666) < 0.001

    @patch('backend.services.review_service.read_reviews')
    def test_recalc_average_rating_invalid_ratings(self, mock_read):
        """Edge case, invalid input
        Should skip invalid ratings in calculation."""
        mock_read.return_value = [
            {"User's Rating out of 10": "8.5"},
            {"User's Rating out of 10": "invalid"},
            {"User's Rating out of 10": "7.0"},
            {"User's Rating out of 10": ""}
        ]

        result = review_service.recalc_average_rating("Test Movie")

        # Only 8.5 and 7.0 are valid: (8.5 + 7.0) / 2 = 7.75
        assert result == 7.75

    @patch('backend.services.review_service.read_reviews')
    @patch('backend.services.review_service.user_service.get_user_by_email')
    def test_get_review_stats(self, mock_get_user, mock_read, sample_reviews, banana_slug_user, slug_user):
        """Functional, positive path
        Should calculate comprehensive review statistics."""
        mock_read.return_value = sample_reviews

        def get_user_side_effect(email):
            if email == "alice@example.com":
                return banana_slug_user
            elif email == "bob@example.com":
                return slug_user
            return None

        mock_get_user.side_effect = get_user_side_effect

        result = review_service.get_review_stats("Test Movie")

        assert result["total_reviews"] == 3
        assert abs(result["average_rating"] - 8.17) < 0.01
        assert result["tier_breakdown"]["banana_slug"] == 1
        assert result["tier_breakdown"]["slug"] == 1
        assert result["tier_breakdown"]["unknown"] == 1

    @patch('backend.services.review_service.read_reviews')
    def test_get_review_stats_no_reviews(self, mock_read):
        """Edge case, no data
        Should return empty stats if no reviews exist."""
        mock_read.return_value = []

        result = review_service.get_review_stats("Test Movie")

        assert result["total_reviews"] == 0
        assert result["average_rating"] == 0.0
        assert result["tier_breakdown"]["banana_slug"] == 0


# ==================== Sorting & Filtering Tests ====================

class TestSorting:
    """Tests for review sorting by tier."""

    @patch('backend.services.review_service.user_service.get_user_by_email')
    def test_sort_reviews_by_tier(self, mock_get_user, sample_reviews, banana_slug_user, slug_user, snail_user):
        """Functional, positive path
        Should sort Banana Slug reviews first."""
        def get_user_side_effect(email):
            if email == "alice@example.com":
                return banana_slug_user
            elif email == "bob@example.com":
                return slug_user
            elif email == "charlie@example.com":
                return snail_user
            return None

        mock_get_user.side_effect = get_user_side_effect

        result = review_service.sort_reviews_by_tier(sample_reviews)

        assert len(result) == 3
        # Banana Slug should be first
        assert result[0]["User"] == "alice@example.com"
        assert result[0]["user_tier"] == User.TIER_BANANA_SLUG
        # Others can be in any order after
        assert result[1]["User"] in ["bob@example.com", "charlie@example.com"]

    @patch('backend.services.review_service.user_service.get_user_by_email')
    def test_sort_reviews_unknown_user(self, mock_get_user):
        """Edge case, missing user
        Should handle reviews from unknown/deleted users."""
        mock_get_user.return_value = None

        reviews = [{"User": "deleted@example.com"}]
        result = review_service.sort_reviews_by_tier(reviews)

        assert result[0]["user_tier"] == "unknown"
        assert result[0]["user_tier_display"] == "User"


# ==================== Validation Tests ====================

class TestValidation:
    """Tests for review validation."""

    @patch('backend.services.review_service.user_service.get_user_by_email')
    def test_validate_review_permission_snail(self, mock_get_user, snail_user):
        """Permission check, negative path
        Snail tier should not be able to write reviews."""
        mock_get_user.return_value = snail_user

        has_permission, error_msg = review_service.validate_review_permission("viewer@example.com")

        assert has_permission is False
        assert "cannot write reviews" in error_msg

    @patch('backend.services.review_service.user_service.get_user_by_email')
    def test_validate_review_permission_slug(self, mock_get_user, slug_user):
        """Permission check, positive path
        Slug tier should be able to write reviews."""
        mock_get_user.return_value = slug_user

        has_permission, error_msg = review_service.validate_review_permission("regular@example.com")

        assert has_permission is True
        assert error_msg is None

    @patch('backend.services.review_service.user_service.get_user_by_email')
    def test_validate_review_permission_banana_slug(self, mock_get_user, banana_slug_user):
        """Permission check, positive path
        Banana Slug tier should be able to write reviews."""
        mock_get_user.return_value = banana_slug_user

        has_permission, error_msg = review_service.validate_review_permission("vip@example.com")

        assert has_permission is True
        assert error_msg is None

    @patch('backend.services.review_service.user_service.get_user_by_email')
    def test_validate_review_permission_user_not_found(self, mock_get_user):
        """Permission check, negative path
        Should return False if user doesn't exist."""
        mock_get_user.return_value = None

        has_permission, error_msg = review_service.validate_review_permission("nobody@example.com")

        assert has_permission is False
        assert "not found" in error_msg

    def test_validate_rating_valid(self):
        """Input validation, positive path
        Should accept valid ratings."""
        is_valid, error_msg = review_service.validate_rating(5.0)
        assert is_valid is True
        assert error_msg is None

        is_valid, error_msg = review_service.validate_rating(0)
        assert is_valid is True

        is_valid, error_msg = review_service.validate_rating(10)
        assert is_valid is True

    def test_validate_rating_invalid(self):
        """Input validation, negative path
        Should reject ratings outside 0-10 range."""
        is_valid, error_msg = review_service.validate_rating(-1)
        assert is_valid is False
        assert "between 0 and 10" in error_msg

        is_valid, error_msg = review_service.validate_rating(11)
        assert is_valid is False
        assert "between 0 and 10" in error_msg

    @patch('backend.services.review_service.user_service.get_user_by_email')
    def test_validate_edit_permission_snail(self, mock_get_user, snail_user):
        """Permission check, negative path
        Snail tier should not be able to edit reviews."""
        mock_get_user.return_value = snail_user

        has_permission, error_msg = review_service.validate_edit_permission("viewer@example.com")

        assert has_permission is False
        assert "cannot edit reviews" in error_msg