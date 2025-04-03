"""
Service module for admission data operations.

This module handles database operations for the admission_data collection.
"""
import logging
from typing import List, Optional
from datetime import date, datetime
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
            return [AdmissionDataService._convert_from_db(data) for data in admission_data]
        except PyMongoError as e:
            logger.error(f"Error retrieving all admission data: {str(e)}")
            raise
    
    @staticmethod
    async def search(
        db: AsyncIOMotorDatabase, 
        nome: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[AdmissionDataModel]:
        """
        Search for admission data records by criteria.
        
        Args:
            db: Database connection object
            nome: Optional patient name filter (case-insensitive partial match)
            start_date: Optional start date for admission date range
            end_date: Optional end date for admission date range
            
        Returns:
            List of matching admission data records
        """
        try:
            query = {}
            
            # Add name filter if provided
            if nome:
                query["nome"] = {"$regex": nome, "$options": "i"}
                
            # Add date range filter if provided
            if start_date or end_date:
                date_query = {}
                if start_date:
                    date_query["$gte"] = start_date.isoformat()
                if end_date:
                    date_query["$lte"] = end_date.isoformat()
                    
                if date_query:
                    query["data_ent"] = date_query
            
            cursor = db.admission_data.find(query)
            results = await cursor.to_list(length=100)
            return [AdmissionDataService._convert_from_db(data) for data in results]
        except PyMongoError as e:
            logger.error(f"Error searching admission data: {str(e)}")
            raise
    
    @staticmethod
    async def get_by_id(db: AsyncIOMotorDatabase, patient_id: str) -> Optional[AdmissionDataModel]:
        """
        Retrieve admission data by patient ID.
        
        Args:
            db: Database connection object
            patient_id: ID of the patient to retrieve admission data for
            
        Returns:
            AdmissionDataModel if found, None otherwise
        """
        try:
            data = await db.admission_data.find_one({"ID": patient_id})
            return AdmissionDataService._convert_from_db(data) if data else None
        except PyMongoError as e:
            logger.error(f"Error retrieving admission data for ID {patient_id}: {str(e)}")
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
            admission_dict = AdmissionDataService._convert_to_db(admission_data)
            result = await db.admission_data.insert_one(admission_dict)
            
            # Retrieve the created document to return
            created_doc = await db.admission_data.find_one({"_id": result.inserted_id})
            return AdmissionDataService._convert_from_db(created_doc)
        except PyMongoError as e:
            logger.error(f"Error creating admission data: {str(e)}")
            raise
    
    @staticmethod
    async def update(
        db: AsyncIOMotorDatabase, 
        patient_id: str, 
        admission_data: AdmissionDataModel
    ) -> Optional[AdmissionDataModel]:
        """
        Update an existing admission data record.
        
        Args:
            db: Database connection object
            patient_id: ID of the patient to update admission data for
            admission_data: Updated AdmissionDataModel object
            
        Returns:
            Updated AdmissionDataModel if successful, None if not found
        """
        try:
            admission_dict = AdmissionDataService._convert_to_db(admission_data)
            
            # Remove ID from update data as it should not be modified
            if "_id" in admission_dict:
                del admission_dict["_id"]
                
            result = await db.admission_data.update_one(
                {"ID": patient_id}, {"$set": admission_dict}
            )
            
            if result.matched_count == 0:
                return None
                
            # Retrieve the updated document to return
            updated_doc = await db.admission_data.find_one({"ID": patient_id})
            return AdmissionDataService._convert_from_db(updated_doc)
        except PyMongoError as e:
            logger.error(f"Error updating admission data for ID {patient_id}: {str(e)}")
            raise
    
    @staticmethod
    async def delete(db: AsyncIOMotorDatabase, patient_id: str) -> bool:
        """
        Delete an admission data record.
        
        Args:
            db: Database connection object
            patient_id: ID of the patient to delete admission data for
            
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
    def _convert_to_db(admission_data: AdmissionDataModel) -> dict:
        """
        Convert AdmissionDataModel to a MongoDB-friendly dictionary.
        
        Args:
            admission_data: AdmissionDataModel to convert
            
        Returns:
            Dictionary that can be stored in MongoDB
        """
        data_dict = admission_data.model_dump()
        
        # Convert date objects to ISO format strings for MongoDB compatibility
        if data_dict.get("data_ent") and isinstance(data_dict["data_ent"], date):
            data_dict["data_ent"] = data_dict["data_ent"].isoformat()
            
        if data_dict.get("data_alta") and isinstance(data_dict["data_alta"], date):
            data_dict["data_alta"] = data_dict["data_alta"].isoformat()
            
        if data_dict.get("data_nasc") and isinstance(data_dict["data_nasc"], date):
            data_dict["data_nasc"] = data_dict["data_nasc"].isoformat()
            
        return data_dict
    
    @staticmethod
    def _convert_from_db(db_data: dict) -> Optional[AdmissionDataModel]:
        """
        Convert a MongoDB document to an AdmissionDataModel.
        
        Args:
            db_data: MongoDB document
            
        Returns:
            AdmissionDataModel instance
        """
        if not db_data:
            return None
            
        # Remove MongoDB _id field if present
        if "_id" in db_data:
            db_data = {k: v for k, v in db_data.items() if k != "_id"}
            
        # Convert ISO format strings back to date objects
        if db_data.get("data_ent") and isinstance(db_data["data_ent"], str):
            try:
                db_data["data_ent"] = date.fromisoformat(db_data["data_ent"])
            except ValueError:
                logger.warning(f"Invalid date format for data_ent: {db_data['data_ent']}")
                
        if db_data.get("data_alta") and isinstance(db_data["data_alta"], str):
            try:
                db_data["data_alta"] = date.fromisoformat(db_data["data_alta"])
            except ValueError:
                logger.warning(f"Invalid date format for data_alta: {db_data['data_alta']}")
                
        if db_data.get("data_nasc") and isinstance(db_data["data_nasc"], str):
            try:
                db_data["data_nasc"] = date.fromisoformat(db_data["data_nasc"])
            except ValueError:
                logger.warning(f"Invalid date format for data_nasc: {db_data['data_nasc']}")
                
        return AdmissionDataModel.model_validate(db_data)