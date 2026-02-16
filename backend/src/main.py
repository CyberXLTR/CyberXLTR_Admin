"""
CyberXLTR Admin Platform - Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy import text
import logging

from .core.config import settings
from .core.database import db_client
from .api.routers import admin_auth, organizations, users, notifications
from .api.routers import sync as sync_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("[STARTUP] Starting CyberXLTR Admin Platform...")
    logger.info(f"[INFO] Environment: {settings.environment}")
    logger.info(f"[INFO] Debug mode: {settings.debug}")
    logger.info("[OK] Application ready to start")
    
    yield
    
    # Shutdown
    logger.info("[SHUTDOWN] Shutting down CyberXLTR Admin Platform...")
    try:
        await db_client.close()
        logger.info("[OK] Services shut down gracefully")
    except Exception as e:
        logger.error(f"[ERROR] Shutdown error: {e}")


# Create FastAPI app
app = FastAPI(
    title="CyberXLTR Admin Platform",
    description="Administrative platform for managing CyberXLTR system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if not settings.is_production else settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "CyberXLTR Admin Platform",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    try:
        # Check database connection
        async with db_client.get_session() as session:
            await session.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "database": "connected",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )


# Include API routes
app.include_router(
    admin_auth.router,
    prefix="/api/v1/auth",
    tags=["authentication"]
)

app.include_router(
    organizations.router,
    prefix="/api/v1/organizations",
    tags=["organizations"]
)

app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["users"]
)

app.include_router(
    notifications.router,
    prefix="/api/v1/notifications",
    tags=["notifications"]
)

app.include_router(
    sync_router.router,
    prefix="/api/v1/sync",
    tags=["sync"]
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.debug else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )

