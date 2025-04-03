# backend/app/config/database_sync.py
"""Database Configuration Module for Synchronous Operations"""

import os
from typing import Optional
from pymongo import MongoClient
from rich.console import Console

console = Console()

class DatabaseConnection:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance.client = None
            cls._instance.db = None
            cls._instance.uri = os.getenv(
                "MONGODB_URL", 
                "mongodb://localhost:27017/infoburn?retryWrites=false&directConnection=true"
            )
            cls._instance.db_name = os.getenv("MONGODB_DB", "infoburn")
        return cls._instance

    def connect(self) -> bool:
        try:
            self.client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=5000
            )
            self.db = self.client[self.db_name]
            self.client.server_info()
            console.print("[green]Successfully connected to MongoDB[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Database connection error: {str(e)}[/red]")
            return False

    def close(self):
        if self.client:
            self.client.close()
            self.client = None
            self.db = None

db = DatabaseConnection()