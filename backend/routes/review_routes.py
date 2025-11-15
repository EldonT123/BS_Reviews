from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.review_service import read_reviews, add_review  # Assuming you have these implemented

router = APIRouter()

class ReviewInput(BaseModel):
    username: str
    rating: float
    comment: str

@router.get("/{movie_name}")
async def get_reviews(movie_name: str):
    reviews = read_reviews(movie_name)
    if reviews is None:
        raise HTTPException(status_code=404, detail="No reviews found")
    return reviews

@router.post("/{movie_name}")
async def post_review(movie_name: str, review: ReviewInput):
    add_review(review.username, movie_name, review.rating, review.comment)
    return {"message": "Review added successfully"}
