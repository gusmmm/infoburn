"""
Burns Service

This module provides service functions to handle operations related to burns data.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.app.config.database import db_connection
from backend.app.models.burns import BurnsPatientData


class BurnsService:
    """Service for managing burns data"""
    
    @staticmethod
    async def get_all_burns(skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve all burns records with pagination.
        
        Args:
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return
            
        Returns:
            List[Dict[str, Any]]: List of burns records
        """
        cursor = db_connection.db.burns.find().skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    @staticmethod
    async def get_burn_by_id(burn_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a burn record by ID.
        
        Args:
            burn_id (str): The ID of the burn record
            
        Returns:
            Optional[Dict[str, Any]]: The burn record if found, None otherwise
        """
        return await db_connection.db.burns.find_one({"ID": burn_id})
    
    @staticmethod
    async def create_burn(burn_data: BurnsPatientData) -> str:
        """
        Create a new burn record.
        
        Args:
            burn_data (BurnsPatientData): The burn data to insert
            
        Returns:
            str: The ID of the created record
        """
        # Convert to dict and add timestamp
        data = burn_data.model_dump(exclude_none=True)
        data["created_at"] = datetime.now()
        data["updated_at"] = datetime.now()
        
        result = await db_connection.db.burns.insert_one(data)
        return burn_data.ID
    
    @staticmethod
    async def update_burn(burn_id: str, burn_data: Dict[str, Any]) -> bool:
        """
        Update an existing burn record.
        
        Args:
            burn_id (str): The ID of the burn record to update
            burn_data (Dict[str, Any]): The updated burn data
            
        Returns:
            bool: True if the update was successful, False otherwise
        """
        # Add updated timestamp
        burn_data["updated_at"] = datetime.now()
        
        result = await db_connection.db.burns.update_one(
            {"ID": burn_id},
            {"$set": burn_data}
        )
        
        return result.modified_count > 0
    
    @staticmethod
    async def delete_burn(burn_id: str) -> bool:
        """
        Delete a burn record.
        
        Args:
            burn_id (str): The ID of the burn record to delete
            
        Returns:
            bool: True if the deletion was successful, False otherwise
        """
        result = await db_connection.db.burns.delete_one({"ID": burn_id})
        return result.deleted_count > 0
    
    @staticmethod
    async def get_statistics() -> Dict[str, Any]:
        """
        Get statistics about burns data.
        
        Returns:
            Dict[str, Any]: Statistical information about burns data
        """
        pipeline = [
            {
                "$facet": {
                    "total_count": [{"$count": "count"}],
                    "mechanism_stats": [
                        {"$group": {"_id": "$mechanism", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}}
                    ],
                    "accident_type_stats": [
                        {"$group": {"_id": "$type_of_accident", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}}
                    ],
                    "avg_tbsa": [{"$group": {"_id": None, "avg": {"$avg": "$tbsa"}}}]
                }
            }
        ]
        
        result = await db_connection.db.burns.aggregate(pipeline).to_list(length=1)
        return result[0] if result else {}