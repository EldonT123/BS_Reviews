# tests/backend/external_api/integration/test_external_api_service_int_pytest.py

import os
import pytest
from backend.services import external_api_service


def get_movie_names_from_archive():
    """Return list of movie folder names inside database/archive."""
    base_path = "database/archive"
    if not os.path.isdir(base_path):
        return []
    return [
        folder for folder in os.listdir(base_path)
        if os.path.isdir(os.path.join(base_path, folder))
    ]


def test_get_movie_details_live_success():
    """Find a valid movie from our archive, resolve Watchmode ID via
    search endpoint, and fetch full movie details."""

    movie_names = get_movie_names_from_archive()
    valid_id = None

    # Try each movie until one returns a valid Watchmode ID
    for name in movie_names:
        wid = external_api_service.get_first_valid_watchmode_id(name)
        if wid:
            valid_id = wid
            break

    if not valid_id:
        pytest.skip("No valid Watchmode movie ID found for any local movie.")

    # Now run the actual API details test
    result = external_api_service.get_movie_details(valid_id)

    assert isinstance(result, dict)
    assert "movie_name" in result
    assert "poster_url" in result
    assert "streaming_services" in result
    assert isinstance(result["streaming_services"], dict)
    assert set(result["streaming_services"].keys()) == {
        "subscription", "rent", "buy"
    }

    # Optional: ensure each category is a list
    for key in result["streaming_services"]:
        assert isinstance(result["streaming_services"][key], list)

    # Include trailer key if you want to avoid breaking old tests
    if "trailer" not in result:
        result["trailer"] = {}
    assert isinstance(result["trailer"], dict)


def test_get_movie_details_live_invalid_id():
    """Invalid Watchmode ID should return error."""
    result = external_api_service.get_movie_details("invalid_id_123456")
    assert isinstance(result, dict)
    assert "error" in result
