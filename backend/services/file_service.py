# ============================================
# file_service.py
# ============================================
import os
import json
import csv
import shutil

DATABASE_PATH = "database/archive"

REVIEWS_HEADERS = [
    "Date of Review", "Email", "Username", "Dislikes",
    "Likes", "User's Rating out of 10",
    "Review Title", "Review", "Reported", "Report Reason",
    "Report Count", "Penalized", "Hidden"
                   ]


def get_movie_folder(movie_name):
    """Returns the folder path for the given movie."""
    folder_path = os.path.join(DATABASE_PATH, movie_name)
    return folder_path


def check_metadata_exists(movie_name):
    """Check if metadata.json exists for a movie."""
    folder_path = get_movie_folder(movie_name)
    metadata_path = os.path.join(folder_path, "metadata.json")
    return os.path.exists(metadata_path)


def check_reviews_exists(movie_name):
    """Check if movieReviews.csv exists for a movie."""
    folder_path = get_movie_folder(movie_name)
    reviews_path = os.path.join(folder_path, "movieReviews.csv")
    return os.path.exists(reviews_path)


def create_movie_folder(movie_name):
    """Creates a folder for a movie if it doesn't exist."""
    folder_path = get_movie_folder(movie_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

        # Create empty metadata.json
        metadata_path = os.path.join(folder_path, "metadata.json")
        with open(metadata_path, "w", encoding='utf-8') as f:
            json.dump({"average_rating": 0, "total_reviews": 0}, f, indent=2)

        # Create movieReviews.csv with proper headers
        reviews_path = os.path.join(folder_path, "movieReviews.csv")
        with open(reviews_path, "w", encoding='utf-8', newline="") as f:
            writer = csv.writer(f)
            writer.writerow(REVIEWS_HEADERS)
    return folder_path


def create_movie_with_metadata(
    movie_name: str,
    title: str,
    director: str = "",
    genres: list = None,
    year: str = "",
    imdb_rating: float = 0.0,
    description: str = "",
    duration: int = 0,
    creators: list = None,
    main_stars: list = None,
    directors: list = None,
    date_published: str = "",
    total_rating_count: int = 0,
    total_user_reviews: str = "0",
    total_critic_reviews: str = "0",
    meta_score: str = "0"
):
    """
    Create a complete movie folder with metadata and reviews CSV.

    Args:
        movie_name: Folder name for the movie
        title: Display title
        director: Primary director (legacy, use directors instead)
        genres: List of genre strings
        year: Release year (legacy, use date_published instead)
        imdb_rating: IMDb rating (0-10)
        description: Movie description
        duration: Duration in minutes
        creators: List of creators/writers
        main_stars: List of main actors
        directors: List of directors (preferred over director)
        date_published: Full date in YYYY-MM-DD format
        total_rating_count: Number of IMDb ratings
        total_user_reviews: String like "11.3K"
        total_critic_reviews: String like "697"
        meta_score: Metacritic score as string

    Returns:
        bool: True if successful, False if movie already exists
    """
    folder_path = get_movie_folder(movie_name)

    # Check if movie already exists
    if os.path.exists(folder_path):
        return False

    # Create directory
    os.makedirs(folder_path)

    # Handle directors - prefer directors list, fallback to director string
    directors_list = directors if directors else (
        [director] if director else [])

    # Handle date - prefer date_published, fallback to year
    final_date = date_published if date_published else (
        f"{year}-01-01" if year else "")

    # Prepare metadata matching existing structure
    metadata = {
        "title": title,
        "movieIMDbRating": imdb_rating,
        "totalRatingCount": total_rating_count,
        "totalUserReviews": total_user_reviews,
        "totalCriticReviews": total_critic_reviews,
        "metaScore": meta_score,
        "movieGenres": genres if genres else [],
        "directors": directors_list,
        "datePublished": final_date,
        "creators": creators if creators else [],
        "mainStars": main_stars if main_stars else [],
        "description": description,
        "duration": duration,
        "total_reviews": 0,
        "average_rating": 0.0,
        "commentCount": 0
    }

    # Write metadata.json
    metadata_path = os.path.join(folder_path, "metadata.json")
    with open(metadata_path, "w", encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    # Create movieReviews.csv with headers
    reviews_path = os.path.join(folder_path, "movieReviews.csv")
    with open(reviews_path, "w", encoding='utf-8', newline="") as f:
        writer = csv.writer(f)
        writer.writerow([REVIEWS_HEADERS])

    return True


def update_movie_metadata(movie_name: str, metadata_updates: dict):
    """
    Update movie metadata.

    Args:
        movie_name: Movie folder name
        metadata_updates: Dictionary of fields to update

    Returns:
        bool: True if successful, False if movie doesn't exist
    """
    folder_path = get_movie_folder(movie_name)

    if not os.path.exists(folder_path):
        return False

    metadata_path = os.path.join(folder_path, "metadata.json")

    # Read existing metadata
    with open(metadata_path, "r", encoding='utf-8') as f:
        metadata = json.load(f)

    # Update fields
    for key, value in metadata_updates.items():
        if value is not None:
            metadata[key] = value

    # Write back
    with open(metadata_path, "w", encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    return True


def get_all_movies():
    """
    Get all movies with their full metadata.

    Returns:
        list: List of movie dictionaries with full metadata
    """
    movies = []

    # Check if database path exists
    if not os.path.exists(DATABASE_PATH):
        return movies

    # Get all movie folders
    for folder in os.listdir(DATABASE_PATH):
        movie_dir = os.path.join(DATABASE_PATH, folder)

        # Skip if not a directory
        if not os.path.isdir(movie_dir):
            continue

        metadata_path = os.path.join(movie_dir, "metadata.json")

        # Skip if no metadata
        if not os.path.exists(metadata_path):
            continue

        try:
            # Read metadata
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            # Return full metadata
            movie_data = {
                "movie_name": folder,
                "title": metadata.get("title", folder),
                "movieIMDbRating": float(metadata.get("movieIMDbRating", 0)),
                "totalRatingCount": int(metadata.get("totalRatingCount", 0)),
                "totalUserReviews": str(metadata.get("totalUserReviews", "0")),
                "totalCriticReviews": str(
                    metadata.get("totalCriticReviews", "0")),
                "metaScore": str(metadata.get("metaScore", "0")),
                "movieGenres": metadata.get("movieGenres", []),
                "directors": metadata.get("directors", []),
                "datePublished": metadata.get("datePublished", ""),
                "creators": metadata.get("creators", []),
                "mainStars": metadata.get("mainStars", []),
                "description": metadata.get("description", ""),
                "duration": int(metadata.get("duration", 0)),
                "total_reviews": int(metadata.get("total_reviews", 0)),
                "average_rating": float(metadata.get("average_rating", 0)),
                "has_poster": os.path.exists(
                    os.path.join(movie_dir, "poster.jpg"))
            }

            movies.append(movie_data)
        except Exception as e:
            print(f"Error reading movie {folder}: {e}")
            continue

    return movies


def get_movie_metadata(movie_name: str):
    """
    Get metadata for a specific movie.

    Args:
        movie_name: Movie folder name

    Returns:
        dict: Movie metadata or None if not found
    """
    folder_path = get_movie_folder(movie_name)

    if not os.path.exists(folder_path):
        return None

    metadata_path = os.path.join(folder_path, "metadata.json")

    if not os.path.exists(metadata_path):
        return None

    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        # Add computed fields
        metadata["movie_name"] = movie_name
        metadata["has_poster"] = os.path.exists(
            os.path.join(folder_path, "poster.jpg"))

        return metadata
    except Exception as e:
        print(f"Error reading metadata for {movie_name}: {e}")
        return None


def movie_exists(movie_name: str):
    """
    Check if a movie exists.

    Args:
        movie_name: Movie folder name

    Returns:
        bool: True if movie exists, False otherwise
    """
    folder_path = get_movie_folder(movie_name)
    return os.path.exists(folder_path)


def delete_movie_folder(movie_name):
    """Deletes the folder and all contents for a movie."""
    folder_path = get_movie_folder(movie_name)
    if not os.path.exists(folder_path):
        raise FileNotFoundError(
            f"Movie folder for '{movie_name}' does not exist."
        )
    # Recursively delete the movie folder and all its contents
    shutil.rmtree(folder_path)
    return f"'{movie_name}' has been deleted."


def save_poster(movie_name: str, poster_data: bytes):
    """
    Save a poster image for a movie.

    Args:
        movie_name: Movie folder name
        poster_data: Binary image data

    Returns:
        bool: True if successful, False if movie doesn't exist
    """
    folder_path = get_movie_folder(movie_name)

    if not os.path.exists(folder_path):
        return False

    poster_path = os.path.join(folder_path, "poster.jpg")
    with open(poster_path, "wb") as f:
        f.write(poster_data)

    return True
