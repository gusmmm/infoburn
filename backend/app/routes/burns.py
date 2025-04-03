"""
Burns Routes

This module defines the API routes for burns data operations.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body, Depends

from backend.app.models.burns import BurnsPatientData
from backend.app.services.burns_service import BurnsService

# Create router
router = APIRouter(
    prefix="/burns",
    tags=["burns"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[Dict[str, Any]])
async def get_burns(
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return")
):
    """
    Retrieve all burns records with pagination.
    
    Args:
        skip (int): Number of records to skip
        limit (int): Maximum number of records to return
        
    Returns:
        List[Dict[str, Any]]: List of burns records
    """
    return await BurnsService.get_all_burns(skip, limit)


@router.get("/{burn_id}", response_model=Dict[str, Any])
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
    return burn


@router.post("/", response_model=Dict[str, Any])
async def create_burn(burn_data: BurnsPatientData):
    """
    Create a new burn record.
    
    Args:
        burn_data (BurnsPatientData): The burn data to insert
        
    Returns:
        Dict[str, Any]: The created burn record
        
    Raises:
        HTTPException: If the burn record could not be created
    """
    burn_id = await BurnsService.create_burn(burn_data)
    
    # Return the created record
    created_burn = await BurnsService.get_burn_by_id(burn_id)
    if not created_burn:
        raise HTTPException(status_code=500, detail="Failed to create burn record")
        
    return created_burn


@router.put("/{burn_id}", response_model=Dict[str, Any])
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
    return updated_burn


@router.delete("/{burn_id}", response_model=Dict[str, str])
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


@router.get("/statistics/summary", response_model=Dict[str, Any])
async def get_statistics():
    """
    Get statistics about burns data.
    
    Returns:
        Dict[str, Any]: Statistical information about burns data
    """
    return await BurnsService.get_statistics()