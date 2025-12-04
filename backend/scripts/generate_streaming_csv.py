# backend/scripts/generate_streaming_csv.py
import os
import csv
import json
from backend.services import external_api_service
from backend.services.file_service import get_movie_folder, create_movie_folder
from backend.services.metadata_service import read_metadata

# =============================
# Configuration
# =============================
DATABASE_PATH = "database/archive"  # Parent folder containing all movie folders
FORCE_UPDATE = False  # Set True to always fetch fresh data from Watchmode


# =============================
# Helper Functions
# =============================
def get_movie_names_from_archive():
    """Return list of movie folder names inside the archive."""
    if not os.path.isdir(DATABASE_PATH):
        return []
    return [
        folder for folder in os.listdir(DATABASE_PATH)
        if os.path.isdir(os.path.join(DATABASE_PATH, folder))
    ]


def write_csv(movie_name: str, movie_data: dict):
    """Write streamingData.csv in the movie folder, overwriting if needed."""
    folder = create_movie_folder(movie_name)  # ensures folder exists
    csv_path = os.path.join(folder, "streamingData.csv")

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow([
            "Poster URL",
            "Subscription Services",
            "Rent Services",
            "Buy Services"
        ])

        streaming = movie_data.get("streaming_services", {})

        # =============================
        # Deduplicate each category by name
        # =============================
        subscription = list({s["name"]: s for s in streaming.get("subscription", [])}.values())
        rent = list({s["name"]: s for s in streaming.get("rent", [])}.values())
        buy = list({s["name"]: s for s in streaming.get("buy", [])}.values())

        # Write JSON objects as strings in each cell
        row = [
            movie_data.get("poster_url", ""),
            json.dumps(subscription),
            json.dumps(rent),
            json.dumps(buy)
        ]
        writer.writerow(row)


# =============================
# Main Function
# =============================
def main():
    movie_names = get_movie_names_from_archive()
    if not movie_names:
        print("[INFO] No movies found in archive.")
        return

    for movie_name in movie_names:
        try:
            folder = get_movie_folder(movie_name)
            csv_path = os.path.join(folder, "streamingData.csv")

            # Skip CSV if it exists and FORCE_UPDATE is False
            if os.path.exists(csv_path) and not FORCE_UPDATE:
                print(f"[SKIP] CSV already exists for '{movie_name}'.")
                continue

            metadata = read_metadata(movie_name)
            title = metadata.get("title", movie_name)
            print(f"[UPDATE] Fetching data for '{title}'...")

            watchmode_id = external_api_service.get_first_valid_watchmode_id(title)
            if not watchmode_id:
                print(f"[WARN] Could not find Watchmode ID for '{title}'. Skipping.")
                continue

            movie_data = external_api_service.get_movie_details(watchmode_id)
            if "error" in movie_data:
                print(f"[WARN] Failed to fetch details for '{title}': {movie_data['error']}")
                continue

            write_csv(movie_name, movie_data)
            print(f"[OK] CSV updated for '{title}'.")

        except Exception as e:
            print(f"[ERROR] Exception processing '{movie_name}': {e}")


# =============================
# Entry Point
# =============================
if __name__ == "__main__":
    main()
