from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.routes import (
                    movie_routes,
                    review_routes,
                    user_routes,
                    admin_routes
                    )
from backend.services import admin_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: runs before the application starts
    admin_service.ensure_admin_csv_exists()
    print("✅ Admin CSV initialized")
    print("🚀 Server started successfully")

    yield

    # Shutdown: runs after the application stops
    admin_service.cleanup_expired_tokens()
    print("🧹 Cleaned up expired tokens")
    print("👋 Server shutting down")


app = FastAPI(lifespan=lifespan)

# Enable CORS (adjust origins in production!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers from routes folder
app.include_router(movie_routes.router, prefix="/movies", tags=["Movies"])
app.include_router(review_routes.router, prefix="/reviews", tags=["Reviews"])
app.include_router(user_routes.router, prefix="/api", tags=["users"])
app.include_router(admin_routes.router, prefix="/api/admin", tags=["admin"])


@app.get("/")
async def root():
    return {"message": "Backend API is up and running."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=5000)
