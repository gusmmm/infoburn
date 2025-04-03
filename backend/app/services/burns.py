"""
Service module for burns data operations.

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
    async def get_all(db: AsyncIOMotorDatabase) -> List[BurnsModel]:
        """
        Retrieve all burns records from the database.
        
        Args:
            db: Database connection object
            
        Returns:
            List of burns records
        """
        try:
            cursor = db.burns.find()
            burns_data = await cursor.to_list(length=100)
            return [BurnsModel.model_validate(data) for data in burns_data]
        except PyMongoError as e:
            logger.error(f"Error retrieving all burns data: {str(e)}")
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
            data = await db.burns.find_one({"ID": patient_id})
            return BurnsModel.model_validate(data) if data else None
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
            burns_dict = burns_data.model_dump()
            result = await db.burns.insert_one(burns_dict)
            
            # Retrieve the created document to return
            created_doc = await db.burns.find_one({"_id": result.inserted_id})
            return BurnsModel.model_validate(created_doc)
        except PyMongoError as e:
            logger.error(f"Error creating burns data: {str(e)}")
            raise
    
    @staticmethod
    async def update(db: AsyncIOMotorDatabase, patient_id: str, 
                   burns_data: BurnsModel) -> Optional[BurnsModel]:
        """
        Update an existing burns record.
        
        Args:
            db: Database connection object
            patient_id: ID of the patient to update burns data for
            burns_data: Updated BurnsModel object
            
        Returns:
            Updated BurnsModel if successful, None if not found
        """
        try:
            burns_dict = burns_data.model_dump()
            result = await db.burns.update_one(
                {"patient_id": patient_id}, {"$set": burns_dict}
            )
            
            if result.matched_count == 0:
                return None
                
            # Retrieve the updated document to return
            updated_doc = await db.burns.find_one({"patient_id": patient_id})
            return BurnsModel.model_validate(updated_doc)
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
            result = await db.burns.delete_one({"patient_id": patient_id})
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"Error deleting burns data for patient ID {patient_id}: {str(e)}")
            raise
            
    @staticmethod
    async def search_by_criteria(db: AsyncIOMotorDatabase, 
                              mechanism: Optional[str] = None,
                              accident_type: Optional[str] = None,
                              min_tbsa: Optional[float] = None,
                              max_tbsa: Optional[float] = None) -> List[BurnsModel]:
        """
        Search for burns records based on criteria.
        
        Args:
            db: Database connection object
            mechanism: Optional burn mechanism filter
            accident_type: Optional accident type filter
            min_tbsa: Optional minimum TBSA percentage
            max_tbsa: Optional maximum TBSA percentage
            
        Returns:
            List of matching BurnsModel objects
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
            
            cursor = db.burns.find(query)
            results = await cursor.to_list(length=100)
            return [BurnsModel.model_validate(data) for data in results]
        except PyMongoError as e:
            logger.error(f"Error searching burns data: {str(e)}")
            raise