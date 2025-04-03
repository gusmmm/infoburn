"""
Admissions API Routes

This module contains the API routes for admission-related operations.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query, Path
from ..models.admission import AdmissionCreate, AdmissionUpdate, AdmissionResponse
from ..services.admission_service import AdmissionService

router = APIRouter(prefix="/api/admissions", tags=["admissions"])

@router.get("/", response_model=List[AdmissionResponse])
def get_admissions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return")
):
    """Get all admission records with pagination"""
    return AdmissionService.get_all_admissions(skip=skip, limit=limit)

@router.get("/by-id/{admission_id}", response_model=AdmissionResponse)
def get_admission_by_id(
    admission_id: str = Path(..., description="The ID of the admission record")
):
    """Get a specific admission by ID"""
    admission = AdmissionService.get_admission(admission_id, "ID")
    if not admission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Admission with ID {admission_id} not found"
        )
    return admission

@router.get("/by-processo/{processo}", response_model=AdmissionResponse)
def get_admission_by_processo(
    processo: int = Path(..., description="The processo number of the admission")
):
    """Get a specific admission by processo number"""
    try:
        admission = AdmissionService.get_admission(str(processo), "processo")
        if not admission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Admission with processo {processo} not found"
            )
        return admission
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/search", response_model=AdmissionResponse)
def search_admission(
    ID: Optional[str] = Query(None, description="Patient admission identifier (4-5 digits)"),
    _id: Optional[str] = Query(None, description="MongoDB document ID"),
    processo: Optional[int] = Query(None, description="Patient file number")
):
    """Search for an admission by various criteria"""
    try:
        if _id is not None:
            return AdmissionService.get_admission(_id, "_id")
        elif ID is not None:
            return AdmissionService.get_admission(ID, "ID")
        elif processo is not None:
            return AdmissionService.get_admission(str(processo), "processo")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one search parameter should be provided"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/", response_model=AdmissionResponse, status_code=status.HTTP_201_CREATED)
def create_admission(admission: AdmissionCreate):
    """Create a new admission record"""
    return AdmissionService.create_admission(admission)

@router.put("/{admission_id}", response_model=AdmissionResponse)
def update_admission(
    admission_data: Dict[str, Any],
    admission_id: str = Path(..., description="The ID of the admission record to update")
):
    """Update an existing admission record by ID"""
    return AdmissionService.update_admission(admission_id, "ID", admission_data)

@router.delete("/{admission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admission(
    admission_id: str = Path(..., description="The ID of the admission record to delete")
):
    """Delete an admission record by ID"""
    AdmissionService.delete_admission(admission_id, "ID")
    return None