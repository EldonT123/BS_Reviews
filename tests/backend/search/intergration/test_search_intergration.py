import pytest
import os
import json
import csv
import tempfile
import shutil
from fastapi.testclient import TestClient
from backend.services.search_service import SearchService


@pytest.fixture
def temp_database():
    """Create a temporary database structure for integration tests"""
    temp_dir = tempfile.mkdtemp()
    archive_path = os.path.join(temp_dir, "archive")
    os.makedirs(archive_path)

    # Create test movies
    movies = [
        {
            "folder": "Avengers Endgame",
            "metadata": {
                "title": "Avengers Endgame",
                "movieIMDbRating": 8.4,
                "totalRatingCount": 1073964,
                "totalUserReviews": "9.5K",
                "totalCriticReviews": "593",
                "metaScore": "78",
                "movieGenres": ["Action", "Adventure", "Drama"],
                "directors": ["Anthony Russo", "Joe Russo"],
                "datePublished": "2019-04-26",
                "creators": [
                    "Christopher Markus",
                    "Stephen McFeely",
                    "Stan Lee"
                ],
                "mainStars": [
                    "Robert Downey Jr.",
                    "Chris Evans",
                    "Mark Ruffalo"
                ],
                "description": (
                    "After the devastating events of Avengers: "
                    "Infinity War (2018)..."
                ),
                "duration": 181
            },
            "reviews": [
                [
                    "2019-05-01",
                    "user123",
                    "50",
                    "60",
                    "10",
                    "Perfect ending",
                    "This movie was amazing!"
                ],
                [
                    "2019-05-02",
                    "user456",
                    "30",
                    "40",
                    "9",
                    "Great film",
                    "Loved every minute of it."
                ]
            ]
        },
        {
            "folder": "Joker",
            "metadata": {
                "title": "Joker",
                "movieIMDbRating": 8.4,
                "totalRatingCount": 987654,
                "totalUserReviews": "7.2K",
                "totalCriticReviews": "502",
                "metaScore": "59",
                "movieGenres": ["Crime", "Drama", "Thriller"],
                "directors": ["Todd Phillips"],
                "datePublished": "2019-10-04",
                "creators": ["Todd Phillips", "Scott Silver"],
                "mainStars": [
                    "Joaquin Phoenix",
                    "Robert De Niro",
                    "Zazie Beetz"
                ],
                "description": "A mentally troubled comedian...",
                "duration": 122
            },
            "reviews": [
                [
                    "2019-10-10",
                    "cinephile99",
                    "100",
                    "110",
                    "10",
                    "Masterpiece",
                    "Joaquin Phoenix delivers an unforgettable "
                    "performance."
                ]
            ]
        },
        {
            "folder": "Inception",
            "metadata": {
                "title": "Inception",
                "movieIMDbRating": 8.8,
                "totalRatingCount": 2134567,
                "totalUserReviews": "12.3K",
                "totalCriticReviews": "720",
                "metaScore": "74",
                "movieGenres": ["Action", "Sci-Fi", "Thriller"],
                "directors": ["Christopher Nolan"],
                "datePublished": "2010-07-16",
                "creators": ["Christopher Nolan"],
                "mainStars": [
                    "Leonardo DiCaprio",
                    "Joseph Gordon-Levitt",
                    "Ellen Page"
                ],
                "description": "A thief who steals corporate secrets...",
                "duration": 148
            },
            "reviews": [
                [
                    "2010-07-20",
                    "dreamfan",
                    "200",
                    "220",
                    "10",
                    "Mind-bending",
                    "Best movie ever!"
                ],
                [
                    "2010-07-21",
                    "moviebuff",
                    "150",
                    "180",
                    "9",
                    "Complex but great",
                    "Required multiple viewings."
                ]
            ]
        },
        {
            "folder": "The Dark Knight",
            "metadata": {
                "title": "The Dark Knight",
                "movieIMDbRating": 9.0,
                "totalRatingCount": 2456789,
                "totalUserReviews": "15.1K",
                "totalCriticReviews": "850",
                "metaScore": "84",
                "movieGenres": ["Action", "Crime", "Drama"],
                "directors": ["Christopher Nolan"],
                "datePublished": "2008-07-18",
                "creators": [
                    "Jonathan Nolan",
                    "Christopher Nolan"
                ],
                "mainStars": [
                    "Christian Bale",
                    "Heath Ledger",
                    "Aaron Eckhart"
                ],
                "description": (
                    "When the menace known as the Joker wreaks "
                    "havoc..."
                ),
                "duration": 152
            },
            "reviews": [
                [
                    "2008-07-25",
                    "batmanfan",
                    "500",
                    "520",
                    "10",
                    "Perfect",
                    "Heath Ledger's Joker is iconic."
                ]
            ]
        }
    ]

    # Create movie folders with metadata and reviews
    for movie in movies:
        movie_path = os.path.join(archive_path, movie["folder"])
        os.makedirs(movie_path)

        # Write metadata.json
        metadata_path = os.path.join(movie_path, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(movie["metadata"], f, indent=2)

        # Write movieReviews.csv
        reviews_path = os.path.join(movie_path, "movieReviews.csv")
        with open(reviews_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Date of Review",
                "User",
                "Usefulness Vote",
                "Total Votes",
                "User's Rating out of 10",
                "Review Title",
                "Review"
            ])
            writer.writerows(movie["reviews"])

    yield archive_path

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def search_service_with_data(temp_database):
    """Create a SearchService instance with test data"""
    return SearchService(database_path=temp_database)


class TestSearchServiceIntegration:
    """Integration tests for SearchService with real file I/O"""

    def test_search_by_title_integration(self, search_service_with_data):
        """Integration test: Search by title with real files"""
        results = search_service_with_data.search_by_title("Avengers")

        assert len(results) == 1
        assert results[0]["title"] == "Avengers Endgame"
        assert results[0]["movieIMDbRating"] == 8.4
        assert "Action" in results[0]["movieGenres"]

    def test_search_by_title_partial_match_integration(
        self, search_service_with_data
    ):
        """Integration test: Partial title search returns multiple results"""
        results = search_service_with_data.search_by_title("the")

        assert len(results) == 1
        assert results[0]["title"] == "The Dark Knight"

    def test_search_by_genre_integration(self, search_service_with_data):
        """Integration test: Search by genre with real files"""
        results = search_service_with_data.search_by_genre(["Action"])

        # Avengers Endgame, Inception, The Dark Knight
        assert len(results) == 3
        titles = [r["title"] for r in results]
        assert "Avengers Endgame" in titles
        assert "Inception" in titles
        assert "The Dark Knight" in titles

    def test_search_by_multiple_genres_integration(
        self, search_service_with_data
    ):
        """Integration test: Search by multiple genres"""
        results = search_service_with_data.search_by_genre(
            ["Crime", "Sci-Fi"]
        )

        # Joker (Crime), Inception (Sci-Fi), The Dark Knight (Crime)
        assert len(results) == 3
        titles = [r["title"] for r in results]
        assert "Joker" in titles
        assert "Inception" in titles
        assert "The Dark Knight" in titles

    def test_search_by_date_range_integration(
        self, search_service_with_data
    ):
        """Integration test: Search by date range with real files"""
        results = search_service_with_data.search_by_date_range(
            "2019-01-01", "2019-12-31"
        )

        # Avengers Endgame and Joker
        assert len(results) == 2
        titles = [r["title"] for r in results]
        assert "Avengers Endgame" in titles
        assert "Joker" in titles

    def test_search_by_year_integration(self, search_service_with_data):
        """Integration test: Search by specific year"""
        results = search_service_with_data.search_by_year(2019)

        assert len(results) == 2
        for result in results:
            assert "2019" in result["datePublished"]

    def test_advanced_search_multiple_criteria_integration(
        self, search_service_with_data
    ):
        """Integration test: Advanced search with multiple criteria"""
        results = search_service_with_data.advanced_search(
            genres=["Action"],
            start_date="2008-01-01",
            end_date="2019-12-31",
            min_rating=8.5
        )

        # Inception (8.8) and The Dark Knight (9.0)
        assert len(results) == 2
        titles = [r["title"] for r in results]
        assert "Inception" in titles
        assert "The Dark Knight" in titles

    def test_advanced_search_title_and_genre_integration(
        self, search_service_with_data
    ):
        """Integration test: Advanced search with title and genre"""
        results = search_service_with_data.advanced_search(
            title="Knight",
            genres=["Action", "Crime"]
        )

        assert len(results) == 1
        assert results[0]["title"] == "The Dark Knight"

    def test_get_movie_with_reviews_integration(
        self, search_service_with_data
    ):
        """Integration test: Get complete movie data with reviews"""
        result = search_service_with_data.get_movie_with_reviews("Inception")

        assert result is not None
        assert result["metadata"]["title"] == "Inception"
        assert result["review_count"] == 2
        assert len(result["reviews"]) == 2
        assert result["reviews"][0]["User"] == "dreamfan"
        assert (
            result["reviews"][1]["Review Title"] == "Complex but great"
        )

    def test_get_movie_with_reviews_not_found_integration(
        self, search_service_with_data
    ):
        """Integration test: Get movie that doesn't exist"""
        result = search_service_with_data.get_movie_with_reviews(
            "Nonexistent Movie"
        )

        assert result is None

    def test_get_all_genres_integration(self, search_service_with_data):
        """Integration test: Get all unique genres from database"""
        genres = search_service_with_data.get_all_genres()

        expected_genres = [
            "Action",
            "Adventure",
            "Crime",
            "Drama",
            "Sci-Fi",
            "Thriller"
        ]
        assert len(genres) == 6
        for genre in expected_genres:
            assert genre in genres
        assert genres == sorted(genres)

    def test_full_workflow_integration(self, search_service_with_data):
        """Integration test: Complete search workflow"""
        # 1. Get all available genres
        all_genres = search_service_with_data.get_all_genres()
        assert "Action" in all_genres

        # 2. Search for action movies
        action_movies = search_service_with_data.search_by_genre(["Action"])
        assert len(action_movies) >= 1

        # 3. Filter by year
        recent_action = search_service_with_data.advanced_search(
            genres=["Action"],
            start_date="2015-01-01"
        )
        assert len(recent_action) >= 1

        # 4. Get specific movie with reviews
        movie = search_service_with_data.get_movie_with_reviews(
            "Avengers Endgame"
        )
        assert movie is not None
        assert movie["review_count"] == 2


class TestSearchRoutesIntegration:
    """Integration tests for search routes with FastAPI TestClient"""

    @pytest.fixture
    def client(self, temp_database, monkeypatch):
        """Create a test client with temporary database"""
        # Import here to avoid circular imports
        from backend.main import app
        from backend.routes import search_routes
        from backend.services.search_service import SearchService

        # Create a test service with temp database
        test_service = SearchService(database_path=temp_database)

        # Monkeypatch the search service to use temp database
        monkeypatch.setattr(
            search_routes,
            'search_service',
            test_service
        )

        return TestClient(app)

    def test_search_title_endpoint_integration(self, client):
        """Integration test: Search by title endpoint"""
        response = client.get("/api/search/title?q=Avengers")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["results"][0]["title"] == "Avengers Endgame"

    def test_search_genre_endpoint_integration(self, client):
        """Integration test: Search by genre endpoint"""
        response = client.get("/api/search/genre?genres=Action")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert "Action" in data["genres"]

    def test_search_year_endpoint_integration(self, client):
        """Integration test: Search by year endpoint"""
        response = client.get("/api/search/year/2019")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert data["year"] == 2019

    def test_search_date_range_endpoint_integration(self, client):
        """Integration test: Search by date range endpoint"""
        response = client.get(
            "/api/search/date-range?"
            "start_date=2019-01-01&end_date=2019-12-31"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2

    def test_advanced_search_endpoint_integration(self, client):
        """Integration test: Advanced search endpoint"""
        response = client.get(
            "/api/search/advanced?genres=Action&min_rating=8.5"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert data["search_criteria"]["min_rating"] == 8.5

    def test_get_movie_endpoint_integration(self, client):
        """Integration test: Get movie with reviews endpoint"""
        response = client.get("/api/search/movie/Inception")

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["title"] == "Inception"
        assert data["review_count"] == 2

    def test_get_genres_endpoint_integration(self, client):
        """Integration test: Get all genres endpoint"""
        response = client.get("/api/search/genres")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 6
        assert "Action" in data["genres"]

    def test_invalid_year_endpoint_integration(self, client):
        """Integration test: Invalid year returns error"""
        response = client.get("/api/search/year/3000")

        assert response.status_code == 400

    def test_movie_not_found_endpoint_integration(self, client):
        """Integration test: Movie not found returns 404"""
        response = client.get("/api/search/movie/Nonexistent%20Movie")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
