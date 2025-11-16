"use client";

import { useState, useEffect } from "react";

export default function DarkModeToggle() {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    if (isDark) {
      document.body.classList.add("dark");
    } else {
      document.body.classList.remove("dark");
    }
  }, [isDark]);

  return (
    <button
      onClick={() => setIsDark(!isDark)}
      aria-label="Toggle dark mode"
      style={{
        position: "fixed",
        bottom: "1rem",
        right: "1rem",
        backgroundColor: isDark ? "#333" : "#eee",
        color: isDark ? "#eee" : "#333",
        border: "none",
        borderRadius: "50%",
        width: "3rem",
        height: "3rem",
        cursor: "pointer",
        boxShadow: "0 2px 6px rgba(0,0,0,0.3)",
        fontSize: "1.5rem",
        userSelect: "none",
      }}
    >
      {isDark ? "☀️" : "🌙"}
    </button>
  );
}
