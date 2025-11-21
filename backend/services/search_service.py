import os
import json
import csv
from typing import List, Dict, Optional, Any
from datetime import datetime


class SearchService:
    """Service for searching movies and reviews in the database"""
    def __init__(self, database_path: str = "database/archive"):
        self.database_path = database_path

    def _load_movie_metadata(self,
                             movie_folder: str
                             ) -> Optional[Dict[str, Any]]:
        """Load metadata.json for a specific movie"""
        metadata_path = os.path.join(self.database_path,
                                     movie_folder,
                                     "metadata.json")
        if not os.path.exists(metadata_path):
            return None
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading metadata for {movie_folder}: {e}")
            return None

    def _load_movie_reviews(self, movie_folder: str) -> List[Dict[str, Any]]:
        """Load reviews from CSV for a specific movie"""
        reviews_path = os.path.join(self.database_path,
                                    movie_folder,
                                    "movieReviews.csv")
        if not os.path.exists(reviews_path):
            return []

        reviews = []
        try:
            with open(reviews_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    reviews.append(row)
        except Exception as e:
            print(f"Error loading reviews for {movie_folder}: {e}")

        return reviews

    def _get_all_movie_folders(self) -> List[str]:
        """Get all movie folder names from the database"""
        if not os.path.exists(self.database_path):
            return []

        return [
            folder for folder in os.listdir(self.database_path)
            if os.path.isdir(os.path.join(self.database_path, folder))
        ]

    def search_by_title(self,
                        query: str,
                        exact_match: bool = False) -> List[Dict[str, Any]]:
        """
        Search movies by title

        Args:
            query: Search term for movie title
            exact_match: If True, only return exact matches (case-insensitive)

        Returns:
            List of movie metadata dictionaries that match the search
        """
        results = []
        query_lower = query.lower()

        for movie_folder in self._get_all_movie_folders():
            metadata = self._load_movie_metadata(movie_folder)

            if metadata:
                title_lower = metadata.get('title', '').lower()

                if exact_match:
                    if title_lower == query_lower:
                        results.append(metadata)
                else:
                    if query_lower in title_lower:
                        results.append(metadata)

        return results

    def search_by_genre(self, genres: List[str]) -> List[Dict[str, Any]]:
        """
        Search movies by genre(s)

        Args:
            genres: List of genre strings to search for

        Returns:
            List of movie metadata dictionaries that
            contain ANY of the specified genres
        """
        results = []
        genres_lower = [g.lower() for g in genres]

        for movie_folder in self._get_all_movie_folders():
            metadata = self._load_movie_metadata(movie_folder)

            if metadata and 'movieGenres' in metadata:
                movie_genres_lower = [
                    g.lower() for g in metadata['movieGenres']]

                # Check if any of the search genres match the movie genres
                if any(genre in movie_genres_lower for genre in genres_lower):
                    results.append(metadata)

        return results

    def search_by_date_range(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search movies by publication date range

        Args:
            start_date: Start date in format 'YYYY-MM-DD' (inclusive)
            end_date: End date in format 'YYYY-MM-DD' (inclusive)

        Returns:
            List of movie metadata dictionaries published within the date range
        """
        results = []

        # Convert to datetime objects for comparison
        start_dt = datetime.strptime(start_date,
                                     '%Y-%m-%d') if start_date else None
        end_dt = datetime.strptime(end_date,
                                   '%Y-%m-%d') if end_date else None

        for movie_folder in self._get_all_movie_folders():
            metadata = self._load_movie_metadata(movie_folder)

            if metadata and 'datePublished' in metadata:
                try:
                    movie_date = datetime.strptime(
                        metadata['datePublished'], '%Y-%m-%d')

                    # Check if movie date falls within range
                    if start_dt and movie_date < start_dt:
                        continue
                    if end_dt and movie_date > end_dt:
                        continue

                    results.append(metadata)
                except ValueError:
                    # Skip movies with invalid date format
                    continue

        return results

    def search_by_year(self, year: int) -> List[Dict[str, Any]]:
        """
        Search movies by publication year

        Args:
            year: Year to search for

        Returns:
            List of movie metadata dictionaries published in the specified year
        """
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        return self.search_by_date_range(start_date, end_date)

    def advanced_search(
        self,
        title: Optional[str] = None,
        genres: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_rating: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform an advanced search with multiple criteria

        Args:
            title: Search term for movie title
            genres: List of genres to filter by
            start_date: Start date for date range filter
            end_date: End date for date range filter
            min_rating: Minimum IMDb rating
            max_rating: Maximum IMDb rating

        Returns:
            List of movie metadata dictionaries matching all specified criteria
        """
        results = []

        for movie_folder in self._get_all_movie_folders():
            metadata = self._load_movie_metadata(movie_folder)

            if not metadata:
                continue

            # Check title
            if title:
                title_lower = metadata.get('title', '').lower()
                if title.lower() not in title_lower:
                    continue

            # Check genres
            if genres:
                movie_genres_lower = [
                    g.lower() for g in metadata.get('movieGenres', [])]
                genres_lower = [g.lower() for g in genres]
                if not any(
                        genre in movie_genres_lower for genre in genres_lower):
                    continue

            # Check date range
            if start_date or end_date:
                try:
                    movie_date = datetime.strptime(
                        metadata.get('datePublished', ''), '%Y-%m-%d')

                    if start_date:
                        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                        if movie_date < start_dt:
                            continue

                    if end_date:
                        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                        if movie_date > end_dt:
                            continue
                except (ValueError, KeyError):
                    continue

            # Check rating range
            if min_rating is not None:
                if metadata.get('movieIMDbRating', 0) < min_rating:
                    continue

            if max_rating is not None:
                if metadata.get('movieIMDbRating', 11) > max_rating:
                    continue

            results.append(metadata)

        return results

    def get_movie_with_reviews(
            self, movie_title: str) -> Optional[Dict[str, Any]]:
        """
        Get complete movie data including metadata and reviews

        Args:
            movie_title: Exact movie title (folder name)

        Returns:
            Dictionary containing metadata and reviews, or None if not found
        """
        movie_folder = movie_title
        metadata = self._load_movie_metadata(movie_folder)

        if not metadata:
            return None

        reviews = self._load_movie_reviews(movie_folder)

        return {
            "metadata": metadata,
            "reviews": reviews,
            "review_count": len(reviews)
        }

    def get_all_genres(self) -> List[str]:
        """
        Get a list of all unique genres in the database

        Returns:
            Sorted list of unique genre strings
        """
        genres_set = set()

        for movie_folder in self._get_all_movie_folders():
            metadata = self._load_movie_metadata(movie_folder)

            if metadata and 'movieGenres' in metadata:
                genres_set.update(metadata['movieGenres'])

        return sorted(list(genres_set))
