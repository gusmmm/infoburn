"""
Database Configuration Module

This module handles the MongoDB database connection configuration using PyMongo.
"""

import os
from typing import Optional, Any
from pymongo import MongoClient
from pymongo.collection import Collection
from rich.console import Console
from rich.panel import Panel

console = Console()

class DatabaseConnection:
    """
    MongoDB database connection manager using PyMongo.
    Implements a singleton pattern to maintain a single database connection.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            # Initialize instance attributes
            cls._instance.client = None
            cls._instance.db = None
            cls._instance.uri = os.getenv(
                "MONGODB_URL", 
                "mongodb://localhost:27017/infoburn?retryWrites=false&directConnection=true&maxPoolSize=10"
            )
            cls._instance.db_name = os.getenv("MONGODB_DB", "infoburn")
        return cls._instance
    
    def connect(self) -> bool:
        """
        Establish connection to MongoDB database.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if self.client is None:
                self.client = MongoClient(self.uri)
                self.db = self.client[self.db_name]
                # Test connection
                self.client.server_info()
                console.print("[green]Successfully connected to MongoDB[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Database connection error: {str(e)}[/red]")
            return False
    
    def close(self) -> None:
        """Close the MongoDB connection"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            console.print("[yellow]MongoDB connection closed[/yellow]")
    
    def get_collection(self, name: str) -> Optional[Collection]:
        """
        Get a MongoDB collection by name.
        Ensures connection is established before accessing.
        
        Args:
            name: Name of the collection
            
        Returns:
            Collection or None: MongoDB collection or None if connection failed
        """
        if not self.db:
            if not self.connect():
                return None
        return self.db[name]
    
    def setup_indexes(self) -> None:
        """
        Setup database indexes for collections.
        Should be called after establishing connection.
        """
        try:
            if not self.db:
                if not self.connect():
                    return
                
            # Create unique index on burns.ID
            self.db.burns.create_index("ID", unique=True)
            
            # Create unique index on admission_data.ID
            self.db.admission_data.create_index("ID", unique=True)
            
            console.print("[green]Database indexes created successfully[/green]")
        except Exception as e:
            console.print(f"[red]Error setting up database indexes: {str(e)}[/red]")

# Global database connection instance
db_connection = DatabaseConnection()