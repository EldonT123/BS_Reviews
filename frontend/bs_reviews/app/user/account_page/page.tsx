"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import TokenBalance from "@/components/TokenBalance";

type User = {
  email: string;
  username: string;
  tier: string;
  tier_display_name: string;
  tokens?: number;
  review_banned?: boolean;
};

type UserReview = {
  "Date of Review": string;
  Email: string;
  Username: string;
  Dislikes: string;
  Likes: string;
  "User's Rating out of 10": string;
  "Review Title": string;
  Review: string;
  movie_name: string;
};

type TierInfo = {
  name: string;
  tier: string;
  emoji: string;
  permissions: string[];
  description?: string;
};

const TIER_DESCRIPTIONS: Record<string, TierInfo> = {
  snail: {
    name: "Snail",
    tier: "snail",
    emoji: "🐌",
    permissions: ["Browse movies", "View reviews", "Read ratings"],
    description: "The free tier. Browse and discover movies with community reviews.",
  },
  slug: {
    name: "Slug",
    tier: "slug",
    emoji: "🐌",
    permissions: [
      "All Snail permissions",
      "Write reviews",
      "Edit own reviews",
      "Rate movies",
    ],
    description: "Write and edit your own reviews. Share your opinions with the community.",
  },
  banana_slug: {
    name: "Banana Slug",
    tier: "banana_slug",
    emoji: "🍌",
    permissions: [
      "All Slug permissions",
      "Reviews appear first",
      "Special cosmetics (coming soon)",
      "VIP status",
    ],
    description: "Premium tier. Your reviews appear first and get more visibility.",
  },
};

export default function AccountPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [userReviews, setUserReviews] = useState<UserReview[]>([]);
  const [bookmarks, setBookmarks] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [reviewsLoading, setReviewsLoading] = useState(true);
  const [bookmarksLoading, setBookmarksLoading] = useState(true);
  const [selectedTier, setSelectedTier] = useState<TierInfo | null>(null);
  const [activeTab, setActiveTab] = useState<"reviews" | "bookmarks">("reviews");

  useEffect(() => {
    async function checkSession() {
      const sessionId = typeof window !== "undefined" ? localStorage.getItem("session_id") : null;

      if (!sessionId) {
        router.push("/login");
        return;
      }

      try {
        const res = await fetch(
          `http://localhost:8000/api/users/check-session/${sessionId}`
        );
        if (!res.ok) {
          router.push("/login");
          return;
        }

        const data = await res.json();
        setUser(data.user);
        
        // Fetch user's reviews and bookmarks
        fetchUserReviews(sessionId);
        fetchBookmarks(data.user.email);
      } catch (error) {
        console.error("Failed to fetch user info:", error);
        router.push("/login");
      } finally {
        setLoading(false);
      }
    }

    checkSession();
  }, [router]);

  async function fetchUserReviews(sessionId: string) {
    try {
      const res = await fetch(
        `http://localhost:8000/api/reviews/user/reviews`,
        {
          headers: {
            Authorization: `Bearer ${sessionId}`,
          },
        }
      );

      if (res.ok) {
        const data = await res.json();
        setUserReviews(data.reviews || []);
      }
    } catch (error) {
      console.error("Failed to fetch user reviews:", error);
    } finally {
      setReviewsLoading(false);
    }
  }

  async function fetchBookmarks(email: string) {
    try {
      const res = await fetch(
        `http://localhost:8000/api/users/bookmarks/${encodeURIComponent(email)}`
      );

      if (res.ok) {
        const data = await res.json();
        setBookmarks(data.bookmarks || []);
      }
    } catch (error) {
      console.error("Failed to fetch bookmarks:", error);
    } finally {
      setBookmarksLoading(false);
    }
  }

  const handleRemoveBookmark = async (movieTitle: string) => {
    if (!user) return;

    try {
      const res = await fetch(
        `http://localhost:8000/api/users/bookmarks/remove`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email: user.email,
            movie_title: movieTitle
          })
        }
      );

      if (res.ok) {
        setBookmarks(prev => prev.filter(b => b !== movieTitle));
      }
    } catch (error) {
      console.error("Failed to remove bookmark:", error);
    }
  };

  const handleTierClick = (tier: string) => {
    const tierKey = tier.toLowerCase();
    setSelectedTier(TIER_DESCRIPTIONS[tierKey] || null);
  };

  const handleUpgrade = () => {
    router.push("/store");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-gray-100 flex items-center justify-center">
        <p>Loading...</p>
      </div>
    );
  }

  if (!user) {
    return null;
  }

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
              className="cursor-pointer"
            />
          </Link>
          <nav className="hidden md:flex space-x-6 text-sm font-semibold uppercase tracking-wider">
            <a href="#" className="hover:text-yellow-400 transition">
              Movies
            </a>
            <a href="#" className="hover:text-yellow-400 transition">
              TV Shows
            </a>
            <a href="#" className="hover:text-yellow-400 transition">
              Celebs
            </a>
            <a href="#" className="hover:text-yellow-400 transition">
              Awards
            </a>
          </nav>
        </div>
        <div className="flex items-center space-x-4">
          <input
            type="search"
            placeholder="Search movies, TV, actors..."
            className="bg-gray-800 text-gray-300 placeholder-gray-500 rounded-md px-4 py-2 focus:outline-yellow-400 focus:ring-1 focus:ring-yellow-400 w-48 sm:w-64"
          />
          <TokenBalance tokens={user.tokens || 0} />
          <Link
            href="/user/account_page"
            className="bg-yellow-400 text-black font-semibold px-4 py-2 rounded hover:bg-yellow-500 transition"
          >
            Account
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <section className="max-w-6xl mx-auto my-12 px-4">
        <div className="bg-gray-800 rounded-lg shadow-lg p-8">
          {/* Header with upgrade button */}
          <div className="flex items-center justify-between mb-8">
            <h1 className="text-4xl font-bold">Account Information</h1>
            <div className="flex items-center space-x-4">
              <Link
                href="/user/account_page/settings_page"
                className="bg-gray-600 text-white font-semibold px-6 py-3 rounded hover:bg-gray-700 transition"
                title="Settings"
              >
                ⚙️ Settings
              </Link>
              <button
                onClick={handleUpgrade}
                className="bg-green-600 text-white font-semibold px-6 py-3 rounded hover:bg-green-700 transition"
              >
                Upgrade Account
              </button>
            </div>
          </div>

          {/* Penalty Notifications */}
          {user.review_banned && (
            <div className="mb-6 bg-red-500/10 border-2 border-red-500 rounded-lg p-6">
              <div className="flex items-start gap-4">
                <div className="text-3xl">⚠️</div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-red-400 mb-2">
                    Review Ban Active
                  </h3>
                  <p className="text-gray-300 mb-2">
                    Your account has been banned from writing reviews due to violations of our community guidelines.
                  </p>
                  <ul className="list-disc list-inside text-gray-400 text-sm space-y-1">
                    <li>You cannot write new reviews</li>
                    <li>You cannot edit existing reviews</li>
                    <li>You cannot rate movies</li>
                    <li>Your existing reviews are hidden</li>
                  </ul>
                  <p className="text-gray-400 text-sm mt-3">
                    If you believe this is an error, please contact support.
                  </p>
                </div>
              </div>
            </div>
          )}
          {/* User Info Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {/* Email Card */}
            <div className="bg-gray-700 rounded-lg p-6">
              <p className="text-gray-400 text-sm mb-2">Email</p>
              <p className="text-xl font-semibold">{user.email}</p>
            </div>

            {/* Username Card */}
            <div className="bg-gray-700 rounded-lg p-6">
              <p className="text-gray-400 text-sm mb-2">Username</p>
              <p className="text-xl font-semibold">{user.username}</p>
            </div>

            {/* Tier Card (Clickable) */}
            <div
              onClick={() => handleTierClick(user.tier)}
              className="bg-yellow-600 rounded-lg p-6 cursor-pointer hover:bg-yellow-700 transition transform hover:scale-105"
            >
              <p className="text-gray-200 text-sm mb-2">Current Tier</p>
              <p className="text-3xl mb-2">
                {TIER_DESCRIPTIONS[user.tier.toLowerCase()]?.emoji || "🐌"}
              </p>
              <p className="text-xl font-semibold">
                {user.tier_display_name}
              </p>
              <p className="text-xs text-gray-100 mt-2">Click to learn more</p>
            </div>
          </div>

          {/* Account Status Card */}
          <div className="bg-gray-700 rounded-lg p-6 mb-8">
            <h3 className="text-xl font-semibold mb-4 text-yellow-400">Account Status</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center justify-between bg-gray-800 rounded p-4">
                <div>
                  <p className="text-gray-400 text-sm">Review Permissions</p>
                  <p className={`text-lg font-semibold ${user.review_banned ? "text-red-400" : "text-green-400"}`}>
                    {user.review_banned ? "Banned" : "Active"}
                  </p>
                </div>
                <div className="text-3xl">
                  {user.review_banned ? "🚫" : "✅"}
                </div>
              </div>
              <div className="flex items-center justify-between bg-gray-800 rounded p-4">
                <div>
                  <p className="text-gray-400 text-sm">Token Balance</p>
                  <p className="text-lg font-semibold text-yellow-400">
                    {user.tokens || 0} tokens
                  </p>
                </div>
                <div className="text-3xl">🪙</div>
              </div>
            </div>
          </div>

          {/* Tier Details Modal */}
          {selectedTier && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
              <div className="bg-gray-800 rounded-lg p-8 max-w-md w-full shadow-xl">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-bold">
                    <span className="text-3xl mr-2">{selectedTier.emoji}</span>
                    {selectedTier.name} Tier
                  </h2>
                  <button
                    onClick={() => setSelectedTier(null)}
                    className="text-gray-400 hover:text-gray-200 text-2xl"
                  >
                    ✕
                  </button>
                </div>

                <p className="text-gray-300 mb-6">{selectedTier.description}</p>

                <div className="mb-6">
                  <h3 className="font-semibold text-yellow-400 mb-3">Permissions:</h3>
                  <ul className="space-y-2">
                    {selectedTier.permissions.map((perm, idx) => (
                      <li key={idx} className="flex items-start">
                        <span className="text-green-400 mr-2">✓</span>
                        <span className="text-gray-300">{perm}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {selectedTier.tier !== "banana_slug" && (
                  <button
                    onClick={handleUpgrade}
                    className="w-full bg-green-600 text-white font-semibold py-2 rounded hover:bg-green-700 transition"
                  >
                    Upgrade to {selectedTier.name}
                  </button>
                )}
                {selectedTier.tier === "banana_slug" && (
                  <p className="text-center text-green-400 font-semibold">
                    You have the premium tier! 🎉
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Tabs */}
          <div className="border-t border-gray-600 pt-8 mt-8">
            <div className="flex gap-4 mb-6">
              <button
                onClick={() => setActiveTab("reviews")}
                className={`px-6 py-3 rounded-lg font-semibold transition ${
                  activeTab === "reviews"
                    ? "bg-yellow-400 text-black"
                    : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                }`}
              >
                Your Reviews ({userReviews.length})
              </button>
              <button
                onClick={() => setActiveTab("bookmarks")}
                className={`px-6 py-3 rounded-lg font-semibold transition ${
                  activeTab === "bookmarks"
                    ? "bg-yellow-400 text-black"
                    : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                }`}
              >
                Bookmarks ({bookmarks.length})
              </button>
            </div>

            {/* Reviews Tab */}
            {activeTab === "reviews" && (
              <div>
                {reviewsLoading ? (
                  <div className="text-center py-8 text-gray-400">
                    Loading your reviews...
                  </div>
                ) : userReviews.length === 0 ? (
                  <div className="bg-gray-700 p-8 rounded-lg text-center">
                    <p className="text-gray-400 mb-4">
                      You haven&apost written any reviews yet.
                    </p>
                    <Link
                      href="/"
                      className="inline-block bg-yellow-400 text-black font-semibold px-6 py-3 rounded hover:bg-yellow-500 transition"
                    >
                      Browse Movies
                    </Link>
                  </div>
                ) : (
                  <div className="grid gap-4">
                    {userReviews.map((review, index) => (
                      <Link
                        key={`${review.movie_name}-${index}`}
                        href={`/movies/${encodeURIComponent(review.movie_name)}`}
                        className="bg-gray-700 p-6 rounded-lg hover:bg-gray-650 transition-colors border border-gray-600 hover:border-yellow-400"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <h3 className="text-xl font-semibold text-yellow-400 mb-1">
                              {review.movie_name}
                            </h3>
                            <h4 className="text-lg font-medium text-white mb-2">
                              {review["Review Title"] || "Untitled Review"}
                            </h4>
                            <div className="flex items-center gap-3 text-sm text-gray-400 mb-3">
                              <span>{review["Date of Review"]}</span>
                              <span>•</span>
                              <span className="text-yellow-400 font-semibold">
                                ⭐ {review["User's Rating out of 10"]}/10
                              </span>
                            </div>
                          </div>
                        </div>

                        <p className="text-gray-300 leading-relaxed mb-4 line-clamp-3">
                          {review.Review}
                        </p>

                        <div className="flex items-center gap-4 pt-3 border-t border-gray-600">
                          <div className="flex items-center gap-2 text-sm text-gray-400">
                            <span>👍</span>
                            <span>{review.Likes || "0"} likes</span>
                          </div>
                          <div className="flex items-center gap-2 text-sm text-gray-400">
                            <span>👎</span>
                            <span>{review.Dislikes || "0"} dislikes</span>
                          </div>
                          <div className="ml-auto text-sm text-yellow-400 font-medium">
                            View & Edit →
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Bookmarks Tab */}
            {activeTab === "bookmarks" && (
              <div>
                {bookmarksLoading ? (
                  <div className="text-center py-8 text-gray-400">
                    Loading your bookmarks...
                  </div>
                ) : bookmarks.length === 0 ? (
                  <div className="bg-gray-700 p-8 rounded-lg text-center">
                    <p className="text-gray-400 mb-4">
                      You haven&apost bookmarked any movies yet.
                    </p>
                    <Link
                      href="/"
                      className="inline-block bg-yellow-400 text-black font-semibold px-6 py-3 rounded hover:bg-yellow-500 transition"
                    >
                      Browse Movies
                    </Link>
                  </div>
                ) : (
                  <div className="grid gap-4">
                    {bookmarks.map((movieTitle, index) => (
                      <div
                        key={`${movieTitle}-${index}`}
                        className="bg-gray-700 p-6 rounded-lg border border-gray-600 hover:border-yellow-400 transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <Link
                            href={`/movies/${encodeURIComponent(movieTitle)}`}
                            className="flex-1 hover:text-yellow-400 transition"
                          >
                            <h3 className="text-xl font-semibold text-white mb-2">
                              {movieTitle}
                            </h3>
                            <p className="text-sm text-gray-400">
                              Click to view movie details
                            </p>
                          </Link>
                          <button
                            onClick={(e) => {
                              e.preventDefault();
                              handleRemoveBookmark(movieTitle);
                            }}
                            className="ml-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition text-sm font-medium"
                          >
                            Remove
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}