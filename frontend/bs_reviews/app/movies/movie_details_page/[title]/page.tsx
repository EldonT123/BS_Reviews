"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import Image from "next/image";

type StreamingData = {
  name: string;
  web_url?: string;
  price?: number | null;
};

type MovieData = {
  movie_name: string;
  poster_url: string;
  streaming_services: {
    subscription: StreamingData[];
    rent: StreamingData[];
    buy: StreamingData[];
  };
};

export default function MovieDetailsPage() {
  const params = useParams();
  const title = params?.title;

  const [data, setData] = useState<MovieData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!title) return;

    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`http://localhost:8000/api/movies/streaming/${title}`);
        if (!res.ok) {
          setError(`Error ${res.status}`);
          setLoading(false);
          return;
        }
        const json: MovieData = await res.json();
        setData(json);
      } catch (err) {
        setError("Fetch failed");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [title]);

  if (loading)
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-400 text-xl font-medium">
        Loading...
      </div>
    );
  if (error)
    return (
      <div className="min-h-screen flex items-center justify-center text-red-500 text-xl font-medium">
        {error}
      </div>
    );
  if (!data)
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-400 text-xl font-medium">
        No data found.
      </div>
    );

  const renderServices = (services: StreamingData[], showPrice: boolean = false) =>
    services.map((s, i) => (
      <a
        key={i}
        href={s.web_url || "#"}
        target="_blank"
        rel="noopener noreferrer"
        className="bg-yellow-400 text-black font-semibold text-sm px-4 py-2 rounded hover:bg-yellow-500 transition shadow-md m-1 whitespace-nowrap"
      >
        {s.name} {showPrice && s.price != null ? `- $${s.price}` : ""}
      </a>
    ));

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 font-sans">
      {/* Header - Full Width at Top */}
      <header className="w-full px-8 py-4 bg-black/90 shadow-md sticky top-0 z-10">
        <Link
          href="/"
          className="text-yellow-400 hover:text-yellow-500 transition text-lg font-semibold"
        >
          ← Back to Home
        </Link>
      </header>

      {/* Main Content */}
      <div className="px-4 py-12 flex flex-col items-center">
        {/* Poster */}
        <div className="relative mb-8">
          <Image 
            src={data.poster_url}
            alt={data.movie_name}
            className="w-48 sm:w-56 md:w-64 rounded-lg shadow-2xl mx-auto"
          />
        </div>

        {/* Title */}
        <h1 className="text-4xl sm:text-5xl font-bold mb-12 text-center">{data.movie_name}</h1>

        {/* Streaming Sections */}
        <div className="w-full max-w-4xl flex flex-col items-center space-y-12">
          {data.streaming_services.subscription.length > 0 && (
            <div className="w-full bg-gray-800 rounded-lg p-6 shadow-lg">
              <h2 className="text-2xl font-semibold text-yellow-400 mb-4 text-center border-b border-yellow-400 pb-2">
                Subscription Services
              </h2>
              <div className="flex justify-center">
                <div className="flex flex-wrap justify-center gap-2 bg-gray-700 p-4 rounded-lg">
                  {renderServices(data.streaming_services.subscription)}
                </div>
              </div>
            </div>
          )}

          {data.streaming_services.rent.length > 0 && (
            <div className="w-full bg-gray-800 rounded-lg p-6 shadow-lg">
              <h2 className="text-2xl font-semibold text-yellow-400 mb-4 text-center border-b border-yellow-400 pb-2">
                Rent
              </h2>
              <div className="flex justify-center">
                <div className="flex flex-wrap justify-center gap-2 bg-gray-700 p-4 rounded-lg">
                  {renderServices(data.streaming_services.rent, true)}
                </div>
              </div>
            </div>
          )}

          {data.streaming_services.buy.length > 0 && (
            <div className="w-full bg-gray-800 rounded-lg p-6 shadow-lg">
              <h2 className="text-2xl font-semibold text-yellow-400 mb-4 text-center border-b border-yellow-400 pb-2">
                Buy
              </h2>
              <div className="flex justify-center">
                <div className="flex flex-wrap justify-center gap-2 bg-gray-700 p-4 rounded-lg">
                  {renderServices(data.streaming_services.buy, true)}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
