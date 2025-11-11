# Banana_Slugs
Class Project for COSC 310
Link for Kanban board on Trello: https://trello.com/invite/accept-board
## Start up commands
### Frontend: 
cd 'Where you store your project'\Banana_Slugs\frontend\bs_reviews
npm run dev 
### Backend: 'Where you store your project'\Banana_Slugs
uvicorn backend:main --reload
// There apears to be an issue  with this startup method and the frontend not connecting with the backend properly. However I can confirm it was working the other nigh so I will provide an updated startup later. 


# Backend Code
Below is the section of code dedicated to the Backend development. Feel free to add or change as further PR's are posted. 

## Overview

This project is structured into several key components that work together to provide a functional backend for managing movie data, user reviews, and related metadata.

* **Models**
  Represent core data entities such as movies, reviews, and users. Models encapsulate the properties and behaviors of these entities, typically loading data through services and providing structured formats for API responses or internal use.

* **Services**
  Contain the business logic and data management functionality. Services handle reading from and writing to data storage (files or databases), including managing movie folders, metadata files, and review CSVs. They serve as an abstraction layer between raw data and higher-level operations, ensuring data consistency and encapsulating file handling details.

* **Routes**
  Define the API endpoints exposed by the backend. Routes receive HTTP requests, invoke the appropriate service or model logic to process data, and return responses to clients. They serve as the interface between external clients (e.g., frontend apps or external services) and the internal application logic.

* **Tests**
  Provide automated verification of the correctness and reliability of models, services, and routes. They use fixtures to create isolated test environments and mock data to validate expected behaviors under various scenarios.

Together, these layers ensure a clean separation of concerns, maintainability, and scalability of the application by organizing responsibilities clearly:

1. **Models** provide structured data representations.
2. **Services** manage data operations and business rules.
3. **Routes** expose functionality through RESTful APIs.
4. **Tests** validate the correctness and robustness of the system.

---


# Models Documentation

## movie_model.py

### Purpose

Represents a movie, aggregating metadata and reviews.

### Description

* Initializes with a movie name, loading metadata, reviews, and computing average rating via service functions.
* Provides a `to_dict()` method to convert movie data into a dictionary suitable for API responses, including title, director, genre, year, average rating, and review count.
* Implements a concise string representation showing the movie name and average rating.

---

## review_model.py

### Purpose

Represents a single user review for a movie.

### Description

* Contains username, rating, and comment fields.
* Provides a `to_dict()` method for serialization.
* Implements a simple string representation indicating the reviewer and rating.

---

## user_model.py

### Purpose

Represents a user who can post reviews.

### Description

* Stores username and an optional admin flag.
* Provides an `add_review()` method which delegates review creation to the review service, linking the user to the review data.
* Includes a readable string representation showing username and admin status.

---


# Routes Documentation

## movie_routes.py

### Purpose

Provides endpoints related to movie listings and poster images.

### Description

* **GET /top**: Returns the top 5 movies sorted by IMDb rating.
* **GET /most_commented**: Returns the top 10 movies sorted by number of comments.
* **GET /poster/{movie_name}**: Returns the poster image file for the specified movie, or a 404 error if not found.

Data is read directly from JSON metadata files stored in the movie database directory. Responses include movie title, rating or comment count, and a URL to the movie poster.

---

## review_routes.py

### Purpose

Handles review retrieval and submission for movies.

### Description

* **GET /{movie_name}**: Returns all reviews for a given movie. Raises 404 if no reviews exist.
* **POST /{movie_name}**: Accepts review input (username, rating, comment) and appends it to the movie’s reviews CSV file, returning a success message.

Uses Pydantic models for input validation and relies on the review service layer for reading and writing review data.

---

# Services Documentation

## file_service.py

### Purpose

Handles file system operations related to movies, including folder creation and checking for required data files.

### Description

* Defines the base database directory for movie data.
* Provides utilities to get the path to a movie's folder.
* Checks for existence of `metadata.json` and `movieReviews.csv` files.
* Creates a movie folder with initialized empty metadata and review CSV files including headers.

---

## metadata_service.py

### Purpose

Manages reading and writing of movie metadata stored as JSON.

### Description

* Reads metadata JSON for a given movie, returning an empty dictionary if missing.
* Writes updated metadata back to disk.
* Provides convenience functions to update specific metadata fields like average rating and total reviews, ensuring data consistency.

---

## review_service.py

### Purpose

Handles reading, writing, and processing of movie reviews stored in CSV format.

### Description

* Reads all reviews from a movie's CSV file as dictionaries.
* Adds new reviews by appending to the CSV, including automatic date insertion and proper CSV header handling.
* Recalculates average movie rating by parsing review ratings, gracefully handling missing or invalid data.

---


# Test Documentation

## Overview

This section documents the test suite for the Movie Project backend services. The tests use **pytest** fixtures and cover unit, integration, and API endpoint testing to ensure the correctness and reliability of the codebase.

---

## conftest.py

### Purpose

Defines shared **pytest fixtures** used by multiple test files to provide isolated and repeatable test environments.

### Description

* **clean_test_data:** Automatically clears the movie data directory before each test to ensure no residual data interferes.
* **temp_database_dir:** Patches the database path to a temporary directory for isolated filesystem tests.
* **temp_real_data_copy:** Copies a snapshot of the real database archive into a temporary location for integration tests, and patches the database path to use this copy.
* **isolated_movie_env:** Creates an isolated environment for movie-related tests by temporarily patching the database path.

These fixtures ensure tests run in clean, controlled environments without affecting the real data or each other.

---

## test_api_intergration_pytest.py

### Purpose

Integration tests for the FastAPI backend endpoints related to movie data.

### Description

* Tests the **/movies/top** endpoint by creating mock movie metadata and verifying top-rated movies are returned.
* Tests the **/movies/poster/{movie_name}** endpoint for handling missing poster files correctly.
* Tests the **/movies/most_commented** endpoint to verify movies are returned in descending order by comment count.
* Includes an integration test with real data to ensure endpoint correctness in a realistic environment.

These tests validate the API's expected behavior when handling movie metadata and poster requests.

---

## test_file_service_pytest.py

### Purpose

Unit and integration tests for the file management service responsible for movie folder and file operations.

### Description

* Verifies correct movie folder path resolution.
* Ensures movie folder creation produces the necessary files (`metadata.json` and `movieReviews.csv`).
* Confirms file existence checking functions behave correctly for both existing and missing files.
* Integration tests confirm that created folders contain expected files.
* Validates that a real data copy has the correct folder and file structure.

These tests guarantee reliable file and folder handling critical for data storage and retrieval.

---

## test_metadata_service_pytest.py

### Purpose

Unit and integration tests for the metadata service handling reading, writing, and updating movie metadata.

### Description

* Uses a fixture to create isolated temporary folders for safe filesystem operations.
* Tests that reading missing metadata returns an empty dictionary.
* Checks writing metadata results in correctly structured JSON files.
* Verifies updating average rating and review count correctly modifies metadata.
* Performs integration tests against a real data copy to confirm updates persist as expected and restore original data afterward.

This suite ensures the metadata service reliably manages movie metadata files.

---

## test_movie_model_pytest.py

### Purpose

Tests for the `Movie` model, which aggregates metadata, reviews, and calculated ratings.

### Description

* Validates the model correctly initializes from real data, checking key properties and data types.
* Tests the string representation for debugging readability.
* Simulates missing metadata and reviews using monkeypatching to ensure the model handles such cases gracefully without crashing.

These tests confirm the model's robustness and correct behavior under various data conditions.

---


## test_review_model_pytest.py

### Purpose

Tests the `Review` model to ensure it correctly represents individual movie reviews.

### Description

* Verifies the `to_dict()` method outputs correct review data.
* Checks the string representation (`repr`) formats the review information as expected.

---

## test_review_service_pytest.py

### Purpose

Unit and integration tests for the `review_service` module, which manages reading, writing, and processing movie reviews.

### Description

* Confirms reading from an empty reviews CSV returns an empty list.
* Tests adding a review updates the CSV and recalculates average ratings correctly.
* Checks handling of invalid or missing rating values during average rating calculation.
* Adds multiple reviews and verifies the average is computed accurately.
* Integration tests with real data ensure reading reviews and adding new ones behave as expected.
* Validates support for special characters and Unicode in review content.

These tests cover core review functionality including data integrity and edge cases.

---

## test_user_mode_pytest.py

### Purpose

Tests the `User` model, focusing on user properties and review submission.

### Description

* Validates the string representation of a `User` instance includes username and admin status.
* Uses monkeypatching to ensure `User.add_review()` delegates correctly to the review service.
* Integration test that actually appends a review to a real movie in the cloned database and verifies persistence.

These tests ensure user interactions with reviews work correctly and integrate smoothly with services.

---

Let me know if you want me to combine everything into a single markdown file or tweak the style!
