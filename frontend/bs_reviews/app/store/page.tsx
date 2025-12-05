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
};

type PurchaseItem = {
  id: string;
  type: "tokens" | "rank" | "cosmetic";
  name: string;
  description: string;
  price_cad?: number;
  price_tokens?: number;
  tokens_received?: number;
  rank_upgrade?: string;
};

const TIER_HIERARCHY = {
  snail: 0,
  slug: 1,
  banana_slug: 2,
};

export default function StorePage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

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
      } catch (error) {
        console.error("Failed to fetch user info:", error);
        router.push("/login");
      } finally {
        setLoading(false);
      }
    }

    checkSession();
  }, [router]);

  const handlePurchase = (item: PurchaseItem) => {
    // Store purchase item in localStorage to pass to payment page
    localStorage.setItem("pendingPurchase", JSON.stringify(item));
    router.push("/store/payment");
  };

  const canPurchaseTier = (tierUpgrade: string): { canPurchase: boolean; message: string } => {
    if (!user) return { canPurchase: false, message: "" };

    const userTierLevel = TIER_HIERARCHY[user.tier.toLowerCase() as keyof typeof TIER_HIERARCHY] ?? -1;
    const upgradeTierLevel = TIER_HIERARCHY[tierUpgrade.toLowerCase() as keyof typeof TIER_HIERARCHY] ?? -1;

    if (userTierLevel === upgradeTierLevel) {
      return { canPurchase: false, message: "You already have this tier" };
    }

    if (userTierLevel > upgradeTierLevel) {
      return { canPurchase: false, message: "You already have a better tier" };
    }

    return { canPurchase: true, message: "" };
  };

  // Token Packages
  const tokenPackages: PurchaseItem[] = [
    {
      id: "tokens_100",
      type: "tokens",
      name: "100 Tokens",
      description: "Small token package",
      price_cad: 4.99,
      tokens_received: 100,
    },
    {
      id: "tokens_500",
      type: "tokens",
      name: "500 Tokens",
      description: "Popular choice - 10% bonus!",
      price_cad: 19.99,
      tokens_received: 500,
    },
    {
      id: "tokens_1000",
      type: "tokens",
      name: "1000 Tokens",
      description: "Best value - 20% bonus!",
      price_cad: 34.99,
      tokens_received: 1000,
    },
  ];

  // Rank Upgrades
  const rankUpgrades: PurchaseItem[] = [
    {
      id: "rank_slug",
      type: "rank",
      name: "Upgrade to Slug",
      description: "Unlock advanced features and priority support",
      price_cad: 9.99,
      price_tokens: 1000,
      rank_upgrade: "slug",
    },
    {
      id: "rank_banana_slug",
      type: "rank",
      name: "Upgrade to Banana Slug",
      description: "Premium tier with exclusive features and profile customization",
      price_cad: 19.99,
      price_tokens: 2000,
      rank_upgrade: "banana_slug",
    },
  ];

  // Cosmetics
  const cosmetics: PurchaseItem[] = [
    {
      id: "cosmetic_profile_frame_gold",
      type: "cosmetic",
      name: "Golden Profile Frame",
      description: "Luxurious gold border for your profile",
      price_tokens: 150,
    },
    {
      id: "cosmetic_profile_frame_silver",
      type: "cosmetic",
      name: "Silver Profile Frame",
      description: "Elegant silver border for your profile",
      price_tokens: 100,
    },
    {
      id: "cosmetic_badge_critic",
      type: "cosmetic",
      name: "Movie Critic Badge",
      description: "Show off your expertise with this exclusive badge",
      price_tokens: 200,
    },
    {
      id: "cosmetic_theme_dark",
      type: "cosmetic",
      name: "Dark Theme Pack",
      description: "Custom dark theme with unique colors",
      price_tokens: 250,
    },
    {
      id: "cosmetic_username_color",
      type: "cosmetic",
      name: "Colored Username",
      description: "Stand out with a custom username color",
      price_tokens: 300,
    },
    {
      id: "cosmetic_animated_avatar",
      type: "cosmetic",
      name: "Animated Avatar Border",
      description: "Animated effects for your profile picture",
      price_tokens: 400,
    },
  ];

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
      <section className="max-w-7xl mx-auto my-12 px-4">
        <div className="mb-8">
          <h1 className="text-5xl font-bold mb-2">Store</h1>
          <p className="text-gray-400 text-lg">
            Purchase tokens, upgrade your rank, or unlock exclusive cosmetics
          </p>
        </div>

        {/* Token Packages */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold mb-6 flex items-center">
            💰 Purchase Tokens
            <span className="ml-3 text-sm text-gray-400 font-normal">
              (Real Money)
            </span>
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {tokenPackages.map((item) => (
              <div
                key={item.id}
                className="bg-gray-800 rounded-lg p-6 border-2 border-gray-700 hover:border-yellow-400 transition"
              >
                <div className="text-center mb-4">
                  <h3 className="text-2xl font-bold mb-2">{item.name}</h3>
                  <p className="text-gray-400 text-sm mb-4">{item.description}</p>
                  <div className="text-4xl font-bold text-yellow-400 mb-2">
                    ${item.price_cad}
                  </div>
                  <div className="text-lg text-gray-300">
                    Get {item.tokens_received} tokens
                  </div>
                </div>
                <button
                  onClick={() => handlePurchase(item)}
                  className="w-full bg-yellow-600 text-white font-semibold py-3 rounded hover:bg-yellow-700 transition"
                >
                  Purchase
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Rank Upgrades */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold mb-6 flex items-center">
            ⬆️ Rank Upgrades
            <span className="ml-3 text-sm text-gray-400 font-normal">
              (Real Money or Tokens)
            </span>
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {rankUpgrades.map((item) => {
              const { canPurchase, message } = canPurchaseTier(item.rank_upgrade || "");
              
              return (
                <div
                  key={item.id}
                  className={`bg-gradient-to-br from-purple-900/50 to-gray-800 rounded-lg p-6 border-2 transition ${
                    canPurchase
                      ? "border-purple-600 hover:border-purple-400"
                      : "border-gray-600 opacity-50"
                  }`}
                  title={!canPurchase ? message : ""}
                >
                  <div className="mb-4">
                    <h3 className="text-2xl font-bold mb-2">{item.name}</h3>
                    <p className="text-gray-300 mb-4">{item.description}</p>
                    {!canPurchase && (
                      <p className="text-yellow-400 text-sm font-semibold mb-3">
                        {message}
                      </p>
                    )}
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-2xl font-bold text-yellow-400">
                          ${item.price_cad}
                        </div>
                        <div className="text-sm text-gray-400">or</div>
                        <div className="text-xl font-bold text-yellow-400">
                          {item.price_tokens} tokens
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handlePurchase({ ...item, price_tokens: undefined })}
                      disabled={!canPurchase}
                      className={`flex-1 font-semibold py-3 rounded transition ${
                        canPurchase
                          ? "bg-yellow-600 text-white hover:bg-yellow-700"
                          : "bg-gray-600 text-gray-400 cursor-not-allowed"
                      }`}
                    >
                      Buy with $
                    </button>
                    <button
                      onClick={() => handlePurchase({ ...item, price_cad: undefined })}
                      disabled={!canPurchase}
                      className={`flex-1 font-semibold py-3 rounded transition ${
                        canPurchase
                          ? "bg-purple-600 text-white hover:bg-purple-700"
                          : "bg-gray-600 text-gray-400 cursor-not-allowed"
                      }`}
                    >
                      Buy with Tokens
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Cosmetics */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold mb-6 flex items-center">
            ✨ Cosmetics
            <span className="ml-3 text-sm text-gray-400 font-normal">
              (Tokens Only)
            </span>
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {cosmetics.map((item) => (
              <div
                key={item.id}
                className="bg-gray-800 rounded-lg p-6 border-2 border-gray-700 hover:border-blue-400 transition"
              >
                <div className="mb-4">
                  <h3 className="text-xl font-bold mb-2">{item.name}</h3>
                  <p className="text-gray-400 text-sm mb-4">{item.description}</p>
                  <div className="text-2xl font-bold text-blue-400">
                    {item.price_tokens} tokens
                  </div>
                </div>
                <button
                  onClick={() => handlePurchase(item)}
                  className="w-full bg-blue-600 text-white font-semibold py-3 rounded hover:bg-blue-700 transition disabled:bg-gray-600 disabled:cursor-not-allowed"
                  disabled={(user.tokens || 0) < (item.price_tokens || 0)}
                >
                  {(user.tokens || 0) < (item.price_tokens || 0)
                    ? "Insufficient Tokens"
                    : "Purchase"}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}