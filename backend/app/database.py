"""
Database connection module for InfoBurn API.

This module handles database connections and operations.
"""
import logging
import motor.motor_asyncio
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

class Database:
    """
    Database connection and operations handler.
    
    This class manages MongoDB connections and provides
    utility methods for database operations.
    """
    
    @staticmethod
    async def connect_to_database(mongodb_url: str, db_name: str):
        """
        Establishes a connection to the MongoDB database.
        
        Args:
            mongodb_url: MongoDB connection string
            db_name: Name of the database to connect to
            
        Returns:
            Database connection object
            
        Raises:
            ConnectionError: If unable to connect to the database
        """
        try:
            logger.info(f"Connecting to MongoDB at {mongodb_url}")
            
            # Set serverSelectionTimeoutMS to 5 seconds to fail fast if MongoDB is not available
            client = motor.motor_asyncio.AsyncIOMotorClient(
                mongodb_url, 
                serverSelectionTimeoutMS=5000
            )
            
            # Verify connection works by pinging the server
            await client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
            # Get database instance
            db = client[db_name]
            return db
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise ConnectionError(f"Could not connect to MongoDB: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {str(e)}")
            raise ConnectionError(f"Unexpected error connecting to MongoDB: {str(e)}")
    
    @staticmethod
    async def close_database_connection(db):
        """
        Closes the database connection.
        
        Args:
            db: Database connection to close
        """
        if db is not None:
            try:
                db.client.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {str(e)}")
                
    @staticmethod
    async def get_collection(db, collection_name: str):
        """
        Gets a reference to a specific collection.
        
        Args:
            db: Database connection
            collection_name: Name of the collection to access
            
        Returns:
            Collection reference
        """
        if db is None:
            raise ValueError("Database connection is None")
        return db[collection_name]
        
    @staticmethod
    async def ensure_indexes(db):
        """
        Create database indexes for optimal performance.
        
        Args:
            db: Database connection
        """
        try:
            # Create indexes for admission_data collection
            await db.admission_data.create_index("ID", unique=True)
            await db.admission_data.create_index("nome")
            await db.admission_data.create_index("data_ent")
            
            # Create indexes for burns collection
            await db.burns.create_index("patient_id", unique=True)
            await db.burns.create_index("mechanism")
            await db.burns.create_index("type_of_accident")
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating database indexes: {str(e)}")
            # Don't raise - indexes are helpful but not critical