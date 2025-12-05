"use client";
import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";

interface User {
  email: string;
  username: string;
  tier: string;
  tier_display: string;
  tokens: number;
  review_banned: boolean;
}

interface BannedEmail {
  email: string;
  banned_date: string;
  banned_by: string;
  reason: string;
}

interface ErrorResponse {
  detail?: string;
}

type PenaltyType = "tokens" | "review_ban" | "full_ban" | null;

export default function PenaltiesManagementPage() {
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [bannedEmails, setBannedEmails] = useState<BannedEmail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showPenaltyModal, setShowPenaltyModal] = useState(false);
  const [penaltyType, setPenaltyType] = useState<PenaltyType>(null);
  const [processingAction, setProcessingAction] = useState(false);
  const [activeTab, setActiveTab] = useState<"users" | "banned">("users");

  // Token penalty state
  const [tokensToRemove, setTokensToRemove] = useState<number>(0);

  // Ban penalty state
  const [banReason, setBanReason] = useState("");

  const fetchUsers = useCallback(async () => {
    const token = localStorage.getItem("adminToken");
    if (!token) {
      router.push("/admin/login");
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/api/admin/users", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) throw new Error("Failed to fetch users");
      const data = await response.json();
      setUsers(data.users);
      setLoading(false);
    } catch (error) {
      console.error("Failed to load users:", error);
      setError("Failed to load users");
      setLoading(false);
    }
  }, [router]);

  const fetchBannedEmails = useCallback(async () => {
    const token = localStorage.getItem("adminToken");
    if (!token) return;

    try {
      const response = await fetch("http://localhost:8000/api/admin/users/banned", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) throw new Error("Failed to fetch banned emails");
      const data = await response.json();
      setBannedEmails(data.banned_emails || []);
    } catch (error) {
      console.error("Failed to load banned emails:", error);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
    fetchBannedEmails();
  }, [fetchUsers, fetchBannedEmails]);

  const handleRemoveTokens = async () => {
    if (!selectedUser || tokensToRemove <= 0) return;

    const token = localStorage.getItem("adminToken");
    setProcessingAction(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/admin/users/remove-tokens", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          email: selectedUser.email,
          tokens_to_remove: tokensToRemove,
        }),
      });

      if (!response.ok) {
        const data: ErrorResponse = await response.json();
        throw new Error(data.detail || "Failed to remove tokens");
      }

      const result = await response.json();
      setSuccessMessage(
        `Removed ${tokensToRemove} tokens from ${selectedUser.email}. New balance: ${result.new_balance}`
      );
      closeModal();
      fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setProcessingAction(false);
    }
  };

  const handleReviewBan = async (ban: boolean) => {
    if (!selectedUser) return;

    const token = localStorage.getItem("adminToken");
    setProcessingAction(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/admin/users/review-ban", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          email: selectedUser.email,
          ban: ban,
        }),
      });

      if (!response.ok) {
        const data: ErrorResponse = await response.json();
        throw new Error(data.detail || "Failed to update review ban status");
      }

      const result = await response.json();
      setSuccessMessage(result.message);
      closeModal();
      fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setProcessingAction(false);
    }
  };

  const handleFullBan = async () => {
    if (!selectedUser) return;

    const token = localStorage.getItem("adminToken");
    setProcessingAction(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/admin/users/ban", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          email: selectedUser.email,
          reason: banReason,
        }),
      });

      if (!response.ok) {
        const data: ErrorResponse = await response.json();
        throw new Error(data.detail || "Failed to ban user");
      }

      const result = await response.json();
      setSuccessMessage(result.message);
      closeModal();
      fetchUsers();
      fetchBannedEmails();
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setProcessingAction(false);
    }
  };

  const handleUnban = async (email: string) => {
    const token = localStorage.getItem("adminToken");
    setProcessingAction(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/admin/users/unban", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        const data: ErrorResponse = await response.json();
        throw new Error(data.detail || "Failed to unban user");
      }

      const result = await response.json();
      setSuccessMessage(result.message);
      fetchBannedEmails();
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setProcessingAction(false);
    }
  };

  const openPenaltyModal = (user: User, type: PenaltyType) => {
    setSelectedUser(user);
    setPenaltyType(type);
    setShowPenaltyModal(true);
    setTokensToRemove(0);
    setBanReason("");
  };

  const closeModal = () => {
    setShowPenaltyModal(false);
    setSelectedUser(null);
    setPenaltyType(null);
    setTokensToRemove(0);
    setBanReason("");
  };

  const getTierBadgeColor = (tier: string) => {
    switch (tier) {
      case "snail":
        return "bg-gray-600 text-gray-100";
      case "slug":
        return "bg-blue-600 text-blue-100";
      case "banana_slug":
        return "bg-yellow-600 text-yellow-100";
      default:
        return "bg-gray-600 text-gray-100";
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
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Penalties Management</h1>
        <p className="text-gray-400">Apply and manage user penalties</p>
      </div>

      {/* Messages */}
      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500 rounded-lg">
          <p className="text-red-500">{error}</p>
          <button
            onClick={() => setError("")}
            className="mt-2 text-sm text-red-400 hover:text-red-300"
          >
            Dismiss
          </button>
        </div>
      )}

      {successMessage && (
        <div className="mb-6 p-4 bg-green-500/10 border border-green-500 rounded-lg">
          <p className="text-green-500">{successMessage}</p>
          <button
            onClick={() => setSuccessMessage("")}
            className="mt-2 text-sm text-green-400 hover:text-green-300"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Tabs */}
      <div className="mb-6 flex gap-4 border-b border-gray-700">
        <button
          onClick={() => setActiveTab("users")}
          className={`pb-4 px-4 font-medium transition-colors ${
            activeTab === "users"
              ? "text-purple-400 border-b-2 border-purple-400"
              : "text-gray-400 hover:text-gray-300"
          }`}
        >
          Active Users
        </button>
        <button
          onClick={() => setActiveTab("banned")}
          className={`pb-4 px-4 font-medium transition-colors ${
            activeTab === "banned"
              ? "text-purple-400 border-b-2 border-purple-400"
              : "text-gray-400 hover:text-gray-300"
          }`}
        >
          Banned Users ({bannedEmails.length})
        </button>
      </div>

      {/* Active Users Table */}
      {activeTab === "users" && (
        <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-900">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Username
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Tier
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Tokens
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Review Status
                  </th>
                  <th className="px-6 py-4 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {users.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-gray-400">
                      No users found
                    </td>
                  </tr>
                ) : (
                  users.map((user) => (
                    <tr key={user.email} className="hover:bg-gray-700/50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-white">{user.email}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-300">{user.username}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getTierBadgeColor(
                            user.tier
                          )}`}
                        >
                          {user.tier_display}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-300">{user.tokens}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {user.review_banned ? (
                          <span className="px-2 py-1 text-xs bg-red-500/20 text-red-400 rounded">
                            Banned
                          </span>
                        ) : (
                          <span className="px-2 py-1 text-xs bg-green-500/20 text-green-400 rounded">
                            Active
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => openPenaltyModal(user, "tokens")}
                            className="px-3 py-1 bg-orange-600 hover:bg-orange-700 text-white rounded transition-colors text-xs"
                            title="Remove tokens"
                          >
                            Remove Tokens
                          </button>
                          <button
                            onClick={() => openPenaltyModal(user, "review_ban")}
                            className={`px-3 py-1 ${
                              user.review_banned
                                ? "bg-green-600 hover:bg-green-700"
                                : "bg-yellow-600 hover:bg-yellow-700"
                            } text-white rounded transition-colors text-xs`}
                            title={user.review_banned ? "Unban reviews" : "Ban reviews"}
                          >
                            {user.review_banned ? "Unban Reviews" : "Ban Reviews"}
                          </button>
                          <button
                            onClick={() => openPenaltyModal(user, "full_ban")}
                            className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded transition-colors text-xs"
                            title="Permanently ban user"
                          >
                            Ban User
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Banned Users Table */}
      {activeTab === "banned" && (
        <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-900">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Banned Date
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Banned By
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Reason
                  </th>
                  <th className="px-6 py-4 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {bannedEmails.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-gray-400">
                      No banned users
                    </td>
                  </tr>
                ) : (
                  bannedEmails.map((banned) => (
                    <tr key={banned.email} className="hover:bg-gray-700/50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-white">{banned.email}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-300">
                          {new Date(banned.banned_date).toLocaleDateString()}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-300">{banned.banned_by}</div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-300">
                          {banned.reason || "No reason provided"}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <button
                          onClick={() => handleUnban(banned.email)}
                          disabled={processingAction}
                          className="px-3 py-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white rounded transition-colors text-xs"
                        >
                          Unban
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Penalty Modal */}
      {showPenaltyModal && selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full border border-gray-700">
            {/* Token Removal */}
            {penaltyType === "tokens" && (
              <>
                <h2 className="text-xl font-bold text-white mb-4">Remove Tokens</h2>
                <p className="text-gray-400 mb-4">
                  Remove tokens from <strong className="text-white">{selectedUser.email}</strong>
                </p>
                <p className="text-sm text-gray-500 mb-4">
                  Current balance: <strong>{selectedUser.tokens} tokens</strong>
                </p>

                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Tokens to Remove
                  </label>
                  <input
                    type="number"
                    min="1"
                    max={selectedUser.tokens}
                    value={tokensToRemove}
                    onChange={(e) => setTokensToRemove(parseInt(e.target.value) || 0)}
                    className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-orange-500"
                    placeholder="Enter amount"
                  />
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={closeModal}
                    className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                    disabled={processingAction}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleRemoveTokens}
                    disabled={processingAction || tokensToRemove <= 0 || tokensToRemove > selectedUser.tokens}
                    className="flex-1 px-4 py-2 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                  >
                    {processingAction ? "Processing..." : "Remove Tokens"}
                  </button>
                </div>
              </>
            )}

            {/* Review Ban/Unban */}
            {penaltyType === "review_ban" && (
              <>
                <h2 className="text-xl font-bold text-white mb-4">
                  {selectedUser.review_banned ? "Unban Reviews" : "Ban Reviews"}
                </h2>
                <p className="text-gray-400 mb-6">
                  {selectedUser.review_banned ? (
                    <>
                      Restore review privileges for{" "}
                      <strong className="text-white">{selectedUser.email}</strong>?
                    </>
                  ) : (
                    <>
                      Ban <strong className="text-white">{selectedUser.email}</strong> from writing
                      reviews? This will:
                      <ul className="list-disc list-inside mt-2 space-y-1">
                        <li>Prevent them from writing new reviews</li>
                        <li>Prevent them from rating movies</li>
                        <li>Mark all existing reviews as penalized</li>
                        <li>Hide all their reviews</li>
                      </ul>
                    </>
                  )}
                </p>

                <div className="flex gap-3">
                  <button
                    onClick={closeModal}
                    className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                    disabled={processingAction}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => handleReviewBan(!selectedUser.review_banned)}
                    disabled={processingAction}
                    className={`flex-1 px-4 py-2 ${
                      selectedUser.review_banned
                        ? "bg-green-600 hover:bg-green-700"
                        : "bg-yellow-600 hover:bg-yellow-700"
                    } disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors`}
                  >
                    {processingAction ? "Processing..." : selectedUser.review_banned ? "Unban" : "Ban Reviews"}
                  </button>
                </div>
              </>
            )}

            {/* Full Ban */}
            {penaltyType === "full_ban" && (
              <>
                <h2 className="text-xl font-bold text-white mb-4">⚠️ Permanent Ban</h2>
                <p className="text-gray-400 mb-4">
                  Permanently ban <strong className="text-white">{selectedUser.email}</strong>?
                </p>
                <div className="mb-4 p-3 bg-red-500/10 border border-red-500 rounded-lg">
                  <p className="text-red-400 text-sm font-medium mb-2">This action will:</p>
                  <ul className="list-disc list-inside text-red-300 text-sm space-y-1">
                    <li>Add email to permanent blacklist</li>
                    <li>Delete user account completely</li>
                    <li>Revoke all active sessions</li>
                    <li>Mark all reviews as penalized</li>
                    <li>Prevent future signups with this email</li>
                  </ul>
                </div>

                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Ban Reason (Optional)
                  </label>
                  <textarea
                    value={banReason}
                    onChange={(e) => setBanReason(e.target.value)}
                    className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-red-500 resize-none"
                    rows={3}
                    placeholder="Enter reason for ban..."
                  />
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={closeModal}
                    className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                    disabled={processingAction}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleFullBan}
                    disabled={processingAction}
                    className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                  >
                    {processingAction ? "Banning..." : "Permanently Ban User"}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}