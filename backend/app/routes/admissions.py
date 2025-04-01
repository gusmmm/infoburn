from fastapi import APIRouter, HTTPException, status
from ..models.admission import AdmissionCreate, AdmissionResponse
from ..services.admission_service import AdmissionService

router = APIRouter(
    prefix="/api/admissions",
    tags=["admissions"]
)

@router.post("/", response_model=AdmissionResponse, status_code=status.HTTP_201_CREATED)
async def create_admission(admission: AdmissionCreate):
    """
    Creates a new admission record.
    
    The _id field is automatically generated by MongoDB and returned in the response.
    
    Args:
        admission: Admission data without _id field
        
    Returns:
        AdmissionResponse: Created admission with MongoDB generated _id
        
    Raises:
        HTTPException: 
            - 409: If admission with same ID already exists
            - 500: For other server errors
    """
    return await AdmissionService.create_admission(admission)