import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import os
import json

from backend.services.external_api_service import get_first_valid_watchmode_id, get_movie_details

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname
                           (os.path.dirname(os.path.abspath(__file__))))
DATABASE_DIR = os.getenv("DATABASE_DIR", os.path.join(
    BASE_DIR, "database", "archive"))


@router.get("/top")
async def get_top_movies():
    movies = []

    for folder in os.listdir(DATABASE_DIR):
        movie_dir = os.path.join(DATABASE_DIR, folder)
        metadata_path = os.path.join(movie_dir, "metadata.json")

        if os.path.isfile(metadata_path):
            try:
                with open(metadata_path, "r") as f:
                    data = json.load(f)

                title = data.get("title", folder)

                # === Fetch external poster URL ===
                wm_id = get_first_valid_watchmode_id(title)
                poster_url = None

                if wm_id:
                    details = await asyncio.to_thread(get_movie_details, wm_id)
                    poster_url = details.get("poster_url")

                movies.append({
                    "title": title,
                    "movieIMDbRating": float(data.get("movieIMDbRating", 0)),
                    "posterPath": poster_url or f"http://localhost:8000/movies/poster/{folder}"
                })

            except Exception as e:
                print(f"Error reading metadata for {folder}: {e}")

    movies.sort(key=lambda m: m["movieIMDbRating"], reverse=True)
    return JSONResponse(content=movies[:5])


@router.get("/most_commented")
async def get_most_commented_movies():
    movies = []

    for folder in os.listdir(DATABASE_DIR):
        movie_dir = os.path.join(DATABASE_DIR, folder)
        metadata_path = os.path.join(movie_dir, "metadata.json")

        if os.path.isfile(metadata_path):
            try:
                with open(metadata_path, "r") as f:
                    data = json.load(f)

                title = data.get("title", folder)

                # === Fetch external poster URL ===
                wm_id = get_first_valid_watchmode_id(title)
                poster_url = None

                if wm_id:
                    details = await asyncio.to_thread(get_movie_details, wm_id)
                    poster_url = details.get("poster_url")

                movies.append({
                    "title": title,
                    "commentCount": data.get("commentCount", 0),
                    "posterPath": poster_url or f"http://localhost:8000/movies/poster/{folder}"
                })

            except Exception as e:
                print(f"Error reading metadata for {folder}: {e}")

    movies.sort(key=lambda m: m["commentCount"], reverse=True)
    return JSONResponse(content=movies[:10])


@router.get("/poster/{movie_name}")
async def get_poster(movie_name: str):
    poster_path = os.path.join(DATABASE_DIR, movie_name, "poster.jpg")

    if os.path.exists(poster_path):
        return FileResponse(poster_path, media_type="image/jpeg")
    else:
        raise HTTPException(status_code=404, detail="Poster not found")
