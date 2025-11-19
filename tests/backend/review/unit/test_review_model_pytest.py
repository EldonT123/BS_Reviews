import pytest
from backend.models.review_model import Review


def test_review_to_dict_and_repr():
    review = Review(username="alice", rating=4.5, comment="Loved it!")
    data = review.to_dict()
    
    assert data["username"] == "alice"
    assert data["rating"] == 4.5
    assert data["comment"] == "Loved it!"
    assert repr(review) == "<Review by alice: 4.5/5>"
