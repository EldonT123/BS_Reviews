"use client";
import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";

interface User {
  email: string;
  username: string;
  tier: string;
  tier_display_name: string;
}

interface ErrorResponse {
  detail?: string;
}

export default function UsersManagementPage() {
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showMakeAdminModal, setShowMakeAdminModal] = useState(false);
  const [newTier, setNewTier] = useState("");
  const [adminPassword, setAdminPassword] = useState("");
  const [processingAction, setProcessingAction] = useState(false);

  const fetchUsers = useCallback(async () => {
    const token = localStorage.getItem("adminToken");

    if (!token) {
      router.push("/admin/login");
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/api/admin/users", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
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

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleUpgradeTier = async () => {
    if (!selectedUser || !newTier) return;

    const token = localStorage.getItem("adminToken");
    setProcessingAction(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/admin/users/upgrade-tier", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          email: selectedUser.email,
          new_tier: newTier,
        }),
      });

      if (!response.ok) {
        const data: ErrorResponse = await response.json();
        throw new Error(data.detail || "Failed to upgrade user");
      }

      setSuccessMessage(`Successfully upgraded ${selectedUser.email} to ${newTier}`);
      setShowUpgradeModal(false);
      setSelectedUser(null);
      setNewTier("");
      fetchUsers();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An error occurred";
      setError(errorMessage);
    } finally {
      setProcessingAction(false);
    }
  };

  const handleDeleteUser = async () => {
    if (!selectedUser) return;

    const token = localStorage.getItem("adminToken");
    setProcessingAction(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/admin/users", {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          email: selectedUser.email,
        }),
      });

      if (!response.ok) {
        const data: ErrorResponse = await response.json();
        throw new Error(data.detail || "Failed to delete user");
      }

      setSuccessMessage(`Successfully deleted user ${selectedUser.email}`);
      setShowDeleteModal(false);
      setSelectedUser(null);
      fetchUsers();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An error occurred";
      setError(errorMessage);
    } finally {
      setProcessingAction(false);
    }
  };

  const handleMakeAdmin = async () => {
    if (!selectedUser || !adminPassword) return;

    setProcessingAction(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/admin/signup", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: selectedUser.email,
          password: adminPassword,
        }),
      });

      if (!response.ok) {
        const data: ErrorResponse = await response.json();
        throw new Error(data.detail || "Failed to create admin");
      }

      setSuccessMessage(`Successfully created admin account for ${selectedUser.email}`);
      setShowMakeAdminModal(false);
      setSelectedUser(null);
      setAdminPassword("");
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An error occurred";
      setError(errorMessage);
    } finally {
      setProcessingAction(false);
    }
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
        <h1 className="text-3xl font-bold text-white mb-2">User Management</h1>
        <p className="text-gray-400">Manage users and their subscription tiers</p>
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

      {/* Users Table */}
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
                <th className="px-6 py-4 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {users.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-gray-400">
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
                        {user.tier_display_name}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => {
                          setSelectedUser(user);
                          setNewTier(user.tier);
                          setShowUpgradeModal(true);
                        }}
                        className="text-blue-400 hover:text-blue-300 mr-4 transition-colors"
                      >
                        Upgrade Tier
                      </button>
                      <button
                        onClick={() => {
                          setSelectedUser(user);
                          setShowMakeAdminModal(true);
                        }}
                        className="text-purple-400 hover:text-purple-300 mr-4 transition-colors"
                      >
                        Make Admin
                      </button>
                      <button
                        onClick={() => {
                          setSelectedUser(user);
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

      {/* Upgrade Tier Modal */}
      {showUpgradeModal && selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full border border-gray-700">
            <h2 className="text-xl font-bold text-white mb-4">Upgrade User Tier</h2>
            <p className="text-gray-400 mb-4">
              Upgrade tier for <strong className="text-white">{selectedUser.email}</strong>
            </p>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Select New Tier
              </label>
              <select
                value={newTier}
                onChange={(e) => setNewTier(e.target.value)}
                className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
              >
                <option value="snail">🐌 Snail (Free)</option>
                <option value="slug">🐛 Slug ($9.99/mo)</option>
                <option value="banana_slug">🌼 Banana Slug ($19.99/mo)</option>
              </select>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowUpgradeModal(false);
                  setSelectedUser(null);
                  setNewTier("");
                }}
                className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                disabled={processingAction}
              >
                Cancel
              </button>
              <button
                onClick={handleUpgradeTier}
                disabled={processingAction || newTier === selectedUser.tier}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
              >
                {processingAction ? "Processing..." : "Upgrade"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Make Admin Modal */}
      {showMakeAdminModal && selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full border border-gray-700">
            <h2 className="text-xl font-bold text-white mb-4">Create Admin Account</h2>
            <p className="text-gray-400 mb-4">
              Create an admin account for{" "}
              <strong className="text-white">{selectedUser.email}</strong>
            </p>
            <p className="text-sm text-yellow-400 mb-6">
              ⚠️ This will create a separate admin account with the same email. Set a password
              for their admin access.
            </p>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Admin Password
              </label>
              <input
                type="password"
                value={adminPassword}
                onChange={(e) => setAdminPassword(e.target.value)}
                placeholder="Enter admin password"
                className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowMakeAdminModal(false);
                  setSelectedUser(null);
                  setAdminPassword("");
                }}
                className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                disabled={processingAction}
              >
                Cancel
              </button>
              <button
                onClick={handleMakeAdmin}
                disabled={processingAction || !adminPassword}
                className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
              >
                {processingAction ? "Creating..." : "Create Admin"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full border border-gray-700">
            <h2 className="text-xl font-bold text-white mb-4">Delete User</h2>
            <p className="text-gray-400 mb-6">
              Are you sure you want to delete{" "}
              <strong className="text-white">{selectedUser.email}</strong>? This action cannot be
              undone.
            </p>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setSelectedUser(null);
                }}
                className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                disabled={processingAction}
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteUser}
                disabled={processingAction}
                className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
              >
                {processingAction ? "Deleting..." : "Delete User"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}