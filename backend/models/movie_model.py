# models/movie_model.py
from backend.services.metadata_service import read_metadata
from backend.services.review_service import read_reviews, recalc_average_rating

class Movie:
    
    def __init__(self, name: str):
        self.name = name
        self.metadata = read_metadata(name) or {}
        self.reviews = read_reviews(name)
        self.average_rating = recalc_average_rating(name)

    def to_dict(self):
        """Return a dictionary representation for API responses."""
        return {
            "title": self.metadata.get("title", self.name),
            "director": self.metadata.get("director"),
            "genre": self.metadata.get("genre"),
            "year": self.metadata.get("year"),
            "averageRating": self.average_rating,
            "reviewCount": len(self.reviews)
        }

    def __repr__(self):
        return f"<Movie {self.name}: {self.average_rating:.1f}/5>"
