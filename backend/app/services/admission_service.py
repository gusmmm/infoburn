from typing import Optional, Any, Dict
from fastapi import HTTPException, status
from rich.console import Console
from ..models.admission import AdmissionCreate, AdmissionResponse
from ..config.database import db_connection

console = Console()

class AdmissionService:
    """Service for handling admission data operations"""
    
    @staticmethod
    async def get_admission(identifier: str, search_by: str) -> AdmissionResponse:
        """
        Retrieve an admission by ID or processo
        
        Args:
            identifier: The ID or processo value to search for
            search_by: The field to search by ('ID' or 'processo')
            
        Returns:
            AdmissionResponse: The found admission
            
        Raises:
            ValueError: If processo search with non-numeric identifier
            HTTPException: If admission not found
        """
        try:
            # Convert processo to int if needed
            if search_by == "processo":
                try:
                    identifier = int(identifier)
                except ValueError:
                    raise ValueError("Processo must be a valid number")
            
            # Search database
            result = await db_connection.db.admission_data.find_one(
                {search_by: identifier}
            )
            
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Admission with {search_by}={identifier} not found"
                )
            
            return AdmissionResponse(**result)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )

    @staticmethod
    async def create_admission(admission: AdmissionCreate) -> AdmissionResponse:
        """
        Creates a new admission record in the database.
        
        Args:
            admission: AdmissionCreate instance with admission data
            
        Returns:
            AdmissionResponse: Created admission with MongoDB generated _id
            
        Raises:
            HTTPException: If admission with same ID exists or other database errors
        """
        try:
            # Convert model to dict and serialize dates for MongoDB
            admission_dict = AdmissionService._serialize_dates(
                admission.model_dump(exclude_none=True)
            )
            
            # Check if admission with same ID exists
            existing = await db_connection.db.admission_data.find_one({"ID": admission.ID})
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Admission with ID {admission.ID} already exists"
                )
            
            # Insert into MongoDB
            result = await db_connection.db.admission_data.insert_one(admission_dict)
            
            # Fetch the complete document with the generated _id
            created_doc = await db_connection.db.admission_data.find_one(
                {"_id": result.inserted_id}
            )
            
            if not created_doc:
                raise ValueError("Failed to retrieve created document")
            
            # Deserialize dates and return response model
            deserialized_doc = AdmissionService._deserialize_dates(created_doc)
            return AdmissionResponse(**deserialized_doc)
            
        except HTTPException:
            raise
        except Exception as e:
            console.print(f"[red]Error creating admission: {str(e)}[/red]")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )