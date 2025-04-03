from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from rich.console import Console
from .settings import get_settings

console = Console()

class DatabaseConnection:
    """
    Manages MongoDB database connection
    """
    def __init__(self):
        self.settings = get_settings()
        self.client: AsyncIOMotorClient | None = None
        self.db: AsyncIOMotorDatabase | None = None
    
    async def connect(self):
        """Connect to MongoDB and setup database"""
        try:
            if self.client is None:
                self.client = AsyncIOMotorClient(self.settings.MONGODB_URL)
                self.db = self.client[self.settings.DATABASE_NAME]
                await self.setup_indexes()  # Set up indexes after connecting
            
            # Test connection
            await self.client.admin.command('ping')
            console.print("[green]Connected to MongoDB successfully![/green]")
        except Exception as e:
            console.print(f"[red]Failed to connect to MongoDB: {str(e)}[/red]")
            raise
    
    async def setup_indexes(self):
        """Set up database indexes for performance and constraints"""
        try:
            # Create unique index on burns.ID
            await self.db.burns.create_index("ID", unique=True)
            
            # Create unique index on admission_data.ID
            await self.db.admission_data.create_index("ID", unique=True)
            
            # Add other indexes as needed
        except Exception as e:
            print(f"Error setting up database indexes: {e}")

    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            console.print("[yellow]MongoDB connection closed[/yellow]")

# Create a singleton instance
db_connection = DatabaseConnection()