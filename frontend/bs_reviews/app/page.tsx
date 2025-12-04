"use client";
import Image from "next/image";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import TokenBalance from "@/components/TokenBalance";

type User = {
  email: string;
  username: string;
  tier: string;
  tier_display_name: string;
  tokens?: number;
};

type Movie = {
  title: string;
  movieIMDbRating: number;
  posterPath: string;
  commentCount?: number;
};

export default function Home() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [topMovies, setTopMovies] = useState<Movie[]>([]);
  const [mostCommentedMovies, setMostCommentedMovies] = useState<Movie[]>([]);
  const [loadingTop, setLoadingTop] = useState(true);
  const [loadingComments, setLoadingComments] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    async function fetchUserData() {
      const sessionId = typeof window !== "undefined" ? localStorage.getItem("session_id") : null;

      if (sessionId) {
        try {
          const res = await fetch(
            `http://localhost:8000/api/users/check-session/${sessionId}`
          );
          if (res.ok) {
            const data = await res.json();
            setUser(data.user);
          } else {
            // Invalid session, clear it
            localStorage.removeItem("session_id");
          }
        } catch (error) {
          console.error("Failed to fetch user data:", error);
        }
      }
    }

    async function fetchTopMovies() {
      try {
        const res = await fetch("http://localhost:8000/api/movies/top");
        const data = await res.json();
        setTopMovies(data);
      } catch (error) {
        console.error("Failed to fetch top movies:", error);
      } finally {
        setLoadingTop(false);
      }
    }

    async function fetchMostCommentedMovies() {
      try {
        const res = await fetch("http://localhost:8000/api/movies/most_commented");
        const data = await res.json();
        setMostCommentedMovies(data);
      } catch (error) {
        console.error("Failed to fetch most commented movies:", error);
      } finally {
        setLoadingComments(false);
      }
    }

    fetchUserData();
    fetchTopMovies();
    fetchMostCommentedMovies();
  }, []);

  const prevMovie = () => {
    setCurrentIndex((idx) =>
      idx === 0 ? (topMovies.length ? topMovies.length - 1 : 0) : idx - 1
    );
  };

  const nextMovie = () => {
    setCurrentIndex((idx) =>
      idx === topMovies.length - 1 ? 0 : idx + 1
    );
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  const currentMovie = topMovies[currentIndex];

  const upNextMovies = topMovies.length
    ? Array(3)
        .fill(null)
        .map((_, i) => topMovies[(currentIndex + i + 1) % topMovies.length])
    : [];

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 font-sans">
      {/* Header */}
      <header className="flex items-center justify-between px-8 py-4 bg-black/90 shadow-md sticky top-0 z-10">
        <div className="flex items-center space-x-4">
          <Link href="/">
            <Image
              src="/bs_reviews_logo.png"
              alt="BS Reviews Logo"
              width={50}
              height={20}
            />
          </Link>
          <nav className="hidden md:flex space-x-6 text-sm font-semibold uppercase tracking-wider">
            <Link href="/movies" className="hover:text-yellow-400 transition">
              Movies
            </Link>
            <Link href="/users" className="hover:text-yellow-400 transition">
              Users
            </Link>
            <Link href="/reviews" className="hover:text-yellow-400 transition">
              Reviews
            </Link>
          </nav>
        </div>
        <div className="flex items-center space-x-4">
          <form onSubmit={handleSearch} className="relative">
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search movies..."
              className="bg-gray-800 text-gray-300 placeholder-gray-500 rounded-md px-4 py-2 focus:outline-yellow-400 focus:ring-1 focus:ring-yellow-400 w-48 sm:w-64"
            />
            <button
              type="submit"
              className="absolute right-2 top-1/2 -translate-y-1/2 text-yellow-400 hover:text-yellow-500"
            >
              🔍
            </button>
          </form>
          {user ? (
            <>
              <TokenBalance tokens={user.tokens || 0} />
              <Link
                href="/user/account_page"
                className="bg-yellow-400 text-black font-semibold px-4 py-2 rounded hover:bg-yellow-500 transition"
              >
                Account
              </Link>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="bg-gray-700 text-white font-semibold px-4 py-2 rounded hover:bg-gray-600 transition"
              >
                Login
              </Link>
              <Link
                href="/login/signup"
                className="bg-yellow-400 text-black font-semibold px-4 py-2 rounded hover:bg-yellow-500 transition"
              >
                Sign Up
              </Link>
            </>
          )}
        </div>
      </header>

      {/* Banner + Up Next Side Pane */}
      <section className="max-w-7xl mx-auto my-12 px-4 flex gap-6">
        {loadingTop ? (
          // Loading state for the entire banner area
          <div className="flex-shrink-0 w-[70%] h-[520px] bg-gray-800 rounded-lg flex items-center justify-center">
            <p className="text-zinc-400 text-xl">Loading top movies...</p>
          </div>
        ) : (
          // Main Poster Section (70% width)
          <div
            className="relative flex-shrink-0 w-[70%] h-[520px] bg-cover bg-center rounded-lg shadow-lg"
            style={{
              backgroundImage: currentMovie
                ? `url(${currentMovie.posterPath})`
                : "url('/banners/default_banner.jpg')",
            }}
          >
            {/* Left arrow */}
            <button
              onClick={prevMovie}
              className="absolute top-1/2 left-4 z-20 -translate-y-1/2 bg-black/50 rounded-full p-3 hover:bg-black/70 text-3xl select-none"
              aria-label="Previous Movie"
            >
              ◀
            </button>

          {/* Info overlay */}
          <div className="absolute bottom-0 left-0 right-0 bg-black/70 p-8 text-white rounded-b-lg">
            <h1 className="text-5xl font-bold">{currentMovie?.title || "Loading..."}</h1>
            <p className="mt-2 text-xl">
              {currentMovie ? `Rated ${currentMovie.movieIMDbRating.toFixed(1)} ⭐ on IMDb` : ""}
            </p>
            <button
              onClick={() =>
                router.push(
                  `/movies/movie_details_page/${encodeURIComponent(currentMovie?.title || "")}`
                )
              }
              className="mt-6 bg-yellow-400 text-black font-semibold px-8 py-3 rounded hover:bg-yellow-500 transition text-lg"
            >
              Watch Now
            </button>

            {/* Info overlay */}
            <div className="absolute bottom-0 left-0 right-0 bg-black/70 p-8 text-white rounded-b-lg">
              <h1 className="text-5xl font-bold">{currentMovie?.title || "Loading..."}</h1>
              <p className="mt-2 text-xl">
                {currentMovie ? `Rated ${currentMovie.movieIMDbRating.toFixed(1)} ⭐ on IMDb` : ""}
              </p>
              <button className="mt-6 bg-yellow-400 text-black font-semibold px-8 py-3 rounded hover:bg-yellow-500 transition text-lg">
                Watch Now
              </button>
            </div>
          </div>
        )}

        {/* Up Next Pane (30% width) */}
        <aside className="w-[30%] bg-gray-800 p-6 rounded-lg shadow-lg flex flex-col gap-6 overflow-y-auto">
          <h2 className="text-2xl font-semibold text-yellow-400 mb-4">Up Next</h2>
          {loadingTop ? (
            <p className="text-zinc-400">Loading...</p>
          ) : upNextMovies.length === 0 ? (
            <p className="text-zinc-400">No movies to display.</p>
          ) : (
            upNextMovies.map((movie) => (
              <Link
                href={`/movies/${encodeURIComponent(movie.title)}`}
                key={movie.title}
                className="flex items-center gap-4 cursor-pointer hover:bg-gray-700 rounded-md p-2"
              >
                <Image
                  src={movie.posterPath}
                  alt={movie.title}
                  width={80}
                  height={120}
                  className="rounded-md object-cover"
                />
                <div className="text-white">
                  <h3 className="font-semibold">{movie.title}</h3>
                  <p className="text-yellow-400 text-sm">
                    ⭐ {movie.movieIMDbRating.toFixed(1)}
                  </p>
                </div>
              </Link>
            ))
          )}
        </aside>
      </section>

      {/* Most Commented Movies Section */}
      <section className="px-8 py-12 max-w-7xl mx-auto">
        <h2 className="text-2xl font-semibold mb-6">Most Commented Movies</h2>

        {loadingComments ? (
          <p className="text-zinc-400">Loading most commented movies...</p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
            {mostCommentedMovies.map((movie) => (
              <Link
                href={`/movies/${encodeURIComponent(movie.title)}`}
                key={movie.title}
                className="bg-gray-800 rounded-md overflow-hidden shadow-lg hover:shadow-yellow-400 transition-shadow cursor-pointer"
              >
                <Image
                  src={movie.posterPath}
                  alt={`${movie.title} poster`}
                  width={300}
                  height={450}
                  className="object-cover"
                />
                <div className="p-3">
                  <h3 className="font-semibold text-lg">{movie.title}</h3>
                  <p className="text-yellow-400">
                    💬 {movie.commentCount ?? 0} comments
                  </p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}