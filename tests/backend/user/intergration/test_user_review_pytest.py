import pytest
from backend.models.user_model import User

def test_add_review_real_integration(temp_real_data_copy, isolated_movie_env, tmp_path, monkeypatch):
    from backend.services import user_service, file_service

    # Create an empty temporary user CSV file for this test
    temp_user_csv = tmp_path / "user_information.csv"
    temp_user_csv.write_text("user_email,user_password,user_tier\n")  # write header only

    # Patch USER_CSV_PATH so user_service uses this empty CSV instead of the real one
    monkeypatch.setattr(user_service, "USER_CSV_PATH", str(temp_user_csv))

    # Now create user should be creating fresh users isolated from real data
    user = user_service.create_user(
        email="realuser@test.com",
        password="Pass123!",
        tier=User.TIER_SLUG
    )

    movie_name = "Integration_Test_Movie"
    file_service.create_movie_folder(movie_name)

    user.add_review(movie_name, 4.5, "Integration test review")

    from backend.services.review_service import read_reviews
    reviews = read_reviews(movie_name)

    assert len(reviews) > 0
    assert any(r.get("User") == user.email for r in reviews)
