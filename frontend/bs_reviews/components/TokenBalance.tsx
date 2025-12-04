"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";

type TokenBalanceProps = {
  tokens: number;
};

export default function TokenBalance({ tokens }: TokenBalanceProps) {
  const router = useRouter();
  const [showTooltip, setShowTooltip] = useState(false);

  const handleClick = () => {
    router.push("/store");
  };

  return (
    <div
      className="relative"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <button
        onClick={handleClick}
        className="bg-yellow-600 text-white px-4 py-2 rounded font-semibold hover:bg-yellow-700 transition cursor-pointer flex items-center space-x-2"
      >
        <span>💰</span>
        <span>{tokens}</span>
      </button>
      
      {showTooltip && (
        <div className="absolute top-full mt-2 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-sm px-3 py-2 rounded shadow-lg whitespace-nowrap z-50 border border-gray-700">
          <div className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-gray-800 rotate-45 border-l border-t border-gray-700"></div>
          Buy Tokens
        </div>
      )}
    </div>
  );
}