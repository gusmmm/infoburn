"""
API routes for admission data operations.

This module contains all FastAPI routes for the admission data collection.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import date
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..dependencies import get_db
from ..models.admission_data import AdmissionDataModel
from ..services.admission_data import AdmissionDataService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admission-data",
    tags=["Admission Data"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[AdmissionDataModel])
async def get_all_admission_data(
    db: AsyncIOMotorDatabase = Depends(get_db),
    skip: int = Query(0, description="Records to skip for pagination"),
    limit: int = Query(100, description="Maximum number of records to return")
):
    """
    Get all admission data records with pagination support.
    
    Args:
        db: Database connection from dependency
        skip: Number of records to skip
        limit: Maximum records to return
        
    Returns:
        List of admission data records
    """
    try:
        return await AdmissionDataService.get_all(db)
    except Exception as e:
        logger.error(f"Error in get_all_admission_data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/search", response_model=List[AdmissionDataModel])
async def search_admission_data(
    db: AsyncIOMotorDatabase = Depends(get_db),
    nome: Optional[str] = Query(None, description="Patient name to search for"),
    start_date: Optional[date] = Query(None, description="Start date for admission date range"),
    end_date: Optional[date] = Query(None, description="End date for admission date range")
):
    """
    Search for admission data records by criteria.
    
    Args:
        db: Database connection from dependency
        nome: Optional patient name filter (case-insensitive partial match)
        start_date: Optional start date for admission date range
        end_date: Optional end date for admission date range
        
    Returns:
        List of matching admission data records
    """
    try:
        return await AdmissionDataService.search(
            db, nome=nome, start_date=start_date, end_date=end_date
        )
    except Exception as e:
        logger.error(f"Error in search_admission_data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/{patient_id}", response_model=AdmissionDataModel)
async def get_admission_data(
    patient_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get admission data for a specific patient by ID.
    
    Args:
        patient_id: ID of the patient to retrieve
        db: Database connection from dependency
        
    Returns:
        Admission data for the specified patient
        
    Raises:
        HTTPException: If patient not found
    """
    try:
        data = await AdmissionDataService.get_by_id(db, patient_id)
        if data is None:
            raise HTTPException(
                status_code=404, detail=f"Admission data with ID {patient_id} not found"
            )
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_admission_data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/", response_model=AdmissionDataModel, status_code=201)
async def create_admission_data(
    admission_data: AdmissionDataModel,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Create a new admission data record.
    
    Args:
        admission_data: AdmissionDataModel to create
        db: Database connection from dependency
        
    Returns:
        Created admission data record
    """
    try:
        # Check if patient ID already exists
        existing = await AdmissionDataService.get_by_id(db, admission_data.ID)
        if existing:
            raise HTTPException(
                status_code=409, 
                detail=f"Admission data with ID {admission_data.ID} already exists"
            )
            
        return await AdmissionDataService.create(db, admission_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_admission_data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.put("/{patient_id}", response_model=AdmissionDataModel)
async def update_admission_data(
    patient_id: str,
    admission_data: AdmissionDataModel,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Update an existing admission data record.
    
    Args:
        patient_id: ID of the patient to update
        admission_data: Updated AdmissionDataModel
        db: Database connection from dependency
        
    Returns:
        Updated admission data record
        
    Raises:
        HTTPException: If patient not found
    """
    try:
        # Ensure IDs match
        if admission_data.ID != patient_id:
            raise HTTPException(
                status_code=400,
                detail=f"Path ID {patient_id} does not match body ID {admission_data.ID}"
            )
            
        updated = await AdmissionDataService.update(db, patient_id, admission_data)
        if updated is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Admission data with ID {patient_id} not found"
            )
            
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_admission_data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/{patient_id}", status_code=204)
async def delete_admission_data(
    patient_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Delete an admission data record.
    
    Args:
        patient_id: ID of the patient to delete
        db: Database connection from dependency
        
    Returns:
        No content on success
        
    Raises:
        HTTPException: If patient not found
    """
    try:
        deleted = await AdmissionDataService.delete(db, patient_id)
        if not deleted:
            raise HTTPException(
                status_code=404, 
                detail=f"Admission data with ID {patient_id} not found"
            )
            
        #return JSONResponse(status_code=204, content={})
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_admission_data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")