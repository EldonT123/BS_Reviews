"use client";

export default function MoviesManagementPage() {
  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Movie Management</h1>
        <p className="text-gray-400">Add, edit, and manage movies in the database</p>
      </div>

      {/* Coming Soon Card */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-12">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-600 rounded-full mb-4">
            <svg
              className="w-8 h-8 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z"
              />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">Coming Soon</h2>
          <p className="text-gray-400 max-w-md mx-auto">
            Movie management features are currently under development. You'll soon be able to add,
            edit, and delete movies from this interface.
          </p>
        </div>
      </div>

      {/* Feature Preview */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center mb-4">
            <svg
              className="w-6 h-6 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">Add Movies</h3>
          <p className="text-gray-400 text-sm">
            Add new movies to the database with details like title, genre, release date, and more.
          </p>
        </div>

        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <div className="w-12 h-12 bg-green-600 rounded-lg flex items-center justify-center mb-4">
            <svg
              className="w-6 h-6 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">Edit Movies</h3>
          <p className="text-gray-400 text-sm">
            Update movie information, correct errors, and keep the database up to date.
          </p>
        </div>

        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <div className="w-12 h-12 bg-red-600 rounded-lg flex items-center justify-center mb-4">
            <svg
              className="w-6 h-6 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">Remove Movies</h3>
          <p className="text-gray-400 text-sm">
            Delete movies that are no longer relevant or duplicates from the system.
          </p>
        </div>
      </div>
    </div>
  );
}