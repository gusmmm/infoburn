"""
Dependency functions for the FastAPI application.

This module contains dependency functions that can be injected into API routes.
"""
import logging
from fastapi import Depends, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

async def get_db(request: Request) -> AsyncIOMotorDatabase:
    """
    Get database connection from request state.
    
    This dependency function provides access to the MongoDB database
    connection that was established during application startup.
    
    Args:
        request: FastAPI request object
        
    Returns:
        MongoDB database connection
        
    Raises:
        RuntimeError: If database connection not found in request state
    """
    db = request.app.state.db
    if db is None:
        logger.error("Database connection not found in application state")
        raise RuntimeError("Database connection not available")
    return db