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

export default function MovieDetailsPage() {
  const params = useParams();
  const [movie, setMovie] = useState<MovieDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
      {/* Header */}
      <header className="flex items-center justify-between px-8 py-4 bg-black/90 shadow-md sticky top-0 z-10">
        <Link
          href="/"
          className="text-yellow-400 hover:text-yellow-500 transition text-lg font-semibold"
        >
          ← Back to Home
        </Link>
      </header>

      {/* Movie Details Container */}
      <div className="max-w-6xl mx-auto px-8 py-12">
        {/* Title Section */}
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

        {/* Rating Section */}
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

        {/* Description */}
        <div className="bg-gray-800 p-8 rounded-lg mb-8">
          <h2 className="text-3xl font-semibold mb-4">Overview</h2>
          <p className="text-xl text-gray-300 leading-relaxed">{movie.description}</p>
        </div>

        {/* Credits Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Directors */}
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

          {/* Writers */}
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

          {/* Stars */}
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
      </div>
    </div>
  );
}