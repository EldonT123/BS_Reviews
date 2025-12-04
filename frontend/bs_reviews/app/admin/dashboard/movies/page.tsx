"use client";
import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";

interface Movie {
  movie_name: string;
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
  total_reviews: number;
  average_rating: number;
  has_poster: boolean;
}

interface ErrorResponse {
  detail?: string;
}

interface FormData {
  movie_name: string;
  title: string;
  imdb_rating: string;
  totalRatingCount: string;
  totalUserReviews: string;
  totalCriticReviews: string;
  metaScore: string;
  movieGenres: string;
  directors: string;
  datePublished: string;
  creators: string;
  mainStars: string;
  description: string;
  duration: string;
}

export default function MoviesManagementPage() {
  const router = useRouter();
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [processingAction, setProcessingAction] = useState(false);

  const [formData, setFormData] = useState<FormData>({
    movie_name: "",
    title: "",
    imdb_rating: "",
    totalRatingCount: "",
    totalUserReviews: "",
    totalCriticReviews: "",
    metaScore: "",
    movieGenres: "",
    directors: "",
    datePublished: "",
    creators: "",
    mainStars: "",
    description: "",
    duration: "",
  });

  const fetchMovies = useCallback(async () => {
    const token = localStorage.getItem("adminToken");

    if (!token) {
      router.push("/admin/login");
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/api/admin/movies", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error("Failed to fetch movies");

      const data = await response.json();
      setMovies(data.movies);
      setLoading(false);
    } catch (error) {
      console.error("Failed to load movies:", error);
      setError("Failed to load movies");
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    fetchMovies();
  }, [fetchMovies]);

  const resetForm = () => {
    setFormData({
      movie_name: "",
      title: "",
      imdb_rating: "",
      totalRatingCount: "",
      totalUserReviews: "",
      totalCriticReviews: "",
      metaScore: "",
      movieGenres: "",
      directors: "",
      datePublished: "",
      creators: "",
      mainStars: "",
      description: "",
      duration: "",
    });
  };

  const handleCreateMovie = async () => {
    if (!formData.movie_name || !formData.title) {
      setError("Movie name and title are required");
      return;
    }

    const token = localStorage.getItem("adminToken");
    setProcessingAction(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/admin/movies", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          movie_name: formData.movie_name,
          title: formData.title,
          imdb_rating: parseFloat(formData.imdb_rating) || 0,
          totalRatingCount: parseInt(formData.totalRatingCount) || 0,
          totalUserReviews: formData.totalUserReviews || "0",
          totalCriticReviews: formData.totalCriticReviews || "0",
          metaScore: formData.metaScore || "0",
          movieGenres: formData.movieGenres
            ? formData.movieGenres.split(",").map(g => g.trim())
            : [],
          directors: formData.directors
            ? formData.directors.split(",").map(d => d.trim())
            : [],
          datePublished: formData.datePublished || "",
          creators: formData.creators
            ? formData.creators.split(",").map(c => c.trim())
            : [],
          mainStars: formData.mainStars
            ? formData.mainStars.split(",").map(s => s.trim())
            : [],
          description: formData.description || "",
          duration: parseInt(formData.duration) || 0,
        }),
      });

      if (!response.ok) {
        const data: ErrorResponse = await response.json();
        throw new Error(data.detail || "Failed to create movie");
      }

      setSuccessMessage(`Successfully created movie "${formData.title}"`);
      setShowCreateModal(false);
      resetForm();
      fetchMovies();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An error occurred";
      setError(errorMessage);
    } finally {
      setProcessingAction(false);
    }
  };

  const handleEditMovie = async () => {
    if (!selectedMovie) return;

    const token = localStorage.getItem("adminToken");
    setProcessingAction(true);
    setError("");

    try {
      const response = await fetch(
        `http://localhost:8000/api/admin/movies/${selectedMovie.movie_name}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            title: formData.title || undefined,
            imdb_rating: formData.imdb_rating ? parseFloat(formData.imdb_rating) : undefined,
            totalRatingCount: formData.totalRatingCount ? parseInt(formData.totalRatingCount) : undefined,
            totalUserReviews: formData.totalUserReviews || undefined,
            totalCriticReviews: formData.totalCriticReviews || undefined,
            metaScore: formData.metaScore || undefined,
            movieGenres: formData.movieGenres
              ? formData.movieGenres.split(",").map(g => g.trim())
              : undefined,
            directors: formData.directors
              ? formData.directors.split(",").map(d => d.trim())
              : undefined,
            datePublished: formData.datePublished || undefined,
            creators: formData.creators
              ? formData.creators.split(",").map(c => c.trim())
              : undefined,
            mainStars: formData.mainStars
              ? formData.mainStars.split(",").map(s => s.trim())
              : undefined,
            description: formData.description || undefined,
            duration: formData.duration ? parseInt(formData.duration) : undefined,
          }),
        }
      );

      if (!response.ok) {
        const data: ErrorResponse = await response.json();
        throw new Error(data.detail || "Failed to update movie");
      }

      setSuccessMessage(`Successfully updated movie "${formData.title}"`);
      setShowEditModal(false);
      setSelectedMovie(null);
      resetForm();
      fetchMovies();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An error occurred";
      setError(errorMessage);
    } finally {
      setProcessingAction(false);
    }
  };

  const handleDeleteMovie = async () => {
    if (!selectedMovie) return;

    const token = localStorage.getItem("adminToken");
    setProcessingAction(true);
    setError("");

    try {
      const response = await fetch(
        `http://localhost:8000/api/admin/movies/${selectedMovie.movie_name}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        const data: ErrorResponse = await response.json();
        throw new Error(data.detail || "Failed to delete movie");
      }

      setSuccessMessage(`Successfully deleted movie "${selectedMovie.title}"`);
      setShowDeleteModal(false);
      setSelectedMovie(null);
      fetchMovies();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An error occurred";
      setError(errorMessage);
    } finally {
      setProcessingAction(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Movie Management</h1>
          <p className="text-gray-400">Add, edit, and manage movies in the database</p>
        </div>
        <button
          onClick={() => {
            resetForm();
            setShowCreateModal(true);
          }}
          className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Movie
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500 rounded-lg">
          <p className="text-red-500">{error}</p>
        </div>
      )}

      {successMessage && (
        <div className="mb-6 p-4 bg-green-500/10 border border-green-500 rounded-lg">
          <p className="text-green-500">{successMessage}</p>
        </div>
      )}

      <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-900">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Title</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Directors</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Genres</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Year</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">IMDb</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Reviews</th>
                <th className="px-6 py-4 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {movies.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-gray-400">
                    No movies found. Add your first movie to get started!
                  </td>
                </tr>
              ) : (
                movies.map((movie) => (
                  <tr key={movie.movie_name} className="hover:bg-gray-700/50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-white font-medium">{movie.title}</div>
                      <div className="text-xs text-gray-400">{movie.movie_name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-300">
                        {movie.directors.length > 0 ? movie.directors.join(", ") : "-"}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-300">
                        {movie.movieGenres.length > 0 ? movie.movieGenres.join(", ") : "-"}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-300">
                        {movie.datePublished ? movie.datePublished.split("-")[0] : "-"}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-yellow-400">⭐ {movie.movieIMDbRating.toFixed(1)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-300">{movie.total_reviews}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => {
                          setSelectedMovie(movie);
                          setFormData({
                            movie_name: movie.movie_name,
                            title: movie.title,
                            imdb_rating: movie.movieIMDbRating.toString(),
                            totalRatingCount: movie.totalRatingCount.toString(),
                            totalUserReviews: movie.totalUserReviews,
                            totalCriticReviews: movie.totalCriticReviews,
                            metaScore: movie.metaScore,
                            movieGenres: movie.movieGenres.join(", "),
                            directors: movie.directors.join(", "),
                            datePublished: movie.datePublished,
                            creators: movie.creators.join(", "),
                            mainStars: movie.mainStars.join(", "),
                            description: movie.description,
                            duration: movie.duration.toString(),
                          });
                          setShowEditModal(true);
                        }}
                        className="text-blue-400 hover:text-blue-300 mr-4 transition-colors"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => {
                          setSelectedMovie(movie);
                          setShowDeleteModal(true);
                        }}
                        className="text-red-400 hover:text-red-300 transition-colors"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-lg p-6 max-w-4xl w-full border border-gray-700 max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold text-white mb-6">Add New Movie</h2>

            <div className="space-y-6">
              <div className="border-b border-gray-700 pb-4">
                <h3 className="text-lg font-semibold text-white mb-4">Basic Information</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Movie Name (folder name) *</label>
                    <input
                      type="text"
                      value={formData.movie_name}
                      onChange={(e) => setFormData({ ...formData, movie_name: e.target.value })}
                      placeholder="e.g., joker-2019"
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                    <p className="text-xs text-gray-400 mt-1">Use lowercase with hyphens</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Title *</label>
                    <input
                      type="text"
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                      placeholder="Joker"
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
                    <textarea
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      placeholder="A mentally troubled stand-up comedian embarks on a downward spiral..."
                      rows={3}
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none resize-none"
                    />
                  </div>
                </div>
              </div>

              <div className="border-b border-gray-700 pb-4">
                <h3 className="text-lg font-semibold text-white mb-4">Ratings & Statistics</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">IMDb Rating (0-10)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={formData.imdb_rating}
                      onChange={(e) => setFormData({ ...formData, imdb_rating: e.target.value })}
                      placeholder="8.4"
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Total Rating Count</label>
                    <input
                      type="number"
                      value={formData.totalRatingCount}
                      onChange={(e) => setFormData({ ...formData, totalRatingCount: e.target.value })}
                      placeholder="1213550"
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Metascore (0-100)</label>
                    <input
                      type="text"
                      value={formData.metaScore}
                      onChange={(e) => setFormData({ ...formData, metaScore: e.target.value })}
                      placeholder="59"
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Duration (minutes)</label>
                    <input
                      type="number"
                      value={formData.duration}
                      onChange={(e) => setFormData({ ...formData, duration: e.target.value })}
                      placeholder="122"
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Total User Reviews</label>
                    <input
                      type="text"
                      value={formData.totalUserReviews}
                      onChange={(e) => setFormData({ ...formData, totalUserReviews: e.target.value })}
                      placeholder="11.3K"
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Total Critic Reviews</label>
                    <input
                      type="text"
                      value={formData.totalCriticReviews}
                      onChange={(e) => setFormData({ ...formData, totalCriticReviews: e.target.value })}
                      placeholder="697"
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                </div>
              </div>

              <div className="pb-4">
                <h3 className="text-lg font-semibold text-white mb-4">Production Details</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Directors (comma-separated)</label>
                    <input
                      type="text"
                      value={formData.directors}
                      onChange={(e) => setFormData({ ...formData, directors: e.target.value })}
                      placeholder="Todd Phillips"
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Creators/Writers (comma-separated)</label>
                    <input
                      type="text"
                      value={formData.creators}
                      onChange={(e) => setFormData({ ...formData, creators: e.target.value })}
                      placeholder="Todd Phillips, Scott Silver, Bob Kane"
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Main Stars (comma-separated)</label>
                    <input
                      type="text"
                      value={formData.mainStars}
                      onChange={(e) => setFormData({ ...formData, mainStars: e.target.value })}
                      placeholder="Joaquin Phoenix, Robert De Niro, Zazie Beetz"
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Genres (comma-separated)</label>
                      <input
                        type="text"
                        value={formData.movieGenres}
                        onChange={(e) => setFormData({ ...formData, movieGenres: e.target.value })}
                        placeholder="Crime, Drama, Thriller"
                        className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Release Date (YYYY-MM-DD)</label>
                      <input
                        type="text"
                        value={formData.datePublished}
                        onChange={(e) => setFormData({ ...formData, datePublished: e.target.value })}
                        placeholder="2019-10-04"
                        className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setShowEditModal(false);
                  setSelectedMovie(null);
                  resetForm();
                }}
                className="flex-1 px-4 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors font-medium"
                disabled={processingAction}
              >
                Cancel
              </button>
              <button
                onClick={handleCreateMovie || handleEditMovie}
                disabled={processingAction || !formData.movie_name || !formData.title}
                className="flex-1 px-4 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-medium"
              >
                {processingAction ? "Creating..." : "Create Movie"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Movie Modal */}
      {showEditModal && selectedMovie && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-lg p-6 max-w-4xl w-full border border-gray-700 max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold text-white mb-6">Edit Movie</h2>

            <div className="space-y-6">
              <div className="border-b border-gray-700 pb-4">
                <h3 className="text-lg font-semibold text-white mb-4">Basic Information</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Movie Name (folder name) *</label>
                    <input
                      type="text"
                      value={formData.movie_name}
                      onChange={(e) => setFormData({ ...formData, movie_name: e.target.value })}
                      placeholder="e.g., joker-2019"
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                    <p className="text-xs text-gray-400 mt-1">Use lowercase with hyphens</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Title *</label>
                    <input
                      type="text"
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                      placeholder="Joker"
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
                    <textarea
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      placeholder="A mentally troubled stand-up comedian embarks on a downward spiral..."
                      rows={3}
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none resize-none"
                    />
                  </div>
                </div>
              </div>

              <div className="border-b border-gray-700 pb-4">
                <h3 className="text-lg font-semibold text-white mb-4">Ratings & Statistics</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">IMDb Rating (0-10)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={formData.imdb_rating}
                      onChange={(e) => setFormData({ ...formData, imdb_rating: e.target.value })}
                      placeholder="8.4"
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Total Rating Count</label>
                    <input
                      type="number"
                      value={formData.totalRatingCount}
                      onChange={(e) => setFormData({ ...formData, totalRatingCount: e.target.value })}
                      placeholder="1213550"
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Metascore (0-100)</label>
                    <input
                      type="text"
                      value={formData.metaScore}
                      onChange={(e) => setFormData({ ...formData, metaScore: e.target.value })}
                      placeholder="59"
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Duration (minutes)</label>
                    <input
                      type="number"
                      value={formData.duration}
                      onChange={(e) => setFormData({ ...formData, duration: e.target.value })}
                      placeholder="122"
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Total User Reviews</label>
                    <input
                      type="text"
                      value={formData.totalUserReviews}
                      onChange={(e) => setFormData({ ...formData, totalUserReviews: e.target.value })}
                      placeholder="11.3K"
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Total Critic Reviews</label>
                    <input
                      type="text"
                      value={formData.totalCriticReviews}
                      onChange={(e) => setFormData({ ...formData, totalCriticReviews: e.target.value })}
                      placeholder="697"
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                </div>
              </div>

              <div className="pb-4">
                <h3 className="text-lg font-semibold text-white mb-4">Production Details</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Directors (comma-separated)</label>
                    <input
                      type="text"
                      value={formData.directors}
                      onChange={(e) => setFormData({ ...formData, directors: e.target.value })}
                      placeholder="Todd Phillips"
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Creators/Writers (comma-separated)</label>
                    <input
                      type="text"
                      value={formData.creators}
                      onChange={(e) => setFormData({ ...formData, creators: e.target.value })}
                      placeholder="Todd Phillips, Scott Silver, Bob Kane"
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Main Stars (comma-separated)</label>
                    <input
                      type="text"
                      value={formData.mainStars}
                      onChange={(e) => setFormData({ ...formData, mainStars: e.target.value })}
                      placeholder="Joaquin Phoenix, Robert De Niro, Zazie Beetz"
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Genres (comma-separated)</label>
                      <input
                        type="text"
                        value={formData.movieGenres}
                        onChange={(e) => setFormData({ ...formData, movieGenres: e.target.value })}
                        placeholder="Crime, Drama, Thriller"
                        className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Release Date (YYYY-MM-DD)</label>
                      <input
                        type="text"
                        value={formData.datePublished}
                        onChange={(e) => setFormData({ ...formData, datePublished: e.target.value })}
                        placeholder="2019-10-04"
                        className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowEditModal(false);
                  setSelectedMovie(null);
                  resetForm();
                }}
                className="flex-1 px-4 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors font-medium"
                disabled={processingAction}
              >
                Cancel
              </button>
              <button
                onClick={handleEditMovie}
                disabled={processingAction || !formData.movie_name || !formData.title}
                className="flex-1 px-4 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-medium"
              >
                {processingAction ? "Updating..." : "Update Movie"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && selectedMovie && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full border border-gray-700">
            <h2 className="text-xl font-bold text-white mb-4">Delete Movie</h2>
            <p className="text-gray-400 mb-6">
              Are you sure you want to delete{" "}
              <strong className="text-white">{selectedMovie.title}</strong>? This will delete all
              reviews and data associated with this movie. This action cannot be undone.
            </p>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setSelectedMovie(null);
                }}
                className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                disabled={processingAction}
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteMovie}
                disabled={processingAction}
                className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
              >
                {processingAction ? "Deleting..." : "Delete Movie"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}