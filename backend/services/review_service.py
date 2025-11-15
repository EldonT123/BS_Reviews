


# ============================================
# review_service.py (FIXED)
# ============================================
import csv
import os
from datetime import datetime

def read_reviews(movie_name):
    """Read all reviews for a movie from CSV."""
    from backend.services.file_service import get_movie_folder
    
    path = os.path.join(get_movie_folder(movie_name), "movieReviews.csv")
    if not os.path.exists(path):
        return []
    
    with open(path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)

def add_review(username, movie_name, rating, comment, review_title="", date=None):
    """
    Add a new review to the movie's CSV file.
    Appends to existing reviews instead of overwriting.
    """
    from backend.services.file_service import get_movie_folder, create_movie_folder
    
    # Ensure movie folder exists
    movie_folder = get_movie_folder(movie_name)
    if not os.path.exists(movie_folder):
        create_movie_folder(movie_name)
    
    path = os.path.join(movie_folder, "movieReviews.csv")
    
    # Use current date if not provided
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Prepare new review row matching the real CSV structure
    new_review = {
        "Date of Review": date,
        "User": username,
        "Usefulness Vote": "0",
        "Total Votes": "0",
        "User's Rating out of 10": str(rating),
        "Review Title": review_title,
        "Review": comment
    }
    
    # Check if file exists and has content
    file_exists = os.path.exists(path) and os.path.getsize(path) > 0
    
    # CRITICAL: Use 'a' (append) mode, not 'w' (write/overwrite)!
    with open(path, 'a', encoding='utf-8', newline='') as f:
        fieldnames = [
            "Date of Review", "User", "Usefulness Vote", 
            "Total Votes", "User's Rating out of 10", 
            "Review Title", "Review"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        # Only write header if file is empty
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(new_review)

def recalc_average_rating(movie_name):
    """
    Calculate average rating from all reviews.
    Handles empty/invalid ratings gracefully.
    """
    reviews = read_reviews(movie_name)
    if not reviews:
        return 0
    
    # Handle both possible column names
    rating_key = "User's Rating out of 10" if "User's Rating out of 10" in reviews[0] else "rating"
    
    valid_ratings = []
    for review in reviews:
        rating_str = review.get(rating_key, "").strip()
        if rating_str:  # Skip empty strings
            try:
                rating = float(rating_str)
                valid_ratings.append(rating)
            except ValueError:
                # Skip invalid ratings
                continue
    
    if not valid_ratings:
        return 0
    
    return sum(valid_ratings) / len(valid_ratings)


