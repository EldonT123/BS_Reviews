"""Unit tests for external_api_service with proper mocking and fixtures."""
import pytest
from unittest.mock import patch, Mock
from backend.services.external_api_service import (
    get_movie_details, _movie_cache
)


# ==================== Fixtures ====================

@pytest.fixture
def sample_movie_response():
    """Fixture - Sample Watchmode API response for a typical movie."""
    return {
        "name": "Sample Movie",
        "poster": "https://example.com/poster.jpg",
        "sources": [
            {
                "source_id": 1,
                "type": "buy",
                "price": 12.99,
                "web_url": "https://example.com",
                "region": "CA"  # <-- add this
            }
        ]
    }


@pytest.fixture
def sample_movie_missing_keys():
    """Fixture - Sample Watchmode API response missing sources."""
    return {"name": "No Services Movie", "poster": "url_here"}


# ==================== get_movie_details Tests ====================

class TestGetMovieDetails:
    """Unit tests for get_movie_details covering caching, responses,
    errors, and missing keys.
    """

    def test_get_movie_details_success(self, sample_movie_response):
        """Return properly structured movie details when API responds."""
        _movie_cache.clear()
        movie_id = "123"

        with patch(
            "backend.services.external_api_service.requests.get"
        ) as mock_get:

            def mock_get_side_effect(url, *args, **kwargs):
                if "sources" in url:
                    return Mock(
                        status_code=200,
                        json=lambda: sample_movie_response["sources"]
                    )
                else:  # details endpoint
                    return Mock(
                        status_code=200,
                        json=lambda: sample_movie_response
                    )

            mock_get.side_effect = mock_get_side_effect

            result = get_movie_details(movie_id)

            assert result["movie_name"] == "Sample Movie"
            assert result["poster_url"] == "https://example.com/poster.jpg"
            # grouped streaming services: check 'buy' list
            assert len(result["streaming_services"]["buy"]) == 1
            assert result["streaming_services"]["buy"][0]["price"] == 12.99
            assert movie_id in _movie_cache

    def test_get_movie_details_request_exception(self):
        """Return error dict if API request fails."""
        movie_id = "fail123"

        with patch(
            "backend.services.external_api_service.requests.get"
        ) as mock_get:
            mock_get.side_effect = Exception("API down")
            result = get_movie_details(movie_id)
            assert "error" in result

    def test_get_movie_details_cache_used(self, sample_movie_response):
        """Use cached result on subsequent calls without hitting the API."""
        _movie_cache.clear()
        movie_id = "cached123"

        # Mock requests.get to return different responses depending on URL
        with patch(
            "backend.services.external_api_service.requests.get"
        ) as mock_get:

            def mock_get_side_effect(url, *args, **kwargs):
                if "/sources/" in url:
                    return Mock(
                        status_code=200,
                        json=lambda: sample_movie_response["sources"]
                    )
                else:  # /details/
                    return Mock(
                        status_code=200,
                        json=lambda: sample_movie_response
                    )

            mock_get.side_effect = mock_get_side_effect

            # First call: fetches from API
            result1 = get_movie_details(movie_id)
            # Second call: should use cache, no new API calls
            result2 = get_movie_details(movie_id)

            # Only 1 /details/ call should have happened
            details_calls = [
                call for call in mock_get.call_args_list
                if "/details/" in call[0][0]
            ]
            assert len(details_calls) == 1

            # Results should be identical
            assert result1 == result2

    def test_get_movie_details_missing_keys(self, sample_movie_missing_keys):
        """Handle API responses missing sources gracefully."""
        _movie_cache.clear()
        movie_id = "missing_keys"

        with patch(
            "backend.services.external_api_service.requests.get"
        ) as mock_get:
            mock_get.return_value = Mock(
                status_code=200, json=lambda: sample_movie_missing_keys
            )

            result = get_movie_details(movie_id)
            # streaming_services should be a dict of empty lists
            assert result["streaming_services"] == {
                "subscription": [], "rent": [], "buy": []
            }

    def test_get_movie_details_invalid_id(self):
        """Return error dict if movie_id is invalid (e.g., None)."""
        _movie_cache.clear()
        result = get_movie_details(None)
        assert "error" in result or result.get("movie_name") is None
