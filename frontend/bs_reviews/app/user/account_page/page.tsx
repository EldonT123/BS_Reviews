"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";

type User = {
  email: string;
  username: string;
  tier: string;
  tier_display_name: string;
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
  const [loading, setLoading] = useState(true);
  const [selectedTier, setSelectedTier] = useState<TierInfo | null>(null);

  useEffect(() => {
    async function checkSession() {
      const sessionId = typeof window !== "undefined" ? localStorage.getItem("sessionId") : null;

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
      } catch (error) {
        console.error("Failed to fetch user info:", error);
        router.push("/login");
      } finally {
        setLoading(false);
      }
    }

    checkSession();
  }, [router]);

  const handleTierClick = (tier: string) => {
    const tierKey = tier.toLowerCase();
    setSelectedTier(TIER_DESCRIPTIONS[tierKey] || null);
  };

  const handleUpgrade = () => {
    router.push("/payment");
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
          <Link href="/user/landing_page">
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
          <Link
            href="/user/account_page"
            className="bg-yellow-400 text-black font-semibold px-4 py-2 rounded hover:bg-yellow-500 transition"
          >
            Account
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <section className="max-w-4xl mx-auto my-12 px-4">
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

          {/* Placeholder Sections */}
          <div className="space-y-8 mt-12">
            <div className="border-t border-gray-600 pt-8">
              <h2 className="text-2xl font-bold text-gray-300 mb-4">
                Reviews (Coming Soon)
              </h2>
              <p className="text-gray-400">
                Your movie reviews will appear here.
              </p>
            </div>

            <div className="border-t border-gray-600 pt-8">
              <h2 className="text-2xl font-bold text-gray-300 mb-4">
                Bookmarks (Coming Soon)
              </h2>
              <p className="text-gray-400">
                Your bookmarked movies will appear here.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}