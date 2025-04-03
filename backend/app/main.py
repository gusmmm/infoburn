"""
Main application module for InfoBurn API.

This module initializes and configures the FastAPI application.
"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routes import router
from .database import Database
from .config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app.main")

# Get application settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="InfoBurn API",
    version="0.1.0",
    description="API for Burns Critical Care Unit Information System",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include API router
app.include_router(router)

@app.on_event("startup")
async def startup_db_client():
    """Initialize database connection on startup."""
    logger.info("Starting up InfoBurn API...")
    print("Starting up InfoBurn API...")
    
    # Fix: Use proper MongoDB connection URL format
    mongodb_url = settings.MONGODB_URL
    if not mongodb_url.endswith(settings.DATABASE_NAME) and "?" not in mongodb_url:
        if not mongodb_url.endswith("/"):
            mongodb_url += "/"
        mongodb_url += settings.DATABASE_NAME
    
    db = await Database.connect_to_database(mongodb_url, settings.DATABASE_NAME)
    app.state.db = db
    logger.info(f"Connected to MongoDB database: {settings.DATABASE_NAME}")
    print(f"Connected to MongoDB database: {settings.DATABASE_NAME}")

@app.on_event("shutdown")
async def shutdown_db_client():
    """Close database connection on shutdown."""
    logger.info("Shutting down InfoBurn API...")
    print("Shutting down InfoBurn API...")
    if hasattr(app.state, "db") and app.state.db is not None:
        await Database.close_database_connection(app.state.db)
        logger.info("Database connection closed")
        print("Database connection closed")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for the API"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

@app.get("/", tags=["Root"])
async def read_root():
    """Root endpoint returning API information."""
    return {
        "message": f"Welcome to InfoBurn API v0.1.0",
        "status": "operational",
        "documentation": "/docs",
        "collections": ["admission_data", "burns"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)