from typing import List, Optional
from datetime import date, datetime
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from ..config.database import db_connection
from ..models.admission import AdmissionCreate, AdmissionResponse
from fastapi import HTTPException, status
from rich.console import Console

console = Console()

class AdmissionService:
    """Service for managing admission records"""
    
    @staticmethod
    def _serialize_dates(data: dict) -> dict:
        """
        Convert date objects to MongoDB datetime objects
        
        Args:
            data: Dictionary containing date fields
            
        Returns:
            dict: Data with dates converted to datetime objects
        """
        date_fields = ['data_ent', 'data_alta', 'data_nasc']
        for field in date_fields:
            if field in data and isinstance(data[field], date):
                # Convert to datetime at midnight UTC
                data[field] = datetime.combine(data[field], datetime.min.time())
        return data
    
    @staticmethod
    def _deserialize_dates(data: dict) -> dict:
        """
        Convert MongoDB datetime objects back to date objects
        
        Args:
            data: Dictionary containing datetime fields
            
        Returns:
            dict: Data with datetimes converted to date objects
        """
        date_fields = ['data_ent', 'data_alta', 'data_nasc']
        for field in date_fields:
            if field in data and isinstance(data[field], datetime):
                data[field] = data[field].date()
        return data
    
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