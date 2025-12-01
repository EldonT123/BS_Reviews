"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);

  // Password validation logic
  const validatePassword = (pw: string) => {
    return {
      hasMinLength: pw.length >= 8,
      hasUpper: /[A-Z]/.test(pw),
      hasLower: /[a-z]/.test(pw),
      hasNumber: /[0-9]/.test(pw),
      hasSpecial: /[^A-Za-z0-9]/.test(pw),
    };
  };

  const checks = validatePassword(password);
  const isPasswordValid = Object.values(checks).every(Boolean);
  const passwordsMatch = confirm === "" || password === confirm;

  // Handle signup submit
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isPasswordValid || !passwordsMatch) return;

    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/api/users/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        alert(data.detail || "Signup failed");
        return;
      }

      alert("Signup successful! Please log in.");
      router.push("/login");
    } catch (error) {
      console.error("Signup error:", error);
      alert("Signup failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      {/* Header Home Button */}
      <Link
        href="/"
        className="absolute top-4 left-4 bg-gray-200 text-black text-sm px-3 py-1 rounded-md 
        hover:bg-gray-300 border border-gray-400"
      >
        Home
      </Link>

      <div className="w-full max-w-md">
        <h1 className="text-4xl font-bold mb-8 text-center">Sign Up</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Email input */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-2">
              Email
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full p-2 border rounded-md"
              required
            />
          </div>

          {/* Password input */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium mb-2">
              Password
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-2 border rounded-md"
              required
            />

            {password && (
              <ul className="text-sm mt-2 space-y-1">
                <li className={checks.hasMinLength ? "text-green-600" : "text-red-500"}>
                  • At least 8 characters
                </li>
                <li className={checks.hasUpper ? "text-green-600" : "text-red-500"}>
                  • Contains uppercase letter
                </li>
                <li className={checks.hasLower ? "text-green-600" : "text-red-500"}>
                  • Contains lowercase letter
                </li>
                <li className={checks.hasNumber ? "text-green-600" : "text-red-500"}>
                  • Contains a number
                </li>
                <li className={checks.hasSpecial ? "text-green-600" : "text-red-500"}>
                  • Contains a special character
                </li>
              </ul>
            )}
          </div>

          {/* Confirm password */}
          <div>
            <label htmlFor="confirm" className="block text-sm font-medium mb-2">
              Confirm Password
            </label>
            <input
              type="password"
              id="confirm"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              className="w-full p-2 border rounded-md"
              required
            />
            {confirm && !passwordsMatch && (
              <p className="text-red-500 text-sm mt-1">Passwords do not match</p>
            )}
          </div>

          {/* Submit button */}
          <button
            type="submit"
            disabled={!isPasswordValid || !passwordsMatch || loading}
            className={`w-full p-2 rounded-md text-white ${
              isPasswordValid && passwordsMatch && !loading
                ? "bg-green-600 hover:bg-green-700"
                : "bg-gray-400 cursor-not-allowed"
            }`}
          >
            {loading ? "Signing up..." : "Sign Up"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm">
          Already have an account?{" "}
          <Link href="/login" className="text-blue-600 hover:underline">
            Login
          </Link>
        </p>
      </div>
    </main>
  );
}
