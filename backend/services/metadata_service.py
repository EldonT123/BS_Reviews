# =====================
# metadata_service.py
# =====================
import json
import os


def read_metadata(movie_name):
    """Read metadata.json for a movie."""
    from backend.services.file_service import get_movie_folder

    path = os.path.join(get_movie_folder(movie_name), "metadata.json")

    if not os.path.exists(path):
        return {}

    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_metadata(movie_name, metadata_dict):
    """Write metadata.json for a movie."""
    from backend.services.file_service import get_movie_folder

    path = os.path.join(get_movie_folder(movie_name), "metadata.json")

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(metadata_dict, f, indent=2)


def update_average_rating(movie_name, new_average):
    """Update the average rating in metadata."""
    metadata = read_metadata(movie_name)
    metadata["average_rating"] = new_average
    write_metadata(movie_name, metadata)


def update_review_count(movie_name, count):
    """Update the total review count in metadata."""
    metadata = read_metadata(movie_name)
    metadata["total_reviews"] = count
    write_metadata(movie_name, metadata)
