import pytest
import json
from unittest.mock import patch, mock_open
from backend.services.search_service import SearchService


@pytest.fixture
def search_service():
    """Fixture to create a SearchService instance"""
    return SearchService(database_path="app/test_database/archive")


@pytest.fixture
def sample_metadata():
    """Fixture with sample movie metadata"""
    return {
        "title": "Avengers Endgame",
        "movieIMDbRating": 8.4,
        "totalRatingCount": 1073964,
        "movieGenres": ["Action", "Adventure", "Drama"],
        "directors": ["Anthony Russo", "Joe Russo"],
        "datePublished": "2019-04-26",
        "description": "After the devastating events...",
        "duration": 181
    }


@pytest.fixture
def sample_metadata_joker():
    """Fixture with sample Joker movie metadata"""
    return {
        "title": "Joker",
        "movieIMDbRating": 8.4,
        "movieGenres": ["Crime", "Drama", "Thriller"],
        "datePublished": "2019-10-04",
        "directors": ["Todd Phillips"],
        "description": "A mentally troubled comedian...",
        "duration": 122
    }


@pytest.fixture
def sample_metadata_inception():
    """Fixture with sample Inception movie metadata"""
    return {
        "title": "Inception",
        "movieIMDbRating": 8.8,
        "movieGenres": ["Action", "Sci-Fi", "Thriller"],
        "datePublished": "2010-07-16",
        "directors": ["Christopher Nolan"],
        "description": "A thief who steals secrets...",
        "duration": 148
    }


class TestSearchServiceInitialization:
    """Tests for SearchService initialization"""

    def test_default_initialization(self):
        """Test SearchService initializes with default path"""
        service = SearchService()
        assert service.database_path == "/app/database/archive"

    def test_custom_path_initialization(self):
        """Test SearchService initializes with custom path"""
        custom_path = "custom/path/to/movies"
        service = SearchService(database_path=custom_path)
        assert service.database_path == custom_path


class TestLoadMovieMetadata:
    """Tests for _load_movie_metadata method"""

    def test_load_metadata_success(self, search_service, sample_metadata):
        """Test successfully loading metadata from JSON file"""
        mock_file_data = json.dumps(sample_metadata)

        with patch('os.path.exists', return_value=True), \
             patch('builtins.open',
                   mock_open(read_data=mock_file_data)):

            result = search_service._load_movie_metadata(
                "Avengers Endgame"
            )

            assert result == sample_metadata
            assert result["title"] == "Avengers Endgame"

    def test_load_metadata_file_not_found(self, search_service):
        """Test loading metadata when file doesn't exist"""
        with patch('os.path.exists', return_value=False):
            result = search_service._load_movie_metadata(
                "NonexistentMovie"
            )
            assert result is None


class TestLoadMovieReviews:
    """Tests for _load_movie_reviews method"""

    def test_load_reviews_success(self, search_service):
        """Test successfully loading reviews from CSV file"""
        csv_data = (
            "Date of Review,User,Usefulness Vote,Total Votes,"
            "User's Rating out of 10,Review Title,Review\n"
        )
        csv_data += (
            "2019-05-01,user123,50,60,10,Perfect ending,"
            "This movie was amazing!\n"
        )

        with patch('os.path.exists', return_value=True), \
             patch('builtins.open',
                   mock_open(read_data=csv_data)):

            result = search_service._load_movie_reviews(
                "Avengers Endgame"
            )

            assert len(result) == 1
            assert result[0]["User"] == "user123"

    def test_load_reviews_file_not_found(self, search_service):
        """Test loading reviews when file doesn't exist"""
        with patch('os.path.exists', return_value=False):
            result = search_service._load_movie_reviews(
                "NonexistentMovie"
            )
            assert result == []


class TestGetAllMovieFolders:
    """Tests for _get_all_movie_folders method"""

    def test_get_folders_success(self, search_service):
        """Test getting all movie folders"""
        mock_folders = ["Avengers Endgame", "Joker", "Inception"]

        with patch('os.path.exists', return_value=True), \
             patch('os.listdir', return_value=mock_folders), \
             patch('os.path.isdir', return_value=True):

            result = search_service._get_all_movie_folders()
            assert result == mock_folders
            assert len(result) == 3

    def test_get_folders_path_not_exists(self, search_service):
        """Test getting folders when path doesn't exist"""
        with patch('os.path.exists', return_value=False):
            result = search_service._get_all_movie_folders()
            assert result == []


class TestSearchByTitle:
    """Tests for search_by_title method"""

    def test_search_partial_match(self, search_service, sample_metadata,
                                  sample_metadata_joker):
        """Test partial title search"""
        with patch.object(
            search_service,
            '_get_all_movie_folders',
            return_value=["Avengers Endgame", "Joker"]
        ), \
                patch.object(
                 search_service,
                 '_load_movie_metadata',
                 side_effect=[sample_metadata, sample_metadata_joker]
             ):

            results = search_service.search_by_title("Avengers")

            assert len(results) == 1
            assert results[0]["title"] == "Avengers Endgame"

    def test_search_exact_match(self, search_service, sample_metadata,
                                sample_metadata_joker):
        """Test exact title search"""
        with patch.object(
            search_service,
            '_get_all_movie_folders',
            return_value=["Avengers Endgame", "Joker"]
        ), \
                patch.object(
                 search_service,
                 '_load_movie_metadata',
                 side_effect=[sample_metadata, sample_metadata_joker]
             ):

            results = search_service.search_by_title("Joker",
                                                     exact_match=True)

            assert len(results) == 1
            assert results[0]["title"] == "Joker"

    def test_search_case_insensitive(self, search_service, sample_metadata):
        """Test that search is case insensitive"""
        with patch.object(
            search_service,
            '_get_all_movie_folders',
            return_value=["Avengers Endgame"]
        ), \
                patch.object(
                 search_service,
                 '_load_movie_metadata',
                 return_value=sample_metadata
             ):

            results = search_service.search_by_title("avengers endgame")

            assert len(results) == 1

    def test_search_no_results(self, search_service, sample_metadata):
        """Test search with no matching results"""
        with patch.object(
            search_service,
            '_get_all_movie_folders',
            return_value=["Avengers Endgame"]
        ), \
                patch.object(
                 search_service,
                 '_load_movie_metadata',
                 return_value=sample_metadata
             ):

            results = search_service.search_by_title("Nonexistent Movie")
            assert len(results) == 0


class TestSearchByGenre:
    """Tests for search_by_genre method"""

    def test_search_single_genre(self, search_service, sample_metadata,
                                 sample_metadata_joker):
        """Test searching by single genre"""
        with patch.object(
            search_service,
            '_get_all_movie_folders',
            return_value=["Avengers Endgame", "Joker"]
        ), \
                patch.object(
                 search_service,
                 '_load_movie_metadata',
                 side_effect=[sample_metadata, sample_metadata_joker]
             ):

            results = search_service.search_by_genre(["Action"])

            assert len(results) == 1
            assert results[0]["title"] == "Avengers Endgame"

    def test_search_multiple_genres(self, search_service, sample_metadata,
                                    sample_metadata_joker,
                                    sample_metadata_inception):
        """Test searching by multiple genres (OR logic)"""
        with patch.object(
            search_service,
            '_get_all_movie_folders',
            return_value=[
                "Avengers Endgame",
                "Joker",
                "Inception"
            ]
        ), \
                patch.object(
                 search_service,
                 '_load_movie_metadata',
                 side_effect=[
                     sample_metadata,
                     sample_metadata_joker,
                     sample_metadata_inception
                 ]
             ):

            results = search_service.search_by_genre(["Crime", "Sci-Fi"])

            assert len(results) == 2
            titles = [r["title"] for r in results]
            assert "Joker" in titles
            assert "Inception" in titles


class TestSearchByDateRange:
    """Tests for search_by_date_range method"""

    def test_search_within_range(self, search_service, sample_metadata,
                                 sample_metadata_joker):
        """Test searching within date range"""
        with patch.object(
            search_service,
            '_get_all_movie_folders',
            return_value=["Avengers Endgame", "Joker"]
        ), \
                patch.object(
                 search_service,
                 '_load_movie_metadata',
                 side_effect=[sample_metadata, sample_metadata_joker]
             ):

            results = search_service.search_by_date_range(
                "2019-01-01", "2019-12-31"
            )
            assert len(results) == 2

    def test_search_only_start_date(self, search_service, sample_metadata,
                                    sample_metadata_inception):
        """Test searching with only start date"""
        with patch.object(
            search_service,
            '_get_all_movie_folders',
            return_value=["Avengers Endgame", "Inception"]
        ), \
                patch.object(
                 search_service,
                 '_load_movie_metadata',
                 side_effect=[sample_metadata, sample_metadata_inception]
             ):

            results = search_service.search_by_date_range(
                "2015-01-01", None
            )

            assert len(results) == 1
            assert results[0]["title"] == "Avengers Endgame"

    def test_search_invalid_date_format(self, search_service,
                                        sample_metadata):
        """Test searching with invalid date format raises error"""
        with patch.object(
            search_service,
            '_get_all_movie_folders',
            return_value=["Avengers Endgame"]
        ), \
                patch.object(
                 search_service,
                 '_load_movie_metadata',
                 return_value=sample_metadata
             ):

            with pytest.raises(ValueError):
                search_service.search_by_date_range(
                    "invalid-date", "2019-12-31"
                )


class TestSearchByYear:
    """Tests for search_by_year method"""

    def test_search_by_year(self, search_service, sample_metadata,
                            sample_metadata_joker):
        """Test searching by specific year"""
        with patch.object(
            search_service,
            '_get_all_movie_folders',
            return_value=["Avengers Endgame", "Joker"]
        ), \
                patch.object(
                 search_service,
                 '_load_movie_metadata',
                 side_effect=[sample_metadata, sample_metadata_joker]
             ):

            results = search_service.search_by_year(2019)
            assert len(results) == 2


class TestAdvancedSearch:
    """Tests for advanced_search method"""

    def test_advanced_search_multiple_criteria(self, search_service,
                                               sample_metadata):
        """Test advanced search with multiple criteria"""
        with patch.object(
            search_service,
            '_get_all_movie_folders',
            return_value=["Avengers Endgame"]
        ), \
                patch.object(
                 search_service,
                 '_load_movie_metadata',
                 return_value=sample_metadata
             ):

            results = search_service.advanced_search(
                title="Avengers",
                genres=["Action"],
                start_date="2019-01-01",
                end_date="2019-12-31",
                min_rating=8.0,
                max_rating=9.0
            )

            assert len(results) == 1
            assert results[0]["title"] == "Avengers Endgame"

    def test_advanced_search_rating_filter(self, search_service,
                                           sample_metadata,
                                           sample_metadata_inception):
        """Test advanced search with rating filters"""
        with patch.object(
            search_service,
            '_get_all_movie_folders',
            return_value=["Avengers Endgame", "Inception"]
        ), \
                patch.object(
                 search_service,
                 '_load_movie_metadata',
                 side_effect=[sample_metadata, sample_metadata_inception]
             ):

            results = search_service.advanced_search(min_rating=8.5)

            assert len(results) == 1
            assert results[0]["title"] == "Inception"


class TestGetMovieWithReviews:
    """Tests for get_movie_with_reviews method"""

    def test_get_movie_with_reviews_success(self, search_service,
                                            sample_metadata):
        """Test getting movie with reviews"""
        csv_data = (
            "Date of Review,User,Usefulness Vote,"
            "Total Votes,User's Rating out of 10,Review Title,Review\n"
        )
        csv_data += (
            "2019-05-01,user123,50,60,10,Perfect ending,"
            "This movie was amazing!\n"
        )

        with patch.object(
            search_service,
            '_load_movie_metadata',
            return_value=sample_metadata
        ), \
                patch('os.path.exists', return_value=True), \
                patch('builtins.open', mock_open(read_data=csv_data)):

            result = search_service.get_movie_with_reviews(
                "Avengers Endgame"
            )

            assert result is not None
            assert result["metadata"]["title"] == "Avengers Endgame"
            assert result["review_count"] == 1

    def test_get_movie_with_reviews_not_found(self, search_service):
        """Test getting movie that doesn't exist"""
        with patch.object(
            search_service,
            '_load_movie_metadata',
            return_value=None
        ):
            result = search_service.get_movie_with_reviews(
                "NonexistentMovie"
            )
            assert result is None


class TestGetAllGenres:
    """Tests for get_all_genres method"""

    def test_get_all_genres(self, search_service, sample_metadata,
                            sample_metadata_joker,
                            sample_metadata_inception):
        """Test getting all unique genres"""
        with patch.object(
            search_service,
            '_get_all_movie_folders',
            return_value=[
                "Avengers Endgame",
                "Joker",
                "Inception"
            ]
        ), \
                patch.object(
                 search_service,
                 '_load_movie_metadata',
                 side_effect=[
                     sample_metadata,
                     sample_metadata_joker,
                     sample_metadata_inception
                 ]
             ):

            genres = search_service.get_all_genres()

            assert len(genres) == 6
            # Action, Adventure, Drama, Crime, Thriller, Sci-Fi
            assert "Action" in genres
            assert "Crime" in genres
            assert "Sci-Fi" in genres
            assert genres == sorted(genres)  # Should be sorted

    def test_get_all_genres_empty(self, search_service):
        """Test getting genres when no movies exist"""
        with patch.object(
            search_service,
            '_get_all_movie_folders',
            return_value=[]
        ):
            genres = search_service.get_all_genres()
            assert len(genres) == 0
