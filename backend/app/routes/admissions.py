from fastapi import APIRouter, HTTPException, status
from bson import ObjectId, errors as bson_errors
from ..models.admission import AdmissionModel
from ..services.admission_service import AdmissionService
from typing import List

router = APIRouter(
    prefix="/api/admissions",
    tags=["admissions"]
)

@router.post("/", response_model=AdmissionModel, status_code=status.HTTP_201_CREATED)
async def create_admission(admission: AdmissionModel):
    """
    Creates a new admission record.
    
    Args:
        admission: AdmissionModel instance containing the admission data
        
    Returns:
        AdmissionModel: The created admission record with MongoDB _id
    """
    try:
        return await AdmissionService.create_admission(admission)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{admission_id}", response_model=AdmissionModel)
async def get_admission(admission_id: str):
    """
    Retrieves an admission record by ID.
    
    Args:
        admission_id: String representation of the admission ObjectId
        
    Returns:
        AdmissionModel: The requested admission record
    """
    try:
        # Validate ObjectId format
        try:
            ObjectId(admission_id)
        except bson_errors.InvalidId:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid admission ID format"
            )
            
        if admission := await AdmissionService.get_admission(admission_id):
            return admission
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Admission with ID {admission_id} not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )