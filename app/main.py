from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.base import Base
from app.db.session import engine
import os

# Try to import plugin models so they are registered with Base
try:
    from app.modules.plugins.commercial_kit import models
    print("Loaded commercial_kit models")
except ImportError:
    pass

# Create tables
Base.metadata.create_all(bind=engine)

def get_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static directory for uploads
    base_path = os.path.dirname(__file__)
    uploads_path = os.path.join(base_path, "uploads")
    os.makedirs(uploads_path, exist_ok=True)
    application.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")

    # Mount static directory for temporary uploads if any (compatibility)
    old_uploads_path = os.path.join(base_path, "static", "uploads")
    if os.path.exists(old_uploads_path):
        application.mount("/static/uploads", StaticFiles(directory=old_uploads_path), name="static_uploads")

    application.include_router(api_router, prefix="/api/v1")

    # Plugin Loading
    try:
        from app.modules.plugins.commercial_kit.router import router as commercial_router
        # Mount at /api/v1/plugins/commercial to share the same base URL structure
        application.include_router(commercial_router, prefix="/api/v1/plugins/commercial", tags=["Commercial Plugin"])
        print("Loaded commercial_kit plugin router")
    except ImportError as e:
        print(f"Commercial plugin router not found or failed to load: {e}")

    # Serve static files from 'static' directory (Frontend)
    static_path = os.path.join(base_path, "static")
    if os.path.exists(static_path):
        # 1. Mount assets directory specifically for performance
        assets_path = os.path.join(static_path, "assets")
        if os.path.exists(assets_path):
            application.mount("/assets", StaticFiles(directory=assets_path), name="assets")

        # 2. Catch-all route for SPA routing and other static files
        @application.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            # Skip if path starts with api prefix to avoid masking 404s for API
            if full_path.startswith("api/"):
                return {"detail": "Not Found"}
            
            # Special handling for uploads path if not caught by mount
            if full_path.startswith("uploads/"):
                relative_file = full_path.replace("uploads/", "", 1)
                file_path = os.path.join(uploads_path, relative_file)
                if os.path.isfile(file_path):
                    return FileResponse(file_path)

            # Check if it's a direct file request (like favicon.svg, robots.txt)
            file_path = os.path.join(static_path, full_path)
            if os.path.isfile(file_path):
                return FileResponse(file_path)
            
            # Otherwise return index.html for SPA routing
            index_file = os.path.join(static_path, "index.html")
            if os.path.exists(index_file):
                return FileResponse(index_file)
            
            return {"detail": "Frontend index.html not found"}

    return application

app = get_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
