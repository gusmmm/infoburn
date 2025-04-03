"""
Service module for admission data operations.

This module handles database operations for the admission_data collection.
"""
import logging
from typing import List, Optional
from datetime import date
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from ..models.admission_data import AdmissionDataModel

logger = logging.getLogger(__name__)

class AdmissionDataService:
    """
    Service class for handling admission data operations in MongoDB.
    
    This class provides methods for querying, creating, updating, and deleting
    admission data records in the database.
    """
    
    @staticmethod
    async def get_all(db: AsyncIOMotorDatabase) -> List[AdmissionDataModel]:
        """
        Retrieve all admission data records from the database.
        
        Args:
            db: Database connection object
            
        Returns:
            List of admission data records
        """
        try:
            cursor = db.admission_data.find()
            admission_data = await cursor.to_list(length=100)
            return [AdmissionDataModel.parse_obj(data) for data in admission_data]
        except PyMongoError as e:
            logger.error(f"Error retrieving all admission data: {str(e)}")
            raise
    
    @staticmethod
    async def get_by_id(db: AsyncIOMotorDatabase, patient_id: str) -> Optional[AdmissionDataModel]:
        """
        Retrieve admission data by patient ID.
        
        Args:
            db: Database connection object
            patient_id: ID of the patient to retrieve
            
        Returns:
            AdmissionDataModel if found, None otherwise
        """
        try:
            data = await db.admission_data.find_one({"ID": patient_id})
            return AdmissionDataModel.parse_obj(data) if data else None
        except PyMongoError as e:
            logger.error(f"Error retrieving admission data by ID {patient_id}: {str(e)}")
            raise
    
    @staticmethod
    async def create(db: AsyncIOMotorDatabase, admission_data: AdmissionDataModel) -> AdmissionDataModel:
        """
        Create a new admission data record.
        
        Args:
            db: Database connection object
            admission_data: AdmissionDataModel object to create
            
        Returns:
            Created AdmissionDataModel object
        """
        try:
            admission_dict = admission_data.model_dump()
            result = await db.admission_data.insert_one(admission_dict)
            
            # Retrieve the created document to return
            created_doc = await db.admission_data.find_one({"_id": result.inserted_id})
            return AdmissionDataModel.parse_obj(created_doc)
        except PyMongoError as e:
            logger.error(f"Error creating admission data: {str(e)}")
            raise
    
    @staticmethod
    async def update(db: AsyncIOMotorDatabase, patient_id: str, 
                    admission_data: AdmissionDataModel) -> Optional[AdmissionDataModel]:
        """
        Update an existing admission data record.
        
        Args:
            db: Database connection object
            patient_id: ID of the patient to update
            admission_data: Updated AdmissionDataModel object
            
        Returns:
            Updated AdmissionDataModel if successful, None if not found
        """
        try:
            admission_dict = admission_data.model_dump()
            result = await db.admission_data.update_one(
                {"ID": patient_id}, {"$set": admission_dict}
            )
            
            if result.matched_count == 0:
                return None
                
            # Retrieve the updated document to return
            updated_doc = await db.admission_data.find_one({"ID": patient_id})
            return AdmissionDataModel.parse_obj(updated_doc)
        except PyMongoError as e:
            logger.error(f"Error updating admission data for ID {patient_id}: {str(e)}")
            raise
    
    @staticmethod
    async def delete(db: AsyncIOMotorDatabase, patient_id: str) -> bool:
        """
        Delete an admission data record.
        
        Args:
            db: Database connection object
            patient_id: ID of the patient to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            result = await db.admission_data.delete_one({"ID": patient_id})
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"Error deleting admission data for ID {patient_id}: {str(e)}")
            raise
            
    @staticmethod
    async def search(db: AsyncIOMotorDatabase, 
                    nome: Optional[str] = None,
                    start_date: Optional[date] = None,
                    end_date: Optional[date] = None) -> List[AdmissionDataModel]:
        """
        Search for admission data records based on criteria.
        
        Args:
            db: Database connection object
            nome: Optional patient name to search for (partial match)
            start_date: Optional start date for admission date range filter
            end_date: Optional end date for admission date range filter
            
        Returns:
            List of matching AdmissionDataModel objects
        """
        try:
            query = {}
            
            # Add name filter if provided
            if nome:
                query["nome"] = {"$regex": nome, "$options": "i"}  # Case-insensitive search
                
            # Add date range filter if provided
            if start_date or end_date:
                date_query = {}
                if start_date:
                    date_query["$gte"] = start_date
                if end_date:
                    date_query["$lte"] = end_date
                    
                if date_query:
                    query["data_ent"] = date_query
            
            cursor = db.admission_data.find(query)
            results = await cursor.to_list(length=100)
            return [AdmissionDataModel.parse_obj(data) for data in results]
        except PyMongoError as e:
            logger.error(f"Error searching admission data: {str(e)}")
            raise