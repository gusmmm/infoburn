"""
API routes for burns data operations.

This module contains all FastAPI routes for the burns collection.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..dependencies import get_db
from ..models.burns import BurnsModel, BurnMechanism, AccidentType
from ..services.burns import BurnsService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/burns",
    tags=["Burns"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[BurnsModel])
async def get_all_burns_data(
    db: AsyncIOMotorDatabase = Depends(get_db),
    skip: int = Query(0, description="Records to skip for pagination"),
    limit: int = Query(100, description="Maximum number of records to return")
):
    """
    Get all burns records with pagination support.
    
    Args:
        db: Database connection from dependency
        skip: Number of records to skip
        limit: Maximum records to return
        
    Returns:
        List of burns records
    """
    try:
        return await BurnsService.get_all(db)
    except Exception as e:
        logger.error(f"Error in get_all_burns_data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/search", response_model=List[BurnsModel])
async def search_burns_data(
    db: AsyncIOMotorDatabase = Depends(get_db),
    mechanism: Optional[BurnMechanism] = Query(None, description="Burn mechanism filter"),
    accident_type: Optional[AccidentType] = Query(None, description="Accident type filter"),
    min_tbsa: Optional[float] = Query(None, ge=0, le=100, description="Minimum TBSA percentage"),
    max_tbsa: Optional[float] = Query(None, ge=0, le=100, description="Maximum TBSA percentage")
):
    """
    Search for burns records by criteria.
    
    Args:
        db: Database connection from dependency
        mechanism: Optional burn mechanism filter
        accident_type: Optional accident type filter
        min_tbsa: Optional minimum TBSA percentage
        max_tbsa: Optional maximum TBSA percentage
        
    Returns:
        List of matching burns records
    """
    try:
        return await BurnsService.search_by_criteria(
            db,
            mechanism=mechanism.value if mechanism else None,
            accident_type=accident_type.value if accident_type else None,
            min_tbsa=min_tbsa,
            max_tbsa=max_tbsa
        )
    except Exception as e:
        logger.error(f"Error in search_burns_data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/{patient_id}", response_model=BurnsModel)
async def get_burns_data(
    patient_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get burns data for a specific patient by ID.
    
    Args:
        patient_id: ID of the patient to retrieve burns data for
        db: Database connection from dependency
        
    Returns:
        Burns data for the specified patient
        
    Raises:
        HTTPException: If patient burns data not found
    """
    try:
        data = await BurnsService.get_by_patient_id(db, patient_id)
        if data is None:
            raise HTTPException(
                status_code=404, detail=f"Burns data for patient ID {patient_id} not found"
            )
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_burns_data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/", response_model=BurnsModel, status_code=201)
async def create_burns_data(
    burns_data: BurnsModel,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Create a new burns record.
    
    Args:
        burns_data: BurnsModel to create
        db: Database connection from dependency
        
    Returns:
        Created burns record
    """
    try:
        # Check if patient burns data already exists
        existing = await BurnsService.get_by_patient_id(db, burns_data.patient_id)
        if existing:
            raise HTTPException(
                status_code=409, 
                detail=f"Burns data for patient ID {burns_data.patient_id} already exists"
            )
            
        return await BurnsService.create(db, burns_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_burns_data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.put("/{patient_id}", response_model=BurnsModel)
async def update_burns_data(
    patient_id: str,
    burns_data: BurnsModel,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Update an existing burns record.
    
    Args:
        patient_id: ID of the patient to update burns data for
        burns_data: Updated BurnsModel
        db: Database connection from dependency
        
    Returns:
        Updated burns record
        
    Raises:
        HTTPException: If patient burns data not found
    """
    try:
        # Ensure patient IDs match
        if burns_data.patient_id != patient_id:
            raise HTTPException(
                status_code=400,
                detail=f"Path ID {patient_id} does not match body patient_id {burns_data.patient_id}"
            )
            
        updated = await BurnsService.update(db, patient_id, burns_data)
        if updated is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Burns data for patient ID {patient_id} not found"
            )
            
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_burns_data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/{patient_id}", status_code=204)
async def delete_burns_data(
    patient_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Delete a burns record.
    
    Args:
        patient_id: ID of the patient to delete burns data for
        db: Database connection from dependency
        
    Returns:
        No content on success
        
    Raises:
        HTTPException: If patient burns data not found
    """
    try:
        deleted = await BurnsService.delete(db, patient_id)
        if not deleted:
            raise HTTPException(
                status_code=404, 
                detail=f"Burns data for patient ID {patient_id} not found"
            )
            
        return JSONResponse(status_code=204, content={})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_burns_data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")