"""
Burns Routes

This module defines the API routes for burns data operations.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from fastapi.responses import JSONResponse
import json

from backend.app.models.burns import BurnsPatientData
from backend.app.services.burns_service import BurnsService

# Create router
router = APIRouter(
    prefix="/burns",
    tags=["burns"],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
async def get_burns(
    ID: Optional[str] = Query(None, description="Patient burns identifier"),
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return")
):
    """
    Retrieve burns records with optional filtering and pagination.
    
    Args:
        ID (Optional[str]): Filter by patient burns identifier (optional filter)
        skip (int): Number of records to skip for pagination
        limit (int): Maximum number of records to return
        
    Returns:
        List[Dict[str, Any]]: List of burns records matching the criteria
        
    Raises:
        HTTPException: If there's an error during the retrieval process
    """
    try:
        # If ID is provided, filter by ID
        if ID:
            # Use the get_burns_by_filters method to filter by ID
            filters = {"ID": ID}
            result = await BurnsService.get_burns_by_filters(filters, skip, limit)
        else:
            # No ID filter provided, return all burns with pagination
            result = await BurnsService.get_all_burns(skip, limit)
        
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving burns records: {str(e)}")


@router.get("/{burn_id}")
async def get_burn(burn_id: str):
    """
    Retrieve a burn record by ID.
    
    Args:
        burn_id (str): The ID of the burn record
        
    Returns:
        Dict[str, Any]: The burn record
        
    Raises:
        HTTPException: If the burn record is not found
    """
    burn = await BurnsService.get_burn_by_id(burn_id)
    if not burn:
        raise HTTPException(status_code=404, detail=f"Burn record with ID {burn_id} not found")
    return JSONResponse(content=burn)


@router.post("/")
async def create_burn(burn_data: BurnsPatientData):
    """
    Create a new burn record.
    
    Args:
        burn_data (BurnsPatientData): The burn data to insert
        
    Returns:
        Dict[str, Any]: The created burn record
        
    Raises:
        HTTPException: If the burn record could not be created or already exists
    """
    try:
        burn_id = await BurnsService.create_burn(burn_data)
        
        # Return the created record
        created_burn = await BurnsService.get_burn_by_id(burn_id)
        if not created_burn:
            raise HTTPException(status_code=500, detail="Failed to create burn record")
            
        return JSONResponse(content=created_burn)
    except ValueError as e:
        # Handle the case when a record with the same ID already exists
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        # Handle other errors
        raise HTTPException(status_code=500, detail=f"Error creating burn record: {str(e)}")


@router.put("/{burn_id}")
async def update_burn(burn_id: str, burn_data: Dict[str, Any] = Body(...)):
    """
    Update an existing burn record.
    
    Args:
        burn_id (str): The ID of the burn record to update
        burn_data (Dict[str, Any]): The updated burn data
        
    Returns:
        Dict[str, Any]: The updated burn record
        
    Raises:
        HTTPException: If the burn record is not found or could not be updated
    """
    # Check if burn exists
    existing_burn = await BurnsService.get_burn_by_id(burn_id)
    if not existing_burn:
        raise HTTPException(status_code=404, detail=f"Burn record with ID {burn_id} not found")
    
    # Update the burn
    success = await BurnsService.update_burn(burn_id, burn_data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update burn record")
    
    # Return the updated record
    updated_burn = await BurnsService.get_burn_by_id(burn_id)
    return JSONResponse(content=updated_burn)


@router.delete("/{burn_id}")
async def delete_burn(burn_id: str):
    """
    Delete a burn record.
    
    Args:
        burn_id (str): The ID of the burn record to delete
        
    Returns:
        Dict[str, str]: Success message
        
    Raises:
        HTTPException: If the burn record is not found or could not be deleted
    """
    # Check if burn exists
    existing_burn = await BurnsService.get_burn_by_id(burn_id)
    if not existing_burn:
        raise HTTPException(status_code=404, detail=f"Burn record with ID {burn_id} not found")
    
    # Delete the burn
    success = await BurnsService.delete_burn(burn_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete burn record")
    
    return {"message": f"Burn record with ID {burn_id} deleted successfully"}


@router.get("/statistics/summary")
async def get_statistics():
    """
    Get statistics about burns data.
    
    Returns:
        Dict[str, Any]: Statistical information about burns data
    """
    stats = await BurnsService.get_statistics()
    return JSONResponse(content=stats)