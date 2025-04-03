"""
API routes module initialization.

This module combines all route modules into a single router.
"""
from fastapi import APIRouter
from .admission_data import router as admission_data_router
from .burns import router as burns_router

# Create a combined router for all API endpoints
router = APIRouter(prefix="/api/v1")

# Add all application routers
router.include_router(admission_data_router)
router.include_router(burns_router)