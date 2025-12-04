"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

type MovieDetails = {
  title: string;
  movieIMDbRating: number;
  totalRatingCount: number;
  totalUserReviews: string;
  totalCriticReviews: string;
  metaScore: string;
  movieGenres: string[];
  directors: string[];
  datePublished: string;
  creators: string[];
  mainStars: string[];
  description: string;
  duration: number;
};

type Review = {
  "Date of Review": string;
  Email: string;
  Username: string;
  Dislikes: string;
  Likes: string;
  "User's Rating out of 10": string;
  "Review Title": string;
  Review: string;
  Reported: string;
  "Report Reason": string;
  "Report Count": string;
  Penalized: string;
  Hidden: string;
  user_tier?: string;
  user_tier_display?: string;
  hasLiked?: boolean;
  hasDisliked?: boolean;
};

export default function MovieDetailsPage() {
  const params = useParams();
  const [movie, setMovie] = useState<MovieDetails | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [displayedReviews, setDisplayedReviews] = useState<Review[]>([]);
  const [reviewsToShow, setReviewsToShow] = useState(5);
  const [loading, setLoading] = useState(true);
  const [reviewsLoading, setReviewsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [voteMessage, setVoteMessage] = useState<string | null>(null);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [reviewForm, setReviewForm] = useState({
    rating: 5,
    reviewTitle: "",
    comment: ""
  });
  const [submitLoading, setSubmitLoading] = useState(false);
  const [userEmail, setUserEmail] = useState<string | null>(null);

  // Check authentication status with backend verification
  useEffect(() => {
    const checkAuth = async () => {
      const sessionId = localStorage.getItem("session_id");
      const email = localStorage.getItem("user_email");
      
      if (!sessionId || !email) {
        setIsAuthenticated(false);
        setUserEmail(null);
        return;
      }

      try {
        const response = await fetch(
          `http://localhost:8000/api/users/check-session/${sessionId}`
        );
        
        if (response.ok) {
          setIsAuthenticated(true);
          setUserEmail(email);
        } else {
          localStorage.removeItem("session_id");
          localStorage.removeItem("user_email");
          setIsAuthenticated(false);
          setUserEmail(null);
        }
      } catch (error) {
        console.error("Error checking session:", error);
        setIsAuthenticated(false);
        setUserEmail(null);
      }
    };
    
    checkAuth();
  }, []);

  // Fetch movie details
  useEffect(() => {
    async function fetchMovieDetails() {
      try {
        const movieTitle = decodeURIComponent(params.title as string);
        const res = await fetch(
          `http://localhost:8000/api/search/title?q=${encodeURIComponent(movieTitle)}`
        );

        if (!res.ok) {
          throw new Error("Failed to fetch movie details");
        }

        const data = await res.json();

        if (data.results && data.results.length > 0) {
          setMovie(data.results[0]);
        } else {
          setError("Movie not found");
        }
      } catch (err) {
        console.error("Error fetching movie:", err);
        setError("Failed to load movie details");
      } finally {
        setLoading(false);
      }
    }

    if (params.title) {
      fetchMovieDetails();
    }
  }, [params.title]);

  // Fetch reviews (without vote status initially)
  useEffect(() => {
    async function fetchReviews() {
      if (!movie?.title) return;

      try {
        setReviewsLoading(true);
        
        const res = await fetch(
          `http://localhost:8000/api/reviews/${encodeURIComponent(movie.title)}`
        );

        if (!res.ok) {
          if (res.status === 404) {
            setReviews([]);
            return;
          }
          throw new Error("Failed to fetch reviews");
        }

        const data = await res.json();
        const visibleReviews = data.reviews.filter((r: Review) => r.Hidden !== "Yes");
        
        setReviews(visibleReviews);
      } catch (err) {
        console.error("Error fetching reviews:", err);
        setReviews([]);
      } finally {
        setReviewsLoading(false);
      }
    }

    fetchReviews();
  }, [movie?.title]);

  // Fetch vote status ONLY for displayed reviews
  useEffect(() => {
    async function fetchVoteStatus() {
      if (!isAuthenticated || reviews.length === 0) {
        setDisplayedReviews(reviews.slice(0, reviewsToShow));
        return;
      }

      const sessionId = localStorage.getItem("session_id");
      const reviewsToDisplay = reviews.slice(0, reviewsToShow);

      const reviewsWithStatus = await Promise.all(
        reviewsToDisplay.map(async (review: Review) => {
          try {
            const statusRes = await fetch(
              `http://localhost:8000/api/reviews/${encodeURIComponent(movie!.title)}/vote-status/${encodeURIComponent(review.Email)}`,
              {
                headers: {
                  Authorization: `Bearer ${sessionId}`,
                },
              }
            );
            
            if (statusRes.ok) {
              const status = await statusRes.json();
              return { 
                ...review, 
                hasLiked: status.has_liked, 
                hasDisliked: status.has_disliked 
              };
            }
          } catch (err) {
            console.error("Error fetching vote status:", err);
          }
          return review;
        })
      );

      setDisplayedReviews(reviewsWithStatus);
    }

    fetchVoteStatus();
  }, [reviews, reviewsToShow, isAuthenticated, movie]);

  const showVoteMessage = (message: string) => {
    setVoteMessage(message);
    setTimeout(() => setVoteMessage(null), 3000);
  };

  const handleLike = async (reviewAuthorEmail: string) => {
    if (!movie?.title) return;
    
    const sessionId = localStorage.getItem("session_id");
    
    if (!sessionId || !isAuthenticated) {
      showVoteMessage("Please log in to like reviews");
      return;
    }

    try {
      const res = await fetch(
        `http://localhost:8000/api/reviews/${encodeURIComponent(movie.title)}/like?review_author_email=${encodeURIComponent(reviewAuthorEmail)}`,
        { 
          method: "POST",
          headers: {
            "Authorization": `Bearer ${sessionId}`,
            "Content-Type": "application/json",
          },
        }
      );

      const result = await res.json();

      if (res.ok) {
        setReviews((prev) =>
          prev.map((r) =>
            r.Email === reviewAuthorEmail
              ? { 
                  ...r, 
                  Likes: String(result.likes),
                  Dislikes: String(result.dislikes),
                  hasLiked: true,
                  hasDisliked: false
                }
              : r
          )
        );
        showVoteMessage("Review liked!");
      } else {
        if (res.status === 401) {
          localStorage.removeItem("session_id");
          localStorage.removeItem("user_email");
          setIsAuthenticated(false);
          setUserEmail(null);
          showVoteMessage("Session expired. Please log in again.");
        } else {
          showVoteMessage(result.detail || "Failed to like review");
        }
      }
    } catch (err) {
      console.error("Error liking review:", err);
      showVoteMessage("Error liking review");
    }
  };

  const handleDislike = async (reviewAuthorEmail: string) => {
    if (!movie?.title) return;
    
    const sessionId = localStorage.getItem("session_id");
    
    if (!sessionId || !isAuthenticated) {
      showVoteMessage("Please log in to dislike reviews");
      return;
    }

    try {
      const res = await fetch(
        `http://localhost:8000/api/reviews/${encodeURIComponent(movie.title)}/dislike?review_author_email=${encodeURIComponent(reviewAuthorEmail)}`,
        { 
          method: "POST",
          headers: {
            "Authorization": `Bearer ${sessionId}`,
            "Content-Type": "application/json",
          },
        }
      );

      const result = await res.json();

      if (res.ok) {
        setReviews((prev) =>
          prev.map((r) =>
            r.Email === reviewAuthorEmail
              ? { 
                  ...r, 
                  Likes: String(result.likes),
                  Dislikes: String(result.dislikes),
                  hasLiked: false,
                  hasDisliked: true
                }
              : r
          )
        );
        showVoteMessage("Review disliked!");
      } else {
        if (res.status === 401) {
          localStorage.removeItem("session_id");
          localStorage.removeItem("user_email");
          setIsAuthenticated(false);
          setUserEmail(null);
          showVoteMessage("Session expired. Please log in again.");
        } else {
          showVoteMessage(result.detail || "Failed to dislike review");
        }
      }
    } catch (err) {
      console.error("Error disliking review:", err);
      showVoteMessage("Error disliking review");
    }
  };

  const loadMore = () => {
    setReviewsToShow((prev) => prev + 5);
  };

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!movie?.title) return;
    
    const sessionId = localStorage.getItem("session_id");
    
    if (!sessionId || !isAuthenticated) {
      showVoteMessage("Please log in to submit a review");
      return;
    }

    if (!reviewForm.reviewTitle.trim()) {
      showVoteMessage("Please enter a review title");
      return;
    }

    if (!reviewForm.comment.trim()) {
      showVoteMessage("Please enter a review comment");
      return;
    }

    try {
      setSubmitLoading(true);
      
      const res = await fetch(
        `http://localhost:8000/api/reviews/${encodeURIComponent(movie.title)}`,
        {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${sessionId}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            movie_name: movie.title,
            rating: reviewForm.rating,
            review_title: reviewForm.reviewTitle,
            comment: reviewForm.comment
          })
        }
      );

      const result = await res.json();

      if (res.ok) {
        showVoteMessage(result.message || "Review submitted successfully!");
        
        setReviewForm({
          rating: 5,
          reviewTitle: "",
          comment: ""
        });
        setShowReviewForm(false);
        
        const reviewsRes = await fetch(
          `http://localhost:8000/api/reviews/${encodeURIComponent(movie.title)}`
        );
        if (reviewsRes.ok) {
          const data = await reviewsRes.json();
          const visibleReviews = data.reviews.filter((r: Review) => r.Hidden !== "Yes");
          setReviews(visibleReviews);
        }
      } else {
        showVoteMessage(result.detail || "Failed to submit review");
      }
    } catch (err) {
      console.error("Error submitting review:", err);
      showVoteMessage("Error submitting review");
    } finally {
      setSubmitLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-gray-100 flex items-center justify-center">
        <div className="text-2xl">Loading...</div>
      </div>
    );
  }

  if (error || !movie) {
    return (
      <div className="min-h-screen bg-gray-900 text-gray-100 flex flex-col items-center justify-center">
        <div className="text-2xl text-red-400 mb-4">{error || "Movie not found"}</div>
        <Link
          href="/"
          className="bg-yellow-400 text-black font-semibold px-6 py-3 rounded hover:bg-yellow-500 transition"
        >
          Back to Home
        </Link>
      </div>
    );
  }

  const releaseYear = new Date(movie.datePublished).getFullYear();
  const durationHours = Math.floor(movie.duration / 60);
  const durationMinutes = movie.duration % 60;

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <header className="flex items-center justify-between px-8 py-4 bg-black/90 shadow-md sticky top-0 z-10">
        <Link
          href="/"
          className="text-yellow-400 hover:text-yellow-500 transition text-lg font-semibold"
        >
          ← Back to Home
        </Link>
      </header>

      {voteMessage && (
        <div className="fixed top-20 right-8 bg-yellow-400 text-black px-6 py-3 rounded-lg shadow-lg z-50 animate-fade-in">
          {voteMessage}
        </div>
      )}

      <div className="max-w-6xl mx-auto px-8 py-12">
        <div className="mb-8">
          <h1 className="text-6xl font-bold mb-4">{movie.title}</h1>
          <div className="flex items-center gap-4 text-lg text-gray-300">
            <span>{releaseYear}</span>
            <span>•</span>
            <span>
              {durationHours}h {durationMinutes}m
            </span>
            <span>•</span>
            <div className="flex gap-2">
              {movie.movieGenres.map((genre) => (
                <span
                  key={genre}
                  className="bg-gray-700 px-3 py-1 rounded-full text-sm"
                >
                  {genre}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="bg-gray-800 p-6 rounded-lg">
            <div className="text-yellow-400 text-5xl font-bold mb-2">
              ⭐ {movie.movieIMDbRating.toFixed(1)}
            </div>
            <div className="text-gray-400">
              IMDb Rating
              <div className="text-sm mt-1">
                {movie.totalRatingCount.toLocaleString()} votes
              </div>
            </div>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg">
            <div className="text-green-400 text-5xl font-bold mb-2">
              {movie.metaScore}
            </div>
            <div className="text-gray-400">Metascore</div>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg">
            <div className="text-blue-400 text-3xl font-bold mb-2">
              {movie.totalUserReviews}
            </div>
            <div className="text-gray-400">
              User Reviews
              <div className="text-sm mt-1">
                {movie.totalCriticReviews} Critic Reviews
              </div>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 p-8 rounded-lg mb-8">
          <h2 className="text-3xl font-semibold mb-4">Overview</h2>
          <p className="text-xl text-gray-300 leading-relaxed">{movie.description}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          <div className="bg-gray-800 p-6 rounded-lg">
            <h3 className="text-2xl font-semibold mb-4 text-yellow-400">
              {movie.directors.length > 1 ? "Directors" : "Director"}
            </h3>
            <div className="space-y-2">
              {movie.directors.map((director) => (
                <div key={director} className="text-lg">
                  {director}
                </div>
              ))}
            </div>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg">
            <h3 className="text-2xl font-semibold mb-4 text-yellow-400">
              {movie.creators.length > 1 ? "Writers" : "Writer"}
            </h3>
            <div className="space-y-2">
              {movie.creators.map((creator) => (
                <div key={creator} className="text-lg">
                  {creator}
                </div>
              ))}
            </div>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg md:col-span-2">
            <h3 className="text-2xl font-semibold mb-4 text-yellow-400">Stars</h3>
            <div className="flex flex-wrap gap-4">
              {movie.mainStars.map((star) => (
                <div
                  key={star}
                  className="bg-gray-700 px-6 py-3 rounded-lg text-lg font-medium"
                >
                  {star}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="bg-gray-800 p-8 rounded-lg">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-3xl font-semibold text-yellow-400">
              User Reviews
              {reviews.length > 0 && (
                <span className="text-lg text-gray-400 ml-3">
                  ({reviews.length} {reviews.length === 1 ? "review" : "reviews"})
                </span>
              )}
            </h2>
            
            {isAuthenticated && !showReviewForm && (
              <button
                onClick={() => setShowReviewForm(true)}
                className="bg-yellow-400 text-black font-semibold px-6 py-2 rounded hover:bg-yellow-500 transition"
              >
                Write a Review
              </button>
            )}
          </div>

          {showReviewForm && (
            <div className="bg-gray-700 p-6 rounded-lg mb-6 border-2 border-yellow-400">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-white">Write Your Review</h3>
                <button
                  onClick={() => setShowReviewForm(false)}
                  className="text-gray-400 hover:text-white text-2xl"
                >
                  ×
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Rating: {reviewForm.rating}/10
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="10"
                    step="0.5"
                    value={reviewForm.rating}
                    onChange={(e) => setReviewForm({ ...reviewForm, rating: parseFloat(e.target.value) })}
                    className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer"
                  />
                  <div className="flex justify-between text-xs text-gray-400 mt-1">
                    <span>0</span>
                    <span>10</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Review Title *
                  </label>
                  <input
                    type="text"
                    value={reviewForm.reviewTitle}
                    onChange={(e) => setReviewForm({ ...reviewForm, reviewTitle: e.target.value })}
                    placeholder="Sum up your thoughts in one line"
                    className="w-full px-4 py-2 bg-gray-600 border border-gray-500 rounded text-white placeholder-gray-400 focus:outline-none focus:border-yellow-400"
                    maxLength={100}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Review *
                  </label>
                  <textarea
                    value={reviewForm.comment}
                    onChange={(e) => setReviewForm({ ...reviewForm, comment: e.target.value })}
                    placeholder="Share your detailed thoughts about this movie..."
                    rows={6}
                    className="w-full px-4 py-2 bg-gray-600 border border-gray-500 rounded text-white placeholder-gray-400 focus:outline-none focus:border-yellow-400 resize-none"
                  />
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={handleSubmitReview}
                    disabled={submitLoading}
                    className={`flex-1 bg-yellow-400 text-black font-semibold px-6 py-3 rounded hover:bg-yellow-500 transition ${
                      submitLoading ? "opacity-50 cursor-not-allowed" : ""
                    }`}
                  >
                    {submitLoading ? "Submitting..." : "Submit Review"}
                  </button>
                  <button
                    onClick={() => setShowReviewForm(false)}
                    className="px-6 py-3 bg-gray-600 text-white rounded hover:bg-gray-500 transition"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}

          {!isAuthenticated && (
            <div className="bg-yellow-400/10 border border-yellow-400 text-yellow-400 px-4 py-3 rounded-lg mb-6">
              <p className="text-sm">
                Please log in to write reviews and vote on reviews
              </p>
            </div>
          )}

          {reviewsLoading ? (
            <div className="text-center py-8 text-gray-400">Loading reviews...</div>
          ) : reviews.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              No reviews yet. Be the first to review this movie!
            </div>
          ) : (
            <>
              <div className="space-y-6 max-h-[600px] overflow-y-auto pr-2">
                {displayedReviews.map((review) => (
                  <div
                    key={review.Email}
                    className="bg-gray-700 p-6 rounded-lg border border-gray-600"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-xl font-semibold text-white">
                            {review["Review Title"] || "Untitled Review"}
                          </h3>
                          {review.user_tier_display && (
                            <span className="text-xs bg-yellow-500 text-black px-2 py-1 rounded font-semibold">
                              {review.user_tier_display}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-3 text-sm text-gray-400">
                          <span>{review.Username}</span>
                          <span>•</span>
                          <span>{review["Date of Review"]}</span>
                          <span>•</span>
                          <span className="text-yellow-400 font-semibold">
                            ⭐ {review["User's Rating out of 10"]}/10
                          </span>
                        </div>
                      </div>
                    </div>

                    <p className="text-gray-200 leading-relaxed mb-4">
                      {review.Review}
                    </p>

                    <div className="flex items-center gap-4 pt-3 border-t border-gray-600">
                      <button
                        onClick={() => handleLike(review.Email)}
                        disabled={!isAuthenticated}
                        className={`flex items-center gap-2 px-3 py-2 rounded transition text-sm ${
                          review.hasLiked
                            ? "bg-green-600 text-white"
                            : "bg-gray-600 hover:bg-green-600"
                        } ${!isAuthenticated ? "opacity-50 cursor-not-allowed" : ""}`}
                      >
                        <span>👍</span>
                        <span>{review.Likes || "0"}</span>
                      </button>
                      <button
                        onClick={() => handleDislike(review.Email)}
                        disabled={!isAuthenticated}
                        className={`flex items-center gap-2 px-3 py-2 rounded transition text-sm ${
                          review.hasDisliked
                            ? "bg-red-600 text-white"
                            : "bg-gray-600 hover:bg-red-600"
                        } ${!isAuthenticated ? "opacity-50 cursor-not-allowed" : ""}`}
                      >
                        <span>👎</span>
                        <span>{review.Dislikes || "0"}</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {displayedReviews.length < reviews.length && (
                <div className="text-center mt-6">
                  <button
                    onClick={loadMore}
                    className="bg-yellow-400 text-black font-semibold px-8 py-3 rounded hover:bg-yellow-500 transition"
                  >
                    Load More Reviews
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}