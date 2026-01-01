from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.base import Base
from app.db.session import engine
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    # CORS configuration
    # Note: allow_origins=["*"] cannot be used with allow_credentials=True
    # In production, you should specify the actual origins
    application.add_middleware(
        CORSMiddleware,
        allow_origin_regex=".*", # Use regex to allow all origins while supporting credentials
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Middleware to log all requests
    @application.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info(f"Incoming request: {request.method} {request.url.path}")
        try:
            response = await call_next(request)
            logger.info(f"Response status: {response.status_code} for {request.method} {request.url.path}")
            return response
        except Exception as e:
            logger.error(f"Request failed: {request.method} {request.url.path} - Error: {str(e)}")
            raise

    # Global exception handler for debugging
    @application.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception during {request.method} {request.url.path}: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal Server Error: {str(exc)}"},
        )

    # Health check
    @application.get("/api/health")
    async def health_check():
        return {"status": "ok"}

    # Mount static directory for uploads
    # Use absolute path for safety
    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    if not os.path.exists(upload_dir):
        try:
            os.makedirs(upload_dir, exist_ok=True)
            logger.info(f"Created upload directory: {upload_dir}")
        except Exception as e:
            logger.error(f"Failed to create upload directory {upload_dir}: {e}")
    
    # Debug: List contents of upload directory
    try:
        files = os.listdir(upload_dir)
        logger.info(f"Upload directory {upload_dir} contains {len(files)} files")
        if len(files) > 0:
            logger.info(f"Sample files: {files[:5]}")
    except Exception as e:
        logger.error(f"Cannot list upload directory: {e}")

    logger.info(f"Mounting /uploads to {upload_dir}")
    application.mount("/uploads", StaticFiles(directory=upload_dir, check_dir=False), name="uploads")

    # API routes
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
    # The frontend is built and placed in backend/app/static
    app_path = os.path.dirname(os.path.abspath(__file__))
    static_path = os.path.join(app_path, "static")
    
    logger.info(f"Static files path: {static_path}")
    
    if os.path.exists(static_path):
        # 1. Mount assets directory specifically for performance
        assets_path = os.path.join(static_path, "assets")
        if os.path.exists(assets_path):
            logger.info(f"Mounting /assets to {assets_path}")
            application.mount("/assets", StaticFiles(directory=assets_path), name="assets")

        # 2. Explicit route for root path
        @application.get("/")
        async def serve_index():
            index_file = os.path.join(static_path, "index.html")
            if os.path.exists(index_file):
                return FileResponse(index_file)
            return JSONResponse(status_code=404, content={"detail": "Frontend index.html not found"})

        # 3. Catch-all route for SPA routing and other static files
        @application.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            # Skip if path starts with api prefix to avoid masking 404s for API
            if full_path.startswith("api/"):
                return JSONResponse(status_code=404, content={"detail": f"API route not found: {full_path}"})
            
            # Special handling for uploads path if not caught by mount
            if full_path.startswith("uploads/"):
                relative_file = full_path.replace("uploads/", "", 1)
                file_path = os.path.join(upload_dir, relative_file)
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
            
            return JSONResponse(status_code=404, content={"detail": "Frontend index.html not found"})

    return application

app = get_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
