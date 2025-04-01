from typing import List, Optional
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from ..config.database import db_connection
from ..models.admission import AdmissionModel
from rich.console import Console
from fastapi import HTTPException, status

console = Console()

class AdmissionService:
    @staticmethod
    async def create_admission(admission: AdmissionModel) -> AdmissionModel:
        """
        Creates a new admission record in the database.
        
        Args:
            admission: AdmissionModel instance to be created
            
        Returns:
            AdmissionModel: Created admission with MongoDB generated _id
            
        Raises:
            HTTPException: If admission with same ID already exists or other database errors
        """
        try:
            # Convert model to dict for MongoDB
            admission_dict = admission.model_dump(
                by_alias=True,
                exclude={'_id'} if not admission.id else set(),
                exclude_none=True
            )
            
            # Check if admission with same ID exists
            existing = await db_connection.db.admission_data.find_one({"ID": admission.ID})
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Admission with ID {admission.ID} already exists"
                )
            
            # Insert into MongoDB
            try:
                result = await db_connection.db.admission_data.insert_one(admission_dict)
            except DuplicateKeyError:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Admission with ID {admission.ID} already exists"
                )
            
            # Fetch the complete document
            created_doc = await db_connection.db.admission_data.find_one(
                {"_id": result.inserted_id}
            )
            
            if not created_doc:
                raise ValueError("Failed to retrieve created document")
            
            # Return new model instance with MongoDB data
            return AdmissionModel.from_mongo(created_doc)
            
        except HTTPException:
            raise
        except Exception as e:
            console.print(f"[red]Error creating admission: {str(e)}[/red]")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    @staticmethod
    async def get_admission(admission_id: str) -> Optional[AdmissionModel]:
        """Retrieves an admission record by ID."""
        try:
            object_id = ObjectId(admission_id)
            if (admission := await db_connection.db.admission_data.find_one({"_id": object_id})):
                return AdmissionModel.from_mongo(admission)
            return None
        except Exception as e:
            console.print(f"[red]Error retrieving admission: {str(e)}[/red]")
            raise