"use client";
import { useState } from "react";

interface StarRatingProps {
  rating: number;
  onChange: (rating: number) => void;
  maxStars?: number;
  size?: "sm" | "md" | "lg";
}

export default function StarRating({ 
  rating, 
  onChange, 
  maxStars = 10,
  size = "md" 
}: StarRatingProps) {
  const [hoverRating, setHoverRating] = useState(0);

  const sizeClasses = {
    sm: "text-xl",
    md: "text-3xl",
    lg: "text-4xl"
  };

  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: maxStars }, (_, i) => {
        const starValue = i + 1;
        const isFilled = starValue <= (hoverRating || rating);

        return (
          <button
            key={i}
            type="button"
            onClick={() => onChange(starValue)}
            onMouseEnter={() => setHoverRating(starValue)}
            onMouseLeave={() => setHoverRating(0)}
            className={`${sizeClasses[size]} transition-all duration-150 hover:scale-110 cursor-pointer`}
            title={`${starValue} out of ${maxStars}`}
          >
            <span className={isFilled ? "text-yellow-400" : "text-gray-600"}>
              {isFilled ? "★" : "☆"}
            </span>
          </button>
        );
      })}
      <span className="ml-3 text-lg font-semibold text-white">
        {rating}/{maxStars}
      </span>
    </div>
  );
}