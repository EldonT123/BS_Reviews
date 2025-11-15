# models/user_model.py
from typing import Optional

class User:
    def __init__(self, username: str, is_admin: bool = False):
        self.username = username
        self.is_admin = is_admin

    def add_review(self, movie_name: str, rating: float, comment: str):
        """
        Allows the user to post a review for a movie.
        This delegates actual writing to the review_service.
        """
        from backend.services.review_service import add_review
        add_review(self.username, movie_name, rating, comment)

    def __repr__(self):
        return f"User(username={self.username}, admin={self.is_admin})"
