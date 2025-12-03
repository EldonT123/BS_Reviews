import requests
from typing import Dict

WATCHMODE_BASE_URL = "https://api.watchmode.com/v1"
API_KEY = "S006Nf0GbCUGOwF5zzB601Q6tK29tXXpkanhXEVv"

_movie_cache: Dict[str, dict] = {}


def fetch_sources(movie_id: str) -> dict:
    """
    Fetch streaming services for a movie from Watchmode,
    filter only Canada sources, and group by type (sub/rent/buy).
    """
    grouped = {"subscription": [], "rent": [], "buy": []}

    try:
        resp = requests.get(
            f"{WATCHMODE_BASE_URL}/title/{movie_id}/sources/",
            params={"apiKey": API_KEY},
            timeout=10
        )
        resp.raise_for_status()
        sources = resp.json()

        if not isinstance(sources, list):
            sources = []

        # filter for Canada only
        sources_ca = [s for s in sources if s.get("region") == "CA"]

        for s in sources_ca:
            source_info = {
                "name": s.get("name") or "",
                "web_url": s.get("web_url") or "",
                "price": s.get("price")  # for rent/buy
            }
            t = s.get("type")
            if t == "sub":
                grouped["subscription"].append(source_info)
            elif t == "rent":
                grouped["rent"].append(source_info)
            elif t == "buy":
                grouped["buy"].append(source_info)

    except Exception as e:
        print(f"Warning: failed to fetch sources for movie {movie_id}: {e}")

    return grouped


def get_movie_details(movie_id: str) -> dict:
    """
    Fetch movie details from Watchmode in a stable, frontend-ready structure.
    """
    if not movie_id:
        return {"error": "Invalid movie ID"}

    if movie_id in _movie_cache:
        return _movie_cache[movie_id]

    try:
        resp = requests.get(
            f"{WATCHMODE_BASE_URL}/title/{movie_id}/details/",
            params={"apiKey": API_KEY},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"error": f"API request failed: {str(e)}"}

    movie_name = (
        data.get("title")
        or data.get("original_title")
        or data.get("name") or "Unknown"
    )
    poster_url = data.get("poster") or data.get("backdrop") or ""

    # Fetch streaming services using the correct endpoint
    streaming_services = fetch_sources(movie_id)

    result = {
        "movie_name": movie_name,
        "poster_url": poster_url,
        "streaming_services": streaming_services
    }

    _movie_cache[movie_id] = result
    return result


def get_first_valid_watchmode_id(movie_name: str) -> str | None:
    """
    Search Watchmode for a movie by name and return the first matching ID.
    """
    if not movie_name:
        return None

    try:
        resp = requests.get(
            f"{WATCHMODE_BASE_URL}/search/",
            params={
                "apiKey": API_KEY,
                "search_field": "name",
                "search_value": movie_name
            },
            timeout=10
        )
        resp.raise_for_status()
        results = resp.json().get("title_results", [])
    except Exception:
        return None

    if not results:
        return None

    return str(results[0].get("id"))
