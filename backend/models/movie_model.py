# models/movie_model.py

# Reformatted to allow for mocking - importing metadata and review service
# when needed instead of overall

from backend.services import metadata_service, review_service


class Movie:

    def __init__(self, name: str):
        self.name = name
        self.metadata = metadata_service.read_metadata(name) or {}
        self.reviews = review_service.read_reviews(name)
        self.average_rating = review_service.recalc_average_rating(name)

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
