"use client";

import { useState } from 'react';
import Link from "next/link";
import { useRouter } from 'next/navigation';
// A simple login page component with email and password fields
export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const response = await fetch("http://localhost:8000/api/users/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const data = await response.json();
        alert(data.detail || "Login failed");
        return;
      }

      const data = await response.json();
      
      // Save session_id to localStorage
      localStorage.setItem("sessionId", data.session_id);
      
      router.push("/user/account_page");
    } catch (error) {
      alert("Login error, please try again.");
    }
  };
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      {/* Header Home Button */}
      <Link
        href="/"
        className="absolute top-4 left-4 bg-gray-200 text-black text-sm px-3 py-1 rounded-md 
        hover:bg-gray-300 border border-gray-400"
      >
        Home
      </Link>
    
      <div className="w-full max-w-md">
        <h1 className="text-4xl font-bold mb-8 text-center">Login</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Email fill out Section */}
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
          {/* Password fill out Section */}
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
          </div>
          <button
            type="submit"
            className="w-full bg-blue-500 text-white p-2 rounded-md hover:bg-blue-600"
          >
            Sign In
          </button>
          <Link
            href="/login/signup"
            className="block w-full text-center bg-gray-200 text-blue-700 p-2 rounded-md hover:bg-gray-300 mt-2"
          >
            Sign Up
          </Link>
        </form>
      </div>
    </main>
  );
}