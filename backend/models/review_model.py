# models/review_model.py
class Review:
    def __init__(self, username: str, rating: float, comment: str):
        self.username = username
        self.rating = rating
        self.comment = comment

    def to_dict(self):
        return {
            "username": self.username,
            "rating": self.rating,
            "comment": self.comment
        }

    def __repr__(self):
        return f"<Review by {self.username}: {self.rating}/5>"
