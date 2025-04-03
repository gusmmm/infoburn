"""
Admission Service

This module provides service functions to handle operations related to admission data.
"""

from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status
from rich.console import Console
from datetime import datetime
from bson import ObjectId

from ..models.admission import AdmissionCreate, AdmissionResponse
from ..config.database import db_connection

console = Console()

class AdmissionService:
    """Service for handling admission data operations"""
    
    @staticmethod
    def _serialize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize MongoDB document for JSON response.
        
        Args:
            doc (Dict[str, Any]): MongoDB document
            
        Returns:
            Dict[str, Any]: Serialized document with string IDs
        """
        if not doc:
            return None
            
        result = {}
        for key, value in doc.items():
            if key == "_id" and isinstance(value, ObjectId):
                result[key] = str(value)
            else:
                result[key] = value
                
        return result
    
    @staticmethod
    def get_admission(identifier: str, search_by: str = "ID") -> Optional[Dict[str, Any]]:
        """
        Get admission by identifier and search field.
        
        Args:
            identifier (str): Value to search for
            search_by (str): Field to search in
            
        Returns:
            Optional[Dict[str, Any]]: Found admission or None
            
        Raises:
            ValueError: If processo field is not a valid number
        """
        try:
            if not db_connection.connect():
                return None
                
            if search_by == "processo":
                try:
                    identifier = int(identifier)
                except ValueError:
                    raise ValueError("Processo must be a valid number")
                    
            if search_by == "_id" and not isinstance(identifier, ObjectId):
                try:
                    identifier = ObjectId(identifier)
                except Exception:
                    raise ValueError(f"Invalid ObjectId format: {identifier}")
                    
            result = db_connection.db.admission_data.find_one({search_by: identifier})
            return AdmissionService._serialize_document(result)
            
        except Exception as e:
            console.print(f"[red]Error in get_admission: {str(e)}[/red]")
            raise
    
    @staticmethod
    def get_all_admissions(skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all admissions with pagination.
        
        Args:
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return
            
        Returns:
            List[Dict[str, Any]]: List of admission records
        """
        try:
            if not db_connection.connect():
                return []
                
            documents = list(db_connection.db.admission_data.find().skip(skip).limit(limit))
            return [AdmissionService._serialize_document(doc) for doc in documents]
            
        except Exception as e:
            console.print(f"[red]Error in get_all_admissions: {str(e)}[/red]")
            return []
    
    @staticmethod
    def create_admission(admission: AdmissionCreate) -> Dict[str, Any]:
        """
        Create a new admission record.
        
        Args:
            admission (AdmissionCreate): The admission data to insert
            
        Returns:
            Dict[str, Any]: The created admission record
            
        Raises:
            HTTPException: If database connection fails or duplicate ID exists
        """
        try:
            if not db_connection.connect():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database connection failed"
                )

            # Check for existing admission
            existing = db_connection.db.admission_data.find_one(
                {"ID": admission.ID}
            )
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Admission with ID {admission.ID} already exists"
                )
            
            # Insert into MongoDB
            admission_dict = admission.model_dump(exclude_none=True)
            admission_dict["created_at"] = datetime.now()
            admission_dict["updated_at"] = datetime.now()
            
            result = db_connection.db.admission_data.insert_one(admission_dict)
            
            # Fetch the created document
            created_doc = db_connection.db.admission_data.find_one(
                {"_id": result.inserted_id}
            )
            
            return AdmissionService._serialize_document(created_doc)
            
        except HTTPException:
            raise
        except Exception as e:
            console.print(f"[red]Error in create_admission: {str(e)}[/red]")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create admission: {str(e)}"
            )
    
    @staticmethod
    def update_admission(identifier: str, search_by: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing admission record.
        
        Args:
            identifier (str): Identifier value
            search_by (str): Field to search by
            update_data (Dict[str, Any]): Data to update
            
        Returns:
            Dict[str, Any]: Updated admission record
            
        Raises:
            HTTPException: If record not found or update fails
        """
        try:
            if not db_connection.connect():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database connection failed"
                )

            # Prepare search query
            query = {}
            if search_by == "_id" and not isinstance(identifier, ObjectId):
                try:
                    query["_id"] = ObjectId(identifier)
                except Exception:
                    raise ValueError(f"Invalid ObjectId format: {identifier}")
            elif search_by == "processo":
                try:
                    query[search_by] = int(identifier)
                except ValueError:
                    raise ValueError("Processo must be a valid number")
            else:
                query[search_by] = identifier
            
            # Add updated timestamp
            update_data["updated_at"] = datetime.now()
            
            # Update the document
            result = db_connection.db.admission_data.find_one_and_update(
                query,
                {"$set": update_data},
                return_document=True
            )
            
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Admission with {search_by}={identifier} not found"
                )
            
            return AdmissionService._serialize_document(result)
            
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            console.print(f"[red]Error in update_admission: {str(e)}[/red]")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update admission: {str(e)}"
            )
    
    @staticmethod
    def delete_admission(identifier: str, search_by: str) -> bool:
        """
        Delete an admission record.
        
        Args:
            identifier (str): Identifier value
            search_by (str): Field to search by
            
        Returns:
            bool: True if deletion was successful
            
        Raises:
            HTTPException: If record not found or deletion fails
        """
        try:
            if not db_connection.connect():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database connection failed"
                )

            # Prepare search query
            query = {}
            if search_by == "_id" and not isinstance(identifier, ObjectId):
                try:
                    query["_id"] = ObjectId(identifier)
                except Exception:
                    raise ValueError(f"Invalid ObjectId format: {identifier}")
            elif search_by == "processo":
                try:
                    query[search_by] = int(identifier)
                except ValueError:
                    raise ValueError("Processo must be a valid number")
            else:
                query[search_by] = identifier
            
            # Delete the document
            result = db_connection.db.admission_data.delete_one(query)
            
            if result.deleted_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Admission with {search_by}={identifier} not found"
                )
            
            return True
            
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            console.print(f"[red]Error in delete_admission: {str(e)}[/red]")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete admission: {str(e)}"
            )