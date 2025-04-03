"""
Service module for burn injury data operations.

This module handles database operations for the burns collection.
"""
import logging
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from ..models.burns import BurnsModel

logger = logging.getLogger(__name__)

class BurnsService:
    """
    Service class for handling burns data operations in MongoDB.
    
    This class provides methods for querying, creating, updating, and deleting
    burns records in the database.
    """
    
    @staticmethod
    async def get_all(db: AsyncIOMotorDatabase, skip: int = 0, limit: int = 100) -> List[BurnsModel]:
        """
        Retrieve all burns records from the database.
        
        Args:
            db: Database connection object
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of burns records
        """
        try:
            cursor = db.burns.find().skip(skip).limit(limit)
            burns_data = await cursor.to_list(length=limit)
            
            # Transform MongoDB documents to Pydantic models
            result = []
            for data in burns_data:
                try:
                    # Handle ID field mapping and remove MongoDB _id
                    processed_data = BurnsService._convert_from_db(data)
                    if processed_data:
                        result.append(processed_data)
                except Exception as e:
                    logger.error(f"Error processing burns data: {str(e)}, data: {data}")
            
            return result
        except PyMongoError as e:
            logger.error(f"Error retrieving all burns data: {str(e)}")
            raise
    
    @staticmethod
    async def search_by_criteria(
        db: AsyncIOMotorDatabase,
        mechanism: Optional[str] = None,
        accident_type: Optional[str] = None,
        min_tbsa: Optional[float] = None,
        max_tbsa: Optional[float] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[BurnsModel]:
        """
        Search for burns records based on criteria.
        
        Args:
            db: Database connection object
            mechanism: Optional burn mechanism filter
            accident_type: Optional accident type filter
            min_tbsa: Optional minimum TBSA percentage
            max_tbsa: Optional maximum TBSA percentage
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching burns records
        """
        try:
            query = {}
            
            # Add mechanism filter if provided
            if mechanism:
                query["mechanism"] = mechanism
                
            # Add accident type filter if provided
            if accident_type:
                query["type_of_accident"] = accident_type
                
            # Add TBSA range filter if provided
            if min_tbsa is not None or max_tbsa is not None:
                tbsa_query = {}
                if min_tbsa is not None:
                    tbsa_query["$gte"] = min_tbsa
                if max_tbsa is not None:
                    tbsa_query["$lte"] = max_tbsa
                    
                if tbsa_query:
                    query["tbsa"] = tbsa_query
            
            cursor = db.burns.find(query).skip(skip).limit(limit)
            data_list = await cursor.to_list(length=limit)
            
            # Transform MongoDB documents to Pydantic models
            result = []
            for data in data_list:
                try:
                    processed_data = BurnsService._convert_from_db(data)
                    if processed_data:
                        result.append(processed_data)
                except Exception as e:
                    logger.error(f"Error processing burns data: {str(e)}, data: {data}")
                    
            return result
        except PyMongoError as e:
            logger.error(f"Error searching burns data: {str(e)}")
            raise
    
    @staticmethod
    async def get_by_patient_id(db: AsyncIOMotorDatabase, patient_id: str) -> Optional[BurnsModel]:
        """
        Retrieve burns data by patient ID.
        
        Args:
            db: Database connection object
            patient_id: ID of the patient to retrieve burns data for
            
        Returns:
            BurnsModel if found, None otherwise
        """
        try:
            # Try to find by patient_id first (for newer documents)
            data = await db.burns.find_one({"patient_id": patient_id})
            
            # If not found, try with ID field (for legacy documents)
            if data is None:
                data = await db.burns.find_one({"ID": patient_id})
            
            return BurnsService._convert_from_db(data) if data else None
        except PyMongoError as e:
            logger.error(f"Error retrieving burns data for patient ID {patient_id}: {str(e)}")
            raise
    
    @staticmethod
    async def create(db: AsyncIOMotorDatabase, burns_data: BurnsModel) -> BurnsModel:
        """
        Create a new burns record.
        
        Args:
            db: Database connection object
            burns_data: BurnsModel object to create
            
        Returns:
            Created BurnsModel object
        """
        try:
            burns_dict = BurnsService._convert_to_db(burns_data)
            
            result = await db.burns.insert_one(burns_dict)
            
            # Retrieve the created document to return
            created_doc = await db.burns.find_one({"_id": result.inserted_id})
            
            return BurnsService._convert_from_db(created_doc)
        except PyMongoError as e:
            logger.error(f"Error creating burns data: {str(e)}")
            raise
    
    @staticmethod
    async def update(
        db: AsyncIOMotorDatabase, 
        patient_id: str, 
        burns_data: BurnsModel
    ) -> Optional[BurnsModel]:
        """
        Update an existing burns record.
        
        Args:
            db: Database connection object
            patient_id: ID of the patient to update burns data for
            burns_data: Updated BurnsModel
            
        Returns:
            Updated BurnsModel if successful, None if not found
        """
        try:
            burns_dict = BurnsService._convert_to_db(burns_data)
            
            # Remove ID from update data as it should not be modified
            if "_id" in burns_dict:
                del burns_dict["_id"]
            
            # Try to update by patient_id first
            result = await db.burns.update_one(
                {"patient_id": patient_id}, {"$set": burns_dict}
            )
            
            # If no document was updated, try with ID field
            if result.matched_count == 0:
                result = await db.burns.update_one(
                    {"ID": patient_id}, {"$set": burns_dict}
                )
            
            if result.matched_count == 0:
                return None
                
            # Retrieve the updated document to return
            updated_doc = await db.burns.find_one({"patient_id": patient_id})
            if updated_doc is None:
                updated_doc = await db.burns.find_one({"ID": patient_id})
                
            return BurnsService._convert_from_db(updated_doc)
        except PyMongoError as e:
            logger.error(f"Error updating burns data for patient ID {patient_id}: {str(e)}")
            raise
    
    @staticmethod
    async def delete(db: AsyncIOMotorDatabase, patient_id: str) -> bool:
        """
        Delete a burns record.
        
        Args:
            db: Database connection object
            patient_id: ID of the patient to delete burns data for
            
        Returns:
            True if deleted, False if not found
        """
        try:
            # Try to delete by patient_id first
            result = await db.burns.delete_one({"patient_id": patient_id})
            
            # If no document was deleted, try with ID field
            if result.deleted_count == 0:
                result = await db.burns.delete_one({"ID": patient_id})
                
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"Error deleting burns data for patient ID {patient_id}: {str(e)}")
            raise
    
    @staticmethod
    def _convert_to_db(burns_data: BurnsModel) -> dict:
        """
        Convert BurnsModel to a MongoDB-friendly dictionary.
        
        Args:
            burns_data: BurnsModel to convert
            
        Returns:
            Dictionary that can be stored in MongoDB
        """
        # Convert to dictionary
        data_dict = burns_data.model_dump()
        
        # For backward compatibility, also set ID field
        data_dict["ID"] = burns_data.patient_id
        
        return data_dict
    
    @staticmethod
    def _convert_from_db(db_data: dict) -> Optional[BurnsModel]:
        """
        Convert a MongoDB document to a BurnsModel.
        
        Args:
            db_data: MongoDB document
            
        Returns:
            BurnsModel instance
        """
        if not db_data:
            return None
            
        # Create a copy to avoid modifying the original
        data = db_data.copy()
        
        # Remove MongoDB _id field if present
        if "_id" in data:
            del data["_id"]
            
        # Handle legacy documents with ID field but no patient_id
        if "ID" in data and "patient_id" not in data:
            data["patient_id"] = data["ID"]
        
        try:
            return BurnsModel.model_validate(data)
        except Exception as e:
            logger.error(f"Failed to convert DB document to BurnsModel: {e}")
            raise