# ============================================
# external_api_service.py (UPDATED)
# ============================================
import requests
import os
from typing import Dict

REELGOOD_BASE_URL = "https://partner-api.reelgood.com/v1.0/content/movie"
API_KEY = os.environ.get("REELGOOD_API_KEY")  # Store your key in environment variables

# Simple in-memory cache
_movie_cache: Dict[str, dict] = {}

def get_movie_details(movie_id: str) -> dict:
    """
    Fetch movie details from Reelgood API, with caching.
    
    Returns JSON containing:
    - movie_name
    - poster_url
    - streaming_services (with prices)
    - trailer info
    """
    # Return cached result if available
    if movie_id in _movie_cache:
        return _movie_cache[movie_id]

    try:
        url = f"{REELGOOD_BASE_URL}/{movie_id}"
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Extract streaming services and prices
        services = []
        for avail in data.get("availability", []):
            service_info = {
                "serviceId": avail.get("serviceId"),
                "serviceGroupId": avail.get("serviceGroupId"),
                "purchaseCostHd": avail.get("purchaseCostHd"),
                "purchaseCostSd": avail.get("purchaseCostSd"),
                "rentalCostHd": avail.get("rentalCostHd"),
                "rentalCostSd": avail.get("rentalCostSd"),
                "accessType": avail.get("accessType"),
                "links": avail.get("links", {})
            }
            services.append(service_info)

        # Build clean JSON for frontend
        result = {
            "movie_name": data.get("title"),
            "poster_url": data.get("posterUrl"),
            "streaming_services": services,
            "trailer": data.get("trailer", {})
        }

        # Cache the result
        _movie_cache[movie_id] = result

        return result

    except requests.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
