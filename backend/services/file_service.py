# ============================================
# file_service.py (UPDATED)
# ============================================
import os
import json
import csv
import shutil

DATABASE_PATH = "./database/archive"


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
            writer.writerow([
                "Date of Review", "User", "Usefulness Vote",
                "Total Votes", "User's Rating out of 10",
                "Review Title", "Review"
            ])
    return folder_path

def delete_movie_folder(movie_name):
    """Deletes the folder and all contents for a movie."""
    folder_path = get_movie_folder(movie_name)
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Movie folder for '{movie_name}' does not exist.")
    shutil.rmtree(folder_path) # Recursively delete the movie folder and all its contents
    return f"'{movie_name}' has been deleted."
    
