from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
from backend.routes import (
                    movie_routes,
                    review_routes,
                    user_routes,
                    admin_routes,
                    search_routes,
                    purchase_routes,
                    external_api_routes
                    )
from backend.services import admin_service
import asyncio
from backend.scripts import generate_streaming_csv


@asynccontextmanager
async def lifespan(app: FastAPI):

    # --------------------
    # STARTUP
    # --------------------
    admin_service.ensure_admin_csv_exists()
    print("✅ Admin CSV initialized")

    # Run the streaming data updater (non-blocking)
    asyncio.create_task(asyncio.to_thread(generate_streaming_csv.main))
    print("🔄 Streaming CSV update started (background task)")

    print("🚀 Server started successfully")

    yield

    # --------------------
    # SHUTDOWN
    # --------------------
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


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Movie Review API",
        version="1.0.0",
        description="API for movie reviews with tiered user system",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "Session ID"
        }
    }

    # Apply security to ALL routes
    openapi_schema["security"] = [{"bearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Register routers from routes folder
app.include_router(movie_routes.router, prefix="/api/movies", tags=["Movies"])
app.include_router(
    review_routes.router, prefix="/api/reviews", tags=["Reviews"]
)
app.include_router(user_routes.router, prefix="/api/users", tags=["Users"])
app.include_router(admin_routes.router, prefix="/api/admin", tags=["Admin"])
app.include_router(search_routes.router, prefix="/api/search", tags=["Search"])
app.include_router(purchase_routes.router, prefix="/api/store", tags=["Store"])
app.include_router(
    external_api_routes.router, prefix="/api/external", tags=["External API"]
)


@app.get("/")
async def root():
    return {"message": "Backend API is up and running."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
