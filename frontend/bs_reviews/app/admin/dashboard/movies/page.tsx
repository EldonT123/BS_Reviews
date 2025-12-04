"use client";
import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";

interface Movie {
  movie_name: string;
  title: string;
  director: string;
  genre: string;
  year: string;
  movieIMDbRating: number;
  total_reviews: number;
  average_rating: number;
  has_poster: boolean;
}

interface ErrorResponse {
  detail?: string;
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

  // Form states
  const [formData, setFormData] = useState({
    movie_name: "",
    title: "",
    director: "",
    genre: "",
    year: "",
    imdb_rating: "",
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
      director: "",
      genre: "",
      year: "",
      imdb_rating: "",
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
          director: formData.director,
          genre: formData.genre,
          year: formData.year,
          imdb_rating: parseFloat(formData.imdb_rating) || 0,
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
            director: formData.director || undefined,
            genre: formData.genre || undefined,
            year: formData.year || undefined,
            imdb_rating: formData.imdb_rating ? parseFloat(formData.imdb_rating) : undefined,
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
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
          Add Movie
        </button>
      </div>

      {/* Messages */}
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

      {/* Movies Table */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-900">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Title
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Director
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Genre
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Year
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  IMDb Rating
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Reviews
                </th>
                <th className="px-6 py-4 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
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
                      <div className="text-sm text-gray-300">{movie.director || "-"}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-300">{movie.genre || "-"}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-300">{movie.year || "-"}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-yellow-400">
                        ⭐ {movie.movieIMDbRating.toFixed(1)}
                      </div>
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
                            director: movie.director,
                            genre: movie.genre,
                            year: movie.year,
                            imdb_rating: movie.movieIMDbRating.toString(),
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

      {/* Create Movie Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full border border-gray-700 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-white mb-4">Add New Movie</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Movie Name (folder name) *
                </label>
                <input
                  type="text"
                  value={formData.movie_name}
                  onChange={(e) => setFormData({ ...formData, movie_name: e.target.value })}
                  placeholder="e.g., the-matrix-1999"
                  className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
                />
                <p className="text-xs text-gray-400 mt-1">
                  Use lowercase with hyphens (this will be the folder name)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Title *
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="The Matrix"
                  className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Director
                  </label>
                  <input
                    type="text"
                    value={formData.director}
                    onChange={(e) => setFormData({ ...formData, director: e.target.value })}
                    placeholder="Wachowski Sisters"
                    className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Year
                  </label>
                  <input
                    type="text"
                    value={formData.year}
                    onChange={(e) => setFormData({ ...formData, year: e.target.value })}
                    placeholder="1999"
                    className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Genre
                  </label>
                  <input
                    type="text"
                    value={formData.genre}
                    onChange={(e) => setFormData({ ...formData, genre: e.target.value })}
                    placeholder="Sci-Fi, Action"
                    className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    IMDb Rating
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.imdb_rating}
                    onChange={(e) => setFormData({ ...formData, imdb_rating: e.target.value })}
                    placeholder="8.7"
                    className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  resetForm();
                }}
                className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                disabled={processingAction}
              >
                Cancel
              </button>
              <button
                onClick={handleCreateMovie}
                disabled={processingAction || !formData.movie_name || !formData.title}
                className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
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
          <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full border border-gray-700 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-white mb-4">Edit Movie</h2>
            <p className="text-gray-400 mb-4">
              Editing <strong className="text-white">{selectedMovie.title}</strong>
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Title
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Director
                  </label>
                  <input
                    type="text"
                    value={formData.director}
                    onChange={(e) => setFormData({ ...formData, director: e.target.value })}
                    className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Year
                  </label>
                  <input
                    type="text"
                    value={formData.year}
                    onChange={(e) => setFormData({ ...formData, year: e.target.value })}
                    className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Genre
                  </label>
                  <input
                    type="text"
                    value={formData.genre}
                    onChange={(e) => setFormData({ ...formData, genre: e.target.value })}
                    className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    IMDb Rating
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.imdb_rating}
                    onChange={(e) => setFormData({ ...formData, imdb_rating: e.target.value })}
                    className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
                  />
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
                className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                disabled={processingAction}
              >
                Cancel
              </button>
              <button
                onClick={handleEditMovie}
                disabled={processingAction}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
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