"use client";
import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";

type ReportedReview = {
  movie_name: string;
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
};

export default function ReviewsModerationPage() {
  const router = useRouter();
  const [reportedReviews, setReportedReviews] = useState<ReportedReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"count" | "date">("count");

  // Check admin authentication
  useEffect(() => {
    const checkAdminAuth = () => {
      const adminToken = localStorage.getItem("adminToken");
      
      if (!adminToken) {
        router.push("/admin/login");
        return;
      }

      fetchReportedReviews(adminToken);
    };

    checkAdminAuth();
  }, [router]);

  const fetchReportedReviews = useCallback(async (adminToken: string) => {
    try {
      setLoading(true);
      setError(null);

      // Fetch all movies first using the admin endpoint
      const moviesRes = await fetch("http://localhost:8000/api/admin/movies", {
        headers: {
          Authorization: `Bearer ${adminToken}`,
        },
      });
      
      if (!moviesRes.ok) {
        throw new Error("Failed to fetch movies");
      }

      const moviesData = await moviesRes.json();
      const allReportedReviews: ReportedReview[] = [];

      // Fetch reviews for each movie
      for (const movie of moviesData.movies) {
        try {
          const reviewsRes = await fetch(
            `http://localhost:8000/api/reviews/${encodeURIComponent(movie.title)}`
          );

          if (reviewsRes.ok) {
            const reviewsData = await reviewsRes.json();
            
            // Filter for reported reviews only
            const reported = reviewsData.reviews
              .filter((r: ReportedReview) => r.Reported === "Yes")
              .map((r: ReportedReview) => ({
                ...r,
                movie_name: movie.title
              }));

            allReportedReviews.push(...reported);
          }
        } catch (err) {
          console.error(`Error fetching reviews for ${movie.title}:`, err);
        }
      }

      setReportedReviews(allReportedReviews);
    } catch (err) {
      console.error("Error fetching reported reviews:", err);
      setError("Failed to load reported reviews");
    } finally {
      setLoading(false);
    }
  }, []);

  const sortedReviews = [...reportedReviews].sort((a, b) => {
    if (sortBy === "count") {
      return parseInt(b["Report Count"]) - parseInt(a["Report Count"]);
    } else {
      return new Date(b["Date of Review"]).getTime() - new Date(a["Date of Review"]).getTime();
    }
  });

  const totalReports = reportedReviews.reduce(
    (sum, review) => sum + parseInt(review["Report Count"] || "0"),
    0
  );

  const hiddenReviews = reportedReviews.filter(r => r.Hidden === "Yes").length;
  const penalizedReviews = reportedReviews.filter(r => r.Penalized === "Yes").length;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl text-red-400">{error}</div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Review Moderation</h1>
        <p className="text-gray-400">Monitor and manage reported user reviews</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <p className="text-gray-400 text-sm mb-1">Reported Reviews</p>
          <p className="text-3xl font-bold text-white">{reportedReviews.length}</p>
        </div>
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <p className="text-gray-400 text-sm mb-1">Total Reports</p>
          <p className="text-3xl font-bold text-yellow-500">{totalReports}</p>
        </div>
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <p className="text-gray-400 text-sm mb-1">Hidden Reviews</p>
          <p className="text-3xl font-bold text-orange-500">{hiddenReviews}</p>
        </div>
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <p className="text-gray-400 text-sm mb-1">Penalized Users</p>
          <p className="text-3xl font-bold text-red-500">{penalizedReviews}</p>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-4 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <label className="text-gray-400 text-sm">Sort by:</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as "count" | "date")}
              className="bg-gray-700 text-white px-4 py-2 rounded border border-gray-600 focus:outline-none focus:border-purple-500"
            >
              <option value="count">Report Count (High to Low)</option>
              <option value="date">Date (Newest First)</option>
            </select>
          </div>
          <button
            onClick={() => {
              const adminToken = localStorage.getItem("adminToken");
              if (adminToken) fetchReportedReviews(adminToken);
            }}
            className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 transition text-sm font-medium"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Reported Reviews List */}
      {sortedReviews.length === 0 ? (
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-12">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-600 rounded-full mb-4">
              <svg
                className="w-8 h-8 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">No Reported Reviews</h2>
            <p className="text-gray-400">All clear! There are no reported reviews at this time.</p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {sortedReviews.map((review, index) => {
            const reportReasons = review["Report Reason"]
              .split(";")
              .filter(r => r.trim());

            return (
              <div
                key={`${review.movie_name}-${review.Email}-${index}`}
                className={`bg-gray-800 rounded-lg border-2 p-6 ${
                  review.Hidden === "Yes"
                    ? "border-orange-500"
                    : review.Penalized === "Yes"
                    ? "border-red-500"
                    : "border-yellow-500"
                }`}
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-xl font-semibold text-white">
                        {review["Review Title"] || "Untitled Review"}
                      </h3>
                      <span className="text-xs bg-purple-600 text-white px-2 py-1 rounded font-semibold">
                        {review.movie_name}
                      </span>
                      {review.user_tier_display && (
                        <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded font-semibold">
                          {review.user_tier_display}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-sm text-gray-400">
                      <span className="font-medium">{review.Email}</span>
                      <span>•</span>
                      <span>{review.Username}</span>
                      <span>•</span>
                      <span>{review["Date of Review"]}</span>
                      <span>•</span>
                      <span className="text-yellow-400 font-semibold">
                        ⭐ {review["User's Rating out of 10"]}/10
                      </span>
                    </div>
                  </div>

                  {/* Status Badges */}
                  <div className="flex flex-col gap-2 items-end">
                    <div className="flex items-center gap-2 bg-yellow-600 text-white px-3 py-1 rounded font-semibold text-sm">
                      🚩 {review["Report Count"]} {parseInt(review["Report Count"]) === 1 ? "Report" : "Reports"}
                    </div>
                    {review.Hidden === "Yes" && (
                      <div className="bg-orange-600 text-white px-3 py-1 rounded text-xs font-semibold">
                        👁️ HIDDEN
                      </div>
                    )}
                    {review.Penalized === "Yes" && (
                      <div className="bg-red-600 text-white px-3 py-1 rounded text-xs font-semibold">
                        ⚠️ PENALIZED
                      </div>
                    )}
                  </div>
                </div>

                {/* Review Content */}
                <div className="bg-gray-900 rounded p-4 mb-4">
                  <p className="text-gray-200 leading-relaxed">{review.Review}</p>
                </div>

                {/* Engagement Stats */}
                <div className="flex items-center gap-4 mb-4 pb-4 border-b border-gray-700">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-green-500">👍</span>
                    <span className="text-gray-300">{review.Likes} Likes</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-red-500">👎</span>
                    <span className="text-gray-300">{review.Dislikes} Dislikes</span>
                  </div>
                </div>

                {/* Report Reasons */}
                <div>
                  <h4 className="text-sm font-semibold text-gray-300 mb-2">
                    Report Reasons ({reportReasons.length}):
                  </h4>
                  <div className="space-y-2">
                    {reportReasons.map((reason, idx) => (
                      <div
                        key={idx}
                        className="bg-gray-900 border border-gray-700 rounded p-3 text-sm text-gray-300"
                      >
                        <span className="text-orange-400 font-medium">#{idx + 1}:</span> {reason}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}