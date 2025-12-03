"""Routes for fetching movie details from Watchmode external API."""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from backend.services import external_api_service

router = APIRouter()


# ==================== Pydantic Models ====================

# Individual streaming service (for subscription, rent, buy)
class StreamingService(BaseModel):
    name: str
    web_url: str
    price: Optional[float] = None  # only for rent/buy


# Grouped streaming services
class StreamingServiceGrouped(BaseModel):
    subscription: List[StreamingService] = []
    rent: List[StreamingService] = []
    buy: List[StreamingService] = []


# Movie details model
class MovieDetails(BaseModel):
    movie_name: str
    poster_url: Optional[str]
    streaming_services: StreamingServiceGrouped


# ==================== Routes ====================

@router.get(
    "/movie/{movie_identifier}",
    response_model=MovieDetails,
    summary="Get movie details from Watchmode external API"
)
async def get_movie_external(movie_identifier: str):
    """
    Get movie details including poster, streaming services, prices,
    and trailer.
    
    Accepts either a database movie ID or a movie name. Converts to
    Watchmode ID internally.
    """
    # Step 1: Convert movie_identifier to Watchmode ID
    # Here we assume movie_identifier could be a name if it's not a valid Watchmode ID
    watchmode_id = movie_identifier

    # Optional: try to detect if it's not a numeric Watchmode ID
    if not movie_identifier.isdigit():
        # Treat as a movie name
        watchmode_id = external_api_service.get_first_valid_watchmode_id(movie_identifier)
        if not watchmode_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Could not find Watchmode ID for '{movie_identifier}'"
            )

    # Step 2: Fetch movie details
    result = await asyncio.to_thread(
        external_api_service.get_movie_details,
        watchmode_id
    )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )

    return result
