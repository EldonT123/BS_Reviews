from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from backend.services.search_service import SearchService

router = APIRouter()


# Initialize the search service
search_service = SearchService(database_path="/app/database/archive")


@router.get("/title")
async def search_movies_by_title(
    q: str = Query(..., description="Search query for movie title"),
    exact: bool = Query(False,
                        description="Whether to perform exact match search")
):
    """
    Search for movies by title
    Example:
        /search/title?q=avengers
        /search/title?q=Avengers%20Endgame&exact=true
    """
    results = search_service.search_by_title(q, exact_match=exact)
    return {
        "query": q,
        "exact_match": exact,
        "count": len(results),
        "results": results
    }


@router.get("/genre")
async def search_movies_by_genre(
    genres: List[str] = Query(..., description="List of genres to search for")
):
    """
    Search for movies by genre(s)
    Example:
        /search/genre?genres=Action&genres=Adventure
        /search/genre?genres=Drama
    """
    results = search_service.search_by_genre(genres)
    return {
        "genres": genres,
        "count": len(results),
        "results": results
    }


@router.get("/date-range")
async def search_movies_by_date_range(
    start_date: Optional[str] = Query(None,
                                      description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None,
                                    description="End date (YYYY-MM-DD)")
):
    """
    Search for movies by publication date range
    Example:
        /search/date-range?start_date=2019-01-01&end_date=2019-12-31
        /search/date-range?start_date=2015-01-01
        /search/date-range?end_date=2020-12-31
    """
    if not start_date and not end_date:
        raise HTTPException(
            status_code=400,
            detail="At least one of start_date or end_date must be provided"
        )
    try:
        results = search_service.search_by_date_range(start_date, end_date)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format. YYYY-MM-DD Expected. Error: {str(e)}"
        )
    return {
        "start_date": start_date,
        "end_date": end_date,
        "count": len(results),
        "results": results
    }


@router.get("/year/{year}")
async def search_movies_by_year(year: int):
    """
    Search for movies by publication year
    Example:
        /search/year/2019
        /search/year/2020
    """
    if year < 1800 or year > 2100:
        raise HTTPException(
            status_code=400,
            detail="Year must be between 1800 and 2100"
        )
    results = search_service.search_by_year(year)
    return {
        "year": year,
        "count": len(results),
        "results": results
    }


@router.get("/advanced")
async def advanced_search(
    title: Optional[str] = Query(None,
                                 description="Search term for movie title"),
    genres: Optional[List[str]] = Query(None,
                                        description="genres to filter"),
    start_date: Optional[str] = Query(None,
                                      description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None,
                                    description="End date (YYYY-MM-DD)"),
    min_rating: Optional[float] = Query(None, ge=0, le=10,
                                        description="Minimum IMDb rating"),
    max_rating: Optional[float] = Query(None, ge=0, le=10,
                                        description="Maximum IMDb rating")
):
    """
    Perform an advanced search with multiple criteria
    Example:
        /search/advanced?title=avengers&genres=Action&min_rating=8.0
        /search/advanced?genres=Drama&start_date=2015-01-01&end_date=2020-12-31
        /search/advanced?min_rating=8.5&genres=Action&genres=Adventure
    """
    if (min_rating is not None
            and max_rating is not None
            and min_rating > max_rating):
        raise HTTPException(
            status_code=400,
            detail="min_rating cannot be greater than max_rating"
        )
    try:
        results = search_service.advanced_search(
            title=title,
            genres=genres,
            start_date=start_date,
            end_date=end_date,
            min_rating=min_rating,
            max_rating=max_rating
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input format: {str(e)}"
        )
    return {
        "search_criteria": {
            "title": title,
            "genres": genres,
            "start_date": start_date,
            "end_date": end_date,
            "min_rating": min_rating,
            "max_rating": max_rating
        },
        "count": len(results),
        "results": results
    }


@router.get("/movie/{movie_title}")
async def get_movie_with_reviews(movie_title: str):
    """
    Get complete movie data including metadata and reviews
    Example:
        /search/movie/Avengers%20Endgame
    """
    result = search_service.get_movie_with_reviews(movie_title)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Movie '{movie_title}' not found"
        )
    return result


@router.get("/genres")
async def get_all_genres():
    """
    Get a list of all unique genres in the database
    Example:
        /search/genres
    """
    genres = search_service.get_all_genres()
    return {
        "count": len(genres),
        "genres": genres
    }
