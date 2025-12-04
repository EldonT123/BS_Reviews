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

interface UpdateData {
  current_email: string;
  current_password: string;
  new_email?: string;
  new_username?: string;
  new_password?: string;
}

export default function SettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState<"success" | "error">("success");

  // Current credentials
  const [currentEmail, setCurrentEmail] = useState("");
  const [currentUsername, setCurrentUsername] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");

  // New credentials
  const [newEmail, setNewEmail] = useState("");
  const [newUsername, setNewUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");

  // Profile image
  const [profileImage, setProfileImage] = useState<File | null>(null);
  const [profileImagePreview, setProfileImagePreview] = useState<string>("");

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

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setProfileImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setProfileImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSaveChanges = async () => {
    if (!user) return;

    setSaving(true);
    setMessage("");

    try {
      // Prepare update data
      const updateData: UpdateData = {
        current_email: currentEmail,
        current_password: currentPassword,
      };

      // Add new email if provided
      if (newEmail && newEmail !== currentEmail) {
        updateData.new_email = newEmail;
      }

      // Add new username if provided
      if (newUsername && newUsername !== currentUsername) {
        updateData.new_username = newUsername;
      }

      // Add new password if provided
      if (newPassword) {
        if (newPassword !== confirmNewPassword) {
          setMessageType("error");
          setMessage("New passwords do not match");
          setSaving(false);
          return;
        }
        updateData.new_password = newPassword;
      }

      // Update profile
      const updateRes = await fetch("http://localhost:8000/api/users/update-profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updateData),
      });

      if (!updateRes.ok) {
        const errorData = await updateRes.json();
        setMessageType("error");
        setMessage(errorData.detail || "Failed to update profile");
        setSaving(false);
        return;
      }

      // Update local user state
      const updatedUser = { ...user };
      if (newEmail && newEmail !== currentEmail) {
        updatedUser.email = newEmail;
      }
      if (newUsername && newUsername !== currentUsername) {
        updatedUser.username = newUsername;
      }
      setUser(updatedUser);

      // Upload profile image if Banana Slug and image selected
      if (
        profileImage &&
        user.tier.toLowerCase() === "banana_slug"
      ) {
        const formData = new FormData();
        formData.append("email", newEmail || currentEmail);
        formData.append("profile_image", profileImage);

        const imageRes = await fetch("http://localhost:8000/api/users/upload-profile-image", {
          method: "POST",
          body: formData,
        });

        if (!imageRes.ok) {
          const errorData = await imageRes.json();
          setMessageType("error");
          setMessage(errorData.detail || "Failed to upload profile image");
          setSaving(false);
          return;
        }

        setProfileImage(null);
        setProfileImagePreview("");
      }

      setMessageType("success");
      setMessage("Profile updated successfully!");
      setEditing(false);
      resetForm();
    } catch (error) {
      console.error("Error updating profile:", error);
      setMessageType("error");
      setMessage("An error occurred while updating your profile");
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setEditing(false);
    setMessage("");
    resetForm();
  };

  const resetForm = () => {
    setCurrentEmail("");
    setCurrentUsername("");
    setCurrentPassword("");
    setNewEmail("");
    setNewUsername("");
    setNewPassword("");
    setConfirmNewPassword("");
    setProfileImage(null);
    setProfileImagePreview("");
  };

  const handleEdit = () => {
    if (user) {
      setCurrentEmail(user.email);
      setCurrentUsername(user.username);
      setEditing(true);
    }
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
      <section className="max-w-4xl mx-auto my-12 px-4">
        <div className="bg-gray-800 rounded-lg shadow-lg p-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <h1 className="text-4xl font-bold">Settings</h1>
            <Link
              href="/user/account_page"
              className="text-gray-400 hover:text-gray-200 text-2xl"
            >
              ✕
            </Link>
          </div>

          {/* Success/Error Message */}
          {message && (
            <div
              className={`p-4 rounded-lg mb-6 ${
                messageType === "success"
                  ? "bg-green-900 text-green-200"
                  : "bg-red-900 text-red-200"
              }`}
            >
              {message}
            </div>
          )}

          {/* Settings Content */}
          <div className="space-y-8">
            {/* Email Settings */}
            <div className="border-b border-gray-600 pb-8">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold">Email</h2>
                {!editing && (
                  <button
                    onClick={handleEdit}
                    className="bg-yellow-600 text-white px-4 py-2 rounded hover:bg-yellow-700 transition"
                  >
                    Edit
                  </button>
                )}
              </div>

              {editing ? (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2 text-gray-300">
                      Current Email
                    </label>
                    <input
                      type="email"
                      value={currentEmail}
                      onChange={(e) => setCurrentEmail(e.target.value)}
                      className="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 focus:border-yellow-400 focus:outline-none"
                      disabled
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2 text-gray-300">
                      New Email (Optional)
                    </label>
                    <input
                      type="email"
                      value={newEmail}
                      onChange={(e) => setNewEmail(e.target.value)}
                      placeholder="Leave blank to keep current email"
                      className="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 focus:border-yellow-400 focus:outline-none"
                    />
                  </div>
                </div>
              ) : (
                <p className="text-gray-300 text-lg">{user.email}</p>
              )}
            </div>

            {/* Username Settings */}
            <div className="border-b border-gray-600 pb-8">
              <h2 className="text-2xl font-bold mb-4">Username</h2>
              {editing ? (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2 text-gray-300">
                      Current Username
                    </label>
                    <input
                      type="text"
                      value={currentUsername}
                      onChange={(e) => setCurrentUsername(e.target.value)}
                      className="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 focus:border-yellow-400 focus:outline-none"
                      disabled
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2 text-gray-300">
                      New Username (Optional)
                    </label>
                    <input
                      type="text"
                      value={newUsername}
                      onChange={(e) => setNewUsername(e.target.value)}
                      placeholder="Leave blank to keep current username"
                      minLength={3}
                      className="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 focus:border-yellow-400 focus:outline-none"
                    />
                  </div>
                </div>
              ) : (
                <p className="text-gray-300 text-lg">{user.username}</p>
              )}
            </div>

            {/* Password Settings */}
            {editing && (
              <div className="border-b border-gray-600 pb-8">
                <h2 className="text-2xl font-bold mb-4">Password</h2>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2 text-gray-300">
                      Current Password (Required)
                    </label>
                    <input
                      type="password"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      placeholder="Enter your current password"
                      className="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 focus:border-yellow-400 focus:outline-none"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2 text-gray-300">
                      New Password (Optional)
                    </label>
                    <input
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="Leave blank to keep current password"
                      className="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 focus:border-yellow-400 focus:outline-none"
                    />
                  </div>
                  {newPassword && (
                    <div>
                      <label className="block text-sm font-medium mb-2 text-gray-300">
                        Confirm New Password
                      </label>
                      <input
                        type="password"
                        value={confirmNewPassword}
                        onChange={(e) => setConfirmNewPassword(e.target.value)}
                        placeholder="Confirm your new password"
                        className="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 focus:border-yellow-400 focus:outline-none"
                      />
                      {confirmNewPassword !== newPassword && (
                        <p className="text-red-400 text-sm mt-2">Passwords do not match</p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Profile Image Settings (Banana Slug only) */}
            {user.tier.toLowerCase() === "banana_slug" && editing && (
              <div className="border-b border-gray-600 pb-8">
                <h2 className="text-2xl font-bold mb-4">
                  Profile Image
                  <span className="ml-2 text-sm text-yellow-400">
                    (Premium Feature)
                  </span>
                </h2>

                <div className="space-y-4">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      {profileImagePreview ? (
                        <Image
                          src={profileImagePreview}
                          alt="Preview"
                          width={96}
                          height={96}
                          className="rounded-lg object-cover"
                        />
                      ) : (
                        <div className="w-24 h-24 bg-gray-700 rounded-lg flex items-center justify-center">
                          <span className="text-gray-400">No image</span>
                        </div>
                      )}
                    </div>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleImageChange}
                      className="bg-gray-700 text-gray-300 p-2 rounded-lg cursor-pointer"
                    />
                  </div>
                  <p className="text-gray-400 text-sm">
                    Accepted formats: JPG, PNG, GIF (Max 5MB)
                  </p>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            {editing && (
              <div className="pt-8">
                <div className="bg-yellow-900/30 border border-yellow-700 rounded-lg p-4 mb-4">
                  <p className="text-yellow-200 text-sm">
                    ⚠️ <strong>Important:</strong> Changing your user information will sign you out. You&apos;ll need to sign in again with your updated credentials.
                  </p>
                </div>
                <div className="flex space-x-4">
                  <button
                    onClick={handleSaveChanges}
                    disabled={saving || !currentPassword}
                    className="flex-1 bg-green-600 text-white font-semibold py-3 rounded hover:bg-green-700 transition disabled:bg-gray-600"
                  >
                    {saving ? "Saving..." : "Save Changes"}
                  </button>
                  <button
                    onClick={handleCancel}
                    disabled={saving}
                    className="flex-1 bg-gray-600 text-white font-semibold py-3 rounded hover:bg-gray-700 transition disabled:bg-gray-700"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
