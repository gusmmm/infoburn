"""
Burns Service

This module provides service functions to handle operations related to burns data.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from bson import ObjectId
from bson.json_util import dumps, loads

from backend.app.config.database import db_connection
from backend.app.models.burns import BurnsPatientData


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle MongoDB ObjectId"""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super(JSONEncoder, self).default(obj)


class BurnsService:
    """Service for managing burns data"""
    
    @staticmethod
    def _serialize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize MongoDB document to convert ObjectId to string.
        
        Args:
            doc (Dict[str, Any]): MongoDB document
            
        Returns:
            Dict[str, Any]: Serialized document
        """
        if doc is None:
            return None
            
        # Use json_util.dumps which handles MongoDB specific types
        json_str = dumps(doc)
        # Parse the JSON string back to a Python dict
        return loads(json_str)
    
    @staticmethod
    def _serialize_documents(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Serialize multiple MongoDB documents.
        
        Args:
            docs (List[Dict[str, Any]]): List of MongoDB documents
            
        Returns:
            List[Dict[str, Any]]: List of serialized documents
        """
        if docs is None:
            return []
        return [BurnsService._serialize_document(doc) for doc in docs]
    
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
        try:
            cursor = db_connection.db.burns.find().skip(skip).limit(limit)
            documents = await cursor.to_list(length=limit)
            return BurnsService._serialize_documents(documents)
        except Exception as e:
            print(f"Error in get_all_burns: {e}")
            return []
    
    @staticmethod
    async def get_burn_by_id(burn_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a burn record by ID.
        
        Args:
            burn_id (str): The ID of the burn record
            
        Returns:
            Optional[Dict[str, Any]]: The burn record if found, None otherwise
        """
        try:
            doc = await db_connection.db.burns.find_one({"ID": burn_id})
            if doc is None:
                return None
                
            # Convert the MongoDB document to a serializable dictionary
            serializable_doc = {}
            for key, value in doc.items():
                if key == "_id":
                    serializable_doc[key] = str(value)
                else:
                    serializable_doc[key] = value
                    
            return serializable_doc
        except Exception as e:
            print(f"Error in get_burn_by_id: {e}")
            return None
    
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
        
        try:
            result = await db_connection.db.burns.aggregate(pipeline).to_list(length=1)
            return BurnsService._serialize_document(result[0] if result else {})
        except Exception as e:
            print(f"Error in get_statistics: {e}")
            return {}
    
    @staticmethod
    async def get_burns_by_filters(filters: Dict[str, Any], skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve burns records that match the specified filters with pagination.
        
        Args:
            filters (Dict[str, Any]): Dictionary of field-value pairs to filter by
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return
            
        Returns:
            List[Dict[str, Any]]: List of burns records matching the filters
        """
        try:
            # Handle special case for MongoDB _id if it's a string
            if "_id" in filters and isinstance(filters["_id"], str):
                try:
                    filters["_id"] = ObjectId(filters["_id"])
                except Exception as e:
                    # If conversion fails, keep the original value
                    print(f"Warning: Invalid ObjectId format: {filters['_id']}")
            
            # Debug output
            print(f"Applying filters: {filters}")
            
            cursor = db_connection.db.burns.find(filters).skip(skip).limit(limit)
            documents = await cursor.to_list(length=limit)
            
            # Debug output
            print(f"Found {len(documents)} documents")
            
            # Manually serialize each document instead of using _serialize_documents
            serialized_docs = []
            for doc in documents:
                # Convert the MongoDB document to a serializable dictionary
                serializable_doc = {}
                for key, value in doc.items():
                    if key == "_id":
                        serializable_doc[key] = str(value)
                    else:
                        serializable_doc[key] = value
                
                serialized_docs.append(serializable_doc)
            
            return serialized_docs
        except Exception as e:
            print(f"Error in get_burns_by_filters: {e}")
            return []