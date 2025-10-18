import os
import json
import csv

# Updated path to include the archive folder
DATABASE_PATH = "./database/archive"

def get_movie_folder(movie_name):
    """
    Returns the folder path for the given movie.
    """
    folder_path = os.path.join(DATABASE_PATH, movie_name)  # Keep spaces as-is
    return folder_path

def check_metadata_exists(movie_name):
    """
    Check if metadata.json exists for a movie.
    """
    folder_path = get_movie_folder(movie_name)
    metadata_path = os.path.join(folder_path, "metadata.json")
    return os.path.exists(metadata_path)

def check_reviews_exists(movie_name):
    """
    Check if movieReviews.csv exists for a movie.
    """
    folder_path = get_movie_folder(movie_name)
    reviews_path = os.path.join(folder_path, "movieReviews.csv")
    return os.path.exists(reviews_path)

def create_movie_folder(movie_name):
    """
    Creates a folder for a movie if it doesn't exist.
    """
    folder_path = get_movie_folder(movie_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        # Optionally, create empty metadata.json and movieReviews.csv
        with open(os.path.join(folder_path, "metadata.json"), "w") as f:
            json.dump({}, f)
        with open(os.path.join(folder_path, "movieReviews.csv"), "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "rating", "comment", "timestamp"])  # CSV header
    return folder_path
