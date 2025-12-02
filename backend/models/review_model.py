# backend/models/review_model.py
"""Models for review requests."""
from pydantic import BaseModel

# ==================== Request Models ====================


# This class alows for reviews and ratings to be created.
# In our case, a rating is just a review without any comment.
class ReviewRequest(BaseModel):
    """Model for creating reviews."""
    movie_name: str
    rating: float
    comment: str = ""
    review_title: str = ""
