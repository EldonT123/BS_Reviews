import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import os
import json
import csv
import re

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_DIR = os.getenv("DATABASE_DIR", os.path.join(BASE_DIR, "database", "archive"))

# -----------------------------
# Helper: Read poster URL from streamingData.csv
# -----------------------------
def get_csv_poster_url(movie_folder: str) -> str | None:
    csv_path = os.path.join(DATABASE_DIR, movie_folder, "streamingData.csv")

    if not os.path.isfile(csv_path):
        return None

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader, None)  # first row
            if row:
                return row.get("Poster URL") or None  # <-- fixed header
    except Exception as e:
        print(f"Error reading CSV for {movie_folder}: {e}")

    return None

# -----------------------------
# Helper: Normalize titles/folder names
# -----------------------------
def normalize(name: str) -> str:
    """Remove punctuation, dashes, colons, apostrophes, etc. Keep capitalization."""
    return re.sub(r"[^\w\s]", "", name).strip()

# ================================
# GET TOP MOVIES
# ================================
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
                poster_url = get_csv_poster_url(folder)

                movies.append({
                    "title": title,
                    "movieIMDbRating": float(data.get("movieIMDbRating", 0)),
                    "posterPath": poster_url or f"http://localhost:8000/api/movies/poster/{folder}"
                })

            except Exception as e:
                print(f"Error reading metadata for {folder}: {e}")

    movies.sort(key=lambda m: m["movieIMDbRating"], reverse=True)
    return JSONResponse(content=movies[:5])

# ================================
# MOST COMMENTED MOVIES
# ================================
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
                poster_url = get_csv_poster_url(folder)

                movies.append({
                    "title": title,
                    "commentCount": data.get("commentCount", 0),
                    "posterPath": poster_url or f"http://localhost:8000/api/movies/poster/{folder}"
                })

            except Exception as e:
                print(f"Error reading metadata for {folder}: {e}")

    movies.sort(key=lambda m: m["commentCount"], reverse=True)
    return JSONResponse(content=movies[:10])

# ================================
# GET STREAMING DATA
# ================================
@router.get("/streaming/{title}")
def get_streaming_data(title: str):
    normalized_title = normalize(title)

    # Search folders by normalized name
    folder_name = None
    for folder in os.listdir(DATABASE_DIR):
        if normalize(folder) == normalized_title:
            folder_name = folder
            break

    if not folder_name:
        raise HTTPException(status_code=404, detail="Movie folder not found")

    folder_path = os.path.join(DATABASE_DIR, folder_name)
    csv_path = os.path.join(folder_path, "streamingData.csv")
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Streaming data not found")

    movie_name = folder_name
    poster_url = None
    streaming_services = {
        "subscription": [],
        "rent": [],
        "buy": []
    }

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        row = next(reader, None)
        if row:
            movie_name = row.get("movie_name", folder_name)
            poster_url = row.get("Poster URL")  # <-- fixed header

            # Parse JSON from correct CSV headers
            for col, key in [
                ("Subscription Services", "subscription"),
                ("Rent Services", "rent"),
                ("Buy Services", "buy")
            ]:
                col_value = row.get(col)
                if col_value:
                    try:
                        items = json.loads(col_value)
                        streaming_services[key] = items
                    except json.JSONDecodeError:
                        streaming_services[key] = []

    return {
        "movie_name": movie_name,
        "poster_url": poster_url or f"http://localhost:8000/api/movies/poster/{folder_name}",
        "streaming_services": streaming_services
    }

# ================================
# SERVE LOCAL POSTER AS FALLBACK
# ================================
@router.get("/poster/{movie_name}")
async def get_poster(movie_name: str):
    normalized_name = normalize(movie_name)

    # Search folders by normalized name
    folder_name = None
    for folder in os.listdir(DATABASE_DIR):
        if normalize(folder) == normalized_name:
            folder_name = folder
            break

    if not folder_name:
        raise HTTPException(status_code=404, detail="Movie folder not found")

    poster_path = os.path.join(DATABASE_DIR, folder_name, "poster.jpg")
    if os.path.exists(poster_path):
        return FileResponse(poster_path, media_type="image/jpeg")
    else:
        raise HTTPException(status_code=404, detail="Poster not found")
