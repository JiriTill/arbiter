"""
The Arbiter - FastAPI Application
Main entry point with CORS configuration.
"""

import os
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import get_settings
from app.api.routes import router as api_router
from app.api.analytics import router as analytics_router
from app.api.admin import router as admin_router


# Global worker thread reference
_worker_thread = None


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="The Arbiter API",
        description="Board game rules Q&A with RAG and citation verification",
        version=__version__,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # CORS Middleware - Allow all origins for now (can be tightened later)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins
        allow_credentials=False,  # Must be False when using "*"
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
    # Include API routes
    app.include_router(api_router)
    app.include_router(analytics_router)
    app.include_router(admin_router)
    
    return app


# Create app instance
app = create_app()


def _start_rq_worker():
    """Start RQ worker in background thread."""
    import subprocess
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        print("⚠️  REDIS_URL not set, skipping worker startup")
        return
    
    print("🔧 Starting RQ Worker in background...")
    # Run worker blocking (this will run in its own thread)
    subprocess.run([
        "python", "-m", "rq.cli", "worker", 
        "--url", redis_url
    ])


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    global _worker_thread
    
    settings = get_settings()
    print(f"🎲 The Arbiter API v{__version__}")
    print(f"   Environment: {settings.environment}")
    print(f"   Debug: {settings.debug}")
    print(f"   CORS Origins: {settings.cors_origins}")
    
    # Start worker in background thread
    _worker_thread = threading.Thread(target=_start_rq_worker, daemon=True)
    _worker_thread.start()
    print("✅ RQ Worker thread started")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print("👋 The Arbiter API shutting down...")
