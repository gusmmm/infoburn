from motor.motor_asyncio import AsyncIOMotorClient
from rich.console import Console
from typing import Optional

console = Console()

class DatabaseConnection:
    """
    Manages MongoDB database connections for the InfoBurn system.
    
    Attributes:
        client (AsyncIOMotorClient): MongoDB client instance
        db (AsyncIOMotorDatabase): Database instance
    """
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        
    async def connect(self):
        """Establishes connection to MongoDB"""
        try:
            self.client = AsyncIOMotorClient("mongodb://localhost:27017")
            self.db = self.client.infoburn
            console.print("[green]Successfully connected to MongoDB[/green]")
        except Exception as e:
            console.print(f"[red]Failed to connect to MongoDB: {str(e)}[/red]")
            raise
            
    async def close(self):
        """Closes the MongoDB connection"""
        if self.client:
            self.client.close()
            console.print("[yellow]MongoDB connection closed[/yellow]")

# Create a global instance
db_connection = DatabaseConnection()