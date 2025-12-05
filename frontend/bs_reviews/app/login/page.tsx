"use client";
import { useState } from 'react';
import Link from "next/link";
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/users/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const data = await response.json();
        alert(data.detail || "Login failed");
        setLoading(false);
        return;
      }

      const data = await response.json();
      
      // Save session_id to localStorage
      localStorage.setItem("session_id", data.session_id);
      localStorage.setItem("user_email", data.user.email);
      
      // Redirect to home page (which now has full functionality)
      router.push("/");
    } catch {
      alert("Login error, please try again.");
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-900">
      {/* Header Home Button */}
      <Link
        href="/"
        className="absolute top-4 left-4 bg-gray-700 text-white text-sm px-3 py-1 rounded-md 
        hover:bg-gray-600 border border-gray-600"
      >
        Home
      </Link>
    
      <div className="w-full max-w-md">
        <h1 className="text-4xl font-bold mb-8 text-center text-white">Login</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Email fill out Section */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-2 text-gray-200">
              Email
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full p-2 border border-gray-600 rounded-md bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          {/* Password fill out Section */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium mb-2 text-gray-200">
              Password
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-2 border border-gray-600 rounded-md bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className={`w-full p-2 rounded-md text-white ${
              loading ? "bg-gray-600 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
          <Link
            href="/login/signup"
            className="block w-full text-center bg-gray-700 text-blue-400 p-2 rounded-md hover:bg-gray-600 mt-2"
          >
            Sign Up
          </Link>
        </form>
      </div>
    </main>
  );
}