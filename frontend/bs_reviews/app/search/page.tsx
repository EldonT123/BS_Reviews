"use client";
import { useEffect, useState, useCallback } from "react";
import { useSearchParams /*useRouter*/ } from "next/navigation";
import Link from "next/link";
import Image from "next/image";

type Movie = {
  title: string;
  movieIMDbRating: number;
  posterPath: string;
  movieGenres: string[];
  datePublished: string;
  description: string;
  duration: number;
};

export default function SearchPage() {
  const searchParams = useSearchParams();
  //const router = useRouter();
  
  const [searchQuery, setSearchQuery] = useState(searchParams.get("q") || "");
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [allGenres, setAllGenres] = useState<string[]>([]);
  
  // Filter states
  const [selectedGenres, setSelectedGenres] = useState<string[]>([]);
  const [minRating, setMinRating] = useState<number | null>(null);
  const [maxRating, setMaxRating] = useState<number | null>(null);
  const [startYear, setStartYear] = useState<string>("");
  const [endYear, setEndYear] = useState<string>("");

  // Fetch all available genres on mount
  useEffect(() => {
    async function fetchGenres() {
      try {
        const res = await fetch("http://localhost:8000/api/search/genres");
        const data = await res.json();
        setAllGenres(data.genres || []);
      } catch (error) {
        console.error("Error fetching genres:", error);
      }
    }
    fetchGenres();
  }, []);

  // Fixed: Added all dependencies to useCallback
  const performSearch = useCallback(async () => {
    setLoading(true);
    try {
      // Build query parameters
      const params = new URLSearchParams();
      
      if (searchQuery.trim()) {
        params.append("title", searchQuery);
      }
      
      selectedGenres.forEach(genre => {
        params.append("genres", genre);
      });
      
      if (minRating !== null) {
        params.append("min_rating", minRating.toString());
      }
      
      if (maxRating !== null) {
        params.append("max_rating", maxRating.toString());
      }
      
      if (startYear) {
        params.append("start_date", `${startYear}-01-01`);
      }
      
      if (endYear) {
        params.append("end_date", `${endYear}-12-31`);
      }

      const res = await fetch(
        `http://localhost:8000/api/search/advanced?${params.toString()}`
      );
      
      if (res.ok) {
        const data = await res.json();
        setMovies(data.results || []);
      } else {
        setMovies([]);
      }
    } catch (error) {
      console.error("Error searching movies:", error);
      setMovies([]);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, selectedGenres, minRating, maxRating, startYear, endYear]);

  // Fixed: Added performSearch to dependencies
  useEffect(() => {
    if (searchQuery.trim()) {
      performSearch();
    }
  }, [searchQuery, selectedGenres, minRating, maxRating, startYear, endYear, performSearch]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch();
  };

  const toggleGenre = (genre: string) => {
    setSelectedGenres(prev => 
      prev.includes(genre) 
        ? prev.filter(g => g !== genre)
        : [...prev, genre]
    );
  };

  const clearFilters = () => {
    setSelectedGenres([]);
    setMinRating(null);
    setMaxRating(null);
    setStartYear("");
    setEndYear("");
  };

  const hasActiveFilters = 
    selectedGenres.length > 0 || 
    minRating !== null || 
    maxRating !== null || 
    startYear !== "" || 
    endYear !== "";

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

      <div className="max-w-7xl mx-auto px-8 py-8">
        {/* Search Bar */}
        <div className="bg-gray-800 p-6 rounded-lg shadow-lg mb-6">
          <form onSubmit={handleSearch} className="flex gap-4">
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search for movies..."
              className="flex-1 bg-gray-700 text-white px-4 py-3 rounded focus:outline-none focus:ring-2 focus:ring-yellow-400"
            />
            <button
              type="submit"
              className="bg-yellow-400 text-black font-semibold px-8 py-3 rounded hover:bg-yellow-500 transition"
            >
              Search
            </button>
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className={`px-6 py-3 rounded font-semibold transition ${
                showFilters || hasActiveFilters
                  ? "bg-yellow-400 text-black"
                  : "bg-gray-700 text-white hover:bg-gray-600"
              }`}
            >
              {showFilters ? "Hide Filters" : "Show Filters"}
              {hasActiveFilters && !showFilters && " (Active)"}
            </button>
          </form>

          {/* Filters Panel */}
          {showFilters && (
            <div className="mt-6 pt-6 border-t border-gray-700 space-y-6">
              {/* Genre Filter */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-yellow-400">Genres</h3>
                  {selectedGenres.length > 0 && (
                    <span className="text-sm text-gray-400">
                      {selectedGenres.length} selected
                    </span>
                  )}
                </div>
                <div className="flex flex-wrap gap-2">
                  {allGenres.map((genre) => (
                    <button
                      key={genre}
                      onClick={() => toggleGenre(genre)}
                      className={`px-4 py-2 rounded-full text-sm font-medium transition ${
                        selectedGenres.includes(genre)
                          ? "bg-yellow-400 text-black"
                          : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                      }`}
                    >
                      {genre}
                    </button>
                  ))}
                </div>
              </div>

              {/* Rating Filter */}
              <div>
                <h3 className="text-lg font-semibold text-yellow-400 mb-3">Rating</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">
                      Minimum Rating
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="10"
                      step="0.1"
                      value={minRating ?? ""}
                      onChange={(e) => setMinRating(e.target.value ? parseFloat(e.target.value) : null)}
                      placeholder="0.0"
                      className="w-full bg-gray-700 text-white px-4 py-2 rounded focus:outline-none focus:ring-2 focus:ring-yellow-400"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">
                      Maximum Rating
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="10"
                      step="0.1"
                      value={maxRating ?? ""}
                      onChange={(e) => setMaxRating(e.target.value ? parseFloat(e.target.value) : null)}
                      placeholder="10.0"
                      className="w-full bg-gray-700 text-white px-4 py-2 rounded focus:outline-none focus:ring-2 focus:ring-yellow-400"
                    />
                  </div>
                </div>
              </div>

              {/* Year Filter */}
              <div>
                <h3 className="text-lg font-semibold text-yellow-400 mb-3">Release Year</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">
                      From Year
                    </label>
                    <input
                      type="number"
                      min="1900"
                      max="2100"
                      value={startYear}
                      onChange={(e) => setStartYear(e.target.value)}
                      placeholder="1900"
                      className="w-full bg-gray-700 text-white px-4 py-2 rounded focus:outline-none focus:ring-2 focus:ring-yellow-400"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">
                      To Year
                    </label>
                    <input
                      type="number"
                      min="1900"
                      max="2100"
                      value={endYear}
                      onChange={(e) => setEndYear(e.target.value)}
                      placeholder="2100"
                      className="w-full bg-gray-700 text-white px-4 py-2 rounded focus:outline-none focus:ring-2 focus:ring-yellow-400"
                    />
                  </div>
                </div>
              </div>

              {/* Clear Filters Button */}
              {hasActiveFilters && (
                <button
                  onClick={clearFilters}
                  className="w-full bg-red-600 text-white font-semibold px-6 py-3 rounded hover:bg-red-700 transition"
                >
                  Clear All Filters
                </button>
              )}
            </div>
          )}
        </div>

        {/* Active Filters Summary */}
        {hasActiveFilters && !showFilters && (
          <div className="bg-gray-800 p-4 rounded-lg mb-6">
            <div className="flex items-center justify-between">
              <div className="flex flex-wrap gap-2">
                <span className="text-sm text-gray-400">Active Filters:</span>
                {selectedGenres.map(genre => (
                  <span key={genre} className="bg-yellow-400 text-black px-3 py-1 rounded-full text-sm font-medium">
                    {genre}
                  </span>
                ))}
                {minRating !== null && (
                  <span className="bg-yellow-400 text-black px-3 py-1 rounded-full text-sm font-medium">
                    Min Rating: {minRating}
                  </span>
                )}
                {maxRating !== null && (
                  <span className="bg-yellow-400 text-black px-3 py-1 rounded-full text-sm font-medium">
                    Max Rating: {maxRating}
                  </span>
                )}
                {startYear && (
                  <span className="bg-yellow-400 text-black px-3 py-1 rounded-full text-sm font-medium">
                    From: {startYear}
                  </span>
                )}
                {endYear && (
                  <span className="bg-yellow-400 text-black px-3 py-1 rounded-full text-sm font-medium">
                    To: {endYear}
                  </span>
                )}
              </div>
              <button
                onClick={clearFilters}
                className="text-red-400 hover:text-red-300 text-sm font-medium"
              >
                Clear All
              </button>
            </div>
          </div>
        )}

        {/* Results */}
        <div className="mb-4">
          <h2 className="text-2xl font-semibold text-white">
            {loading ? "Searching..." : `Found ${movies.length} ${movies.length === 1 ? "movie" : "movies"}`}
          </h2>
          {searchQuery && (
            <p className="text-gray-400 mt-1">
              Search results for: <span className="text-yellow-400 font-medium">{searchQuery}</span>
            </p>
          )}
        </div>

        {/* Movie Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-xl text-gray-400">Loading results...</div>
          </div>
        ) : movies.length === 0 ? (
          <div className="bg-gray-800 p-12 rounded-lg text-center">
            <p className="text-xl text-gray-400 mb-4">No movies found</p>
            <p className="text-gray-500">Try adjusting your search query or filters</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
            {movies.map((movie) => (
              <Link
                key={movie.title}
                href={`/movies/${encodeURIComponent(movie.title)}`}
                className="bg-gray-800 rounded-lg overflow-hidden shadow-lg hover:shadow-yellow-400 hover:scale-105 transition-all duration-200"
              >
                <div className="relative aspect-[2/3] bg-gray-700">
                  {movie.posterPath && movie.posterPath.trim() !== "" ? (
                    <Image
                      src={movie.posterPath}
                      alt={movie.title}
                      fill
                      sizes="(max-width: 640px) 50vw, (max-width: 768px) 33vw, (max-width: 1024px) 25vw, 20vw"
                      className="object-cover"
                      onError={(e) => {
                        // Hide the image if it fails to load
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                  ) : (
                    <div className="absolute inset-0 flex items-center justify-center bg-gray-700">
                      <span className="text-gray-500 text-4xl">🎬</span>
                    </div>
                  )}
                </div>
                <div className="p-3">
                  <h3 className="font-semibold text-sm line-clamp-2 mb-2">
                    {movie.title}
                  </h3>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-yellow-400 font-semibold">
                      ⭐ {movie.movieIMDbRating.toFixed(1)}
                    </span>
                    <span className="text-gray-400">
                      {new Date(movie.datePublished).getFullYear()}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {movie.movieGenres.slice(0, 2).map((genre) => (
                      <span
                        key={genre}
                        className="text-xs bg-gray-700 px-2 py-1 rounded"
                      >
                        {genre}
                      </span>
                    ))}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}