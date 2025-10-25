from auth_server import AuthService, AccountManager, MovieGoer
from movie_database import MovieDatabase

auth = AuthService("users.json")
manager = AccountManager(auth)
db = MovieDatabase("Banana_Slugs/database/archive")

#log in attempt
user = auth.login ("ABC", "1234")
if not user:
    manager.create_account("ABC", "1234", "ABC@gmail.com", "2000-04-01")
    user = auth.login("grayson", "1234")

#interface
while True:
    print("\nMenu")
    print("1. Search for movie")
    print("2. View bookmarks")
    print("3. Logout")

    answer = input("Choose: ")
    
    if answer == "1":
        keyword = input ("Enter search keyword: ")
        results = db.search_movies(keyword)
        if not results:
            print("No results.")
            continue
        for i, title in enumerate(results, 1):
            print(f"{i}. {title}")
        pick = input("Select a movie to bookmark (number): ")
        if pick.isdigit() and 1 <= int(pick) <= len(results):
            movie_title = results[int(pick)-1]
            if user.add_bookmark(movie_title):
                users = auth._load_users()
                for u in users:
                    if u["username"] == user.username:
                        u["bookmarks"] = user.bookmarks
                auth._save_users(users)

    elif answer == "2":
        user.view_bookmarks()
    elif answer == "3":
        print("Logged out")
        break

    

