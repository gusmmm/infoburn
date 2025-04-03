"""
Admission Service (Synchronous)

This module provides synchronous service functions to handle operations 
related to admission data. It's primarily used by CLI tools and scripts.
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from ..models.admission import AdmissionCreate, AdmissionResponse
from ..config.database_sync import db

class AdmissionServiceSync:
    """Service for handling synchronous admission data operations"""
    
    @staticmethod
    def get_admission(identifier: str, search_by: str = "ID") -> Optional[Dict[str, Any]]:
        """
        Get admission by ID or other field.
        
        Args:
            identifier: Value to search for
            search_by: Field to search in (default: "ID")
            
        Returns:
            Optional[Dict[str, Any]]: Found admission or None
        """
        try:
            if not db.connect():
                return None
                
            if search_by == "processo":
                try:
                    identifier = int(identifier)
                except ValueError:
                    raise ValueError("Processo must be a valid number")
                    
            result = db.db.admission_data.find_one({search_by: identifier})
            return result
            
        finally:
            db.close()

    @staticmethod
    def update_admission(admission_id: str, update_data: Dict[str, Any]) -> bool:
        """Update an admission document"""
        try:
            if not db.connect():
                return False
                
            result = db.db.admission_data.update_one(
                {"_id": admission_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
            
        finally:
            db.close()

    @staticmethod
    def link_to_burns(admission_id: str, burns_id: str) -> bool:
        """
        Create reference between admission and burns documents.
        
        Args:
            admission_id: MongoDB _id of the admission document
            burns_id: MongoDB _id of the burns document
            
        Returns:
            bool: True if the operation was successful, False otherwise
        """
        try:
            if not db.connect():
                return False
                
            result = db.db.admission_data.update_one(
                {"_id": admission_id},
                {"$set": {"burns": burns_id}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error linking admission to burns: {e}")
            return False
        finally:
            db.close()