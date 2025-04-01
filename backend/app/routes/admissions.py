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
        
    Raises:
        HTTPException: 
            - 409: If admission with same ID already exists
            - 500: For other server errors
    """
    return await AdmissionService.create_admission(admission)