# backend/routes/external_api_routes.py
"""Routes for fetching movie details from Reelgood external API."""
from fastapi import APIRouter, HTTPException, status
from backend.services import external_api_service

router = APIRouter()


# ==================== Routes ====================

@router.get("/{movie_id}")
async def get_movie_external(movie_id: str):
    """
    Get movie details from Reelgood (poster, streaming services, prices, trailer)
    """
    result = external_api_service.get_movie_details(movie_id)

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )

    return result
