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
from backend.app.models.burns_responses import BurnsPatientResponse, BurnsStatisticsResponse


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
        Serialize MongoDB document to convert ObjectId to string and rename _id to id.
        
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
        serialized_doc = loads(json_str)
        
        # Rename _id to id for Pydantic compatibility
        if '_id' in serialized_doc:
            serialized_doc['id'] = serialized_doc['_id']
            del serialized_doc['_id']
            
        return serialized_doc
    
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
    def get_all_burns(skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve all burns records with pagination.
        
        Args:
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return
            
        Returns:
            List[Dict[str, Any]]: List of burns records
        """
        try:
            if not db_connection.connect():
                return []
                
            documents = list(db_connection.db.burns.find().skip(skip).limit(limit))
            return BurnsService._serialize_documents(documents)
        except Exception as e:
            print(f"Error in get_all_burns: {e}")
            return []
    
    @staticmethod
    def get_burn_by_id(burn_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a burn record by ID.
        
        Args:
            burn_id (str): The ID of the burn record
            
        Returns:
            Optional[Dict[str, Any]]: The burn record if found, None otherwise
        """
        try:
            if not db_connection.connect():
                return None
                
            doc = db_connection.db.burns.find_one({"ID": burn_id})
            if doc is None:
                return None
                
            # Use the serialization method that handles _id to id conversion
            return BurnsService._serialize_document(doc)
        except Exception as e:
            print(f"Error in get_burn_by_id: {e}")
            return None
    
    @staticmethod
    def get_burn_by_id_sync(burn_id: str) -> Optional[Dict[str, Any]]:
        """
        Synchronous version of get_burn_by_id.
        Retrieve a burn record by ID.
        
        Args:
            burn_id (str): The ID of the burn record
            
        Returns:
            Optional[Dict[str, Any]]: The burn record if found, None otherwise
        """
        try:
            if not db_connection.connect():
                return None
                
            doc = db_connection.db.burns.find_one({"ID": burn_id})
            if doc is None:
                return None
                
            # Use the serialization method that handles _id to id conversion
            return BurnsService._serialize_document(doc)
        except Exception as e:
            print(f"Error in get_burn_by_id_sync: {e}")
            return None
        finally:
            db_connection.close()
    
    @staticmethod
    def create_burn(burn_data: BurnsPatientData) -> str:
        """
        Create a new burn record.
        
        Args:
            burn_data (BurnsPatientData): The burn data to insert
            
        Returns:
            str: The ID of the created record
            
        Raises:
            ValueError: If a record with the same ID already exists
        """
        try:
            if not db_connection.connect():
                raise ValueError("Failed to connect to database")
                
            # Check if a record with the same ID already exists
            existing_record = db_connection.db.burns.find_one({"ID": burn_data.ID})
            if existing_record:
                raise ValueError(f"A burn record with ID {burn_data.ID} already exists")
            
            # Convert to dict and add timestamp
            data = burn_data.model_dump(exclude_none=True)
            data["created_at"] = datetime.now()
            data["updated_at"] = datetime.now()
            
            result = db_connection.db.burns.insert_one(data)
            return burn_data.ID
            
        except Exception as e:
            print(f"Error in create_burn: {e}")
            raise
    
    @staticmethod
    def update_burn(burn_id: str, burn_data: Dict[str, Any]) -> bool:
        """
        Update an existing burn record.
        
        Args:
            burn_id (str): The ID of the burn record to update
            burn_data (Dict[str, Any]): The updated burn data
            
        Returns:
            bool: True if the update was successful, False otherwise
        """
        try:
            if not db_connection.connect():
                return False
                
            # Add updated timestamp
            burn_data["updated_at"] = datetime.now()
            
            result = db_connection.db.burns.update_one(
                {"ID": burn_id},
                {"$set": burn_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error in update_burn: {e}")
            return False
    
    @staticmethod
    def delete_burn(burn_id: str) -> bool:
        """
        Delete a burn record.
        
        Args:
            burn_id (str): The ID of the burn record to delete
            
        Returns:
            bool: True if the deletion was successful, False otherwise
        """
        try:
            if not db_connection.connect():
                return False
                
            result = db_connection.db.burns.delete_one({"ID": burn_id})
            return result.deleted_count > 0
            
        except Exception as e:
            print(f"Error in delete_burn: {e}")
            return False
    
    @staticmethod
    def get_statistics() -> Dict[str, Any]:
        """
        Get statistics about burns data.
        
        Returns:
            Dict[str, Any]: Statistical information about burns data
        """
        try:
            if not db_connection.connect():
                return {}
                
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
            
            result = list(db_connection.db.burns.aggregate(pipeline))
            
            # Process stats to create a proper BurnsStatisticsResponse
            raw_stats = BurnsService._serialize_document(result[0] if result else {})
            
            # Extract and format stats according to response model
            stats = {
                "total_count": raw_stats.get("total_count", [{}])[0].get("count", 0) if raw_stats.get("total_count") else 0,
                "mechanism_distribution": {},
                "accident_type_distribution": {},
                "violence_count": 0  # Default value
            }
            
            # Process mechanism stats
            if "mechanism_stats" in raw_stats:
                for item in raw_stats["mechanism_stats"]:
                    if item["_id"]:  # Skip null/None values
                        stats["mechanism_distribution"][item["_id"]] = item["count"]
            
            # Process accident type stats
            if "accident_type_stats" in raw_stats:
                for item in raw_stats["accident_type_stats"]:
                    if item["_id"]:  # Skip null/None values
                        stats["accident_type_distribution"][item["_id"]] = item["count"]
            
            # Process average TBSA
            if "avg_tbsa" in raw_stats and raw_stats["avg_tbsa"]:
                stats["average_tbsa"] = raw_stats["avg_tbsa"][0].get("avg") if raw_stats["avg_tbsa"] else None
            
            # Calculate domestic accident percentage
            if "domestic" in stats["accident_type_distribution"] and stats["total_count"] > 0:
                domestic_count = stats["accident_type_distribution"]["domestic"]
                stats["domestic_accident_percentage"] = (domestic_count / stats["total_count"]) * 100
            
            # Count violence cases
            if "violence" in raw_stats:
                stats["violence_count"] = raw_stats["violence"].count(True) if isinstance(raw_stats["violence"], list) else 0
            
            return stats
            
        except Exception as e:
            print(f"Error in get_statistics: {e}")
            return {}
    
    @staticmethod
    def get_burns_by_filters(filters: Dict[str, Any], skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
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
            if not db_connection.connect():
                return []
                
            # Handle special case for MongoDB _id if it's a string
            if "_id" in filters and isinstance(filters["_id"], str):
                try:
                    filters["_id"] = ObjectId(filters["_id"])
                except Exception as e:
                    # If conversion fails, keep the original value
                    print(f"Warning: Invalid ObjectId format: {filters['_id']}")
            
            # Debug output
            print(f"Applying filters: {filters}")
            
            documents = list(db_connection.db.burns.find(filters).skip(skip).limit(limit))
            
            # Debug output
            print(f"Found {len(documents)} documents")
            
            return BurnsService._serialize_documents(documents)
            
        except Exception as e:
            print(f"Error in get_burns_by_filters: {e}")
            return []