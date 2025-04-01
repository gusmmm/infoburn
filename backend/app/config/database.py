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
            self.client = AsyncIOMotorClient(self.settings.MONGODB_URL)
            self.db = self.client[self.settings.DATABASE_NAME]
            
            # Create unique index on ID field
            await self.db.admission_data.create_index("ID", unique=True)
            
            # Test connection
            await self.client.admin.command('ping')
            console.print("[green]Connected to MongoDB successfully![/green]")
        except Exception as e:
            console.print(f"[red]Failed to connect to MongoDB: {str(e)}[/red]")
            raise
    
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            console.print("[yellow]MongoDB connection closed[/yellow]")

# Create a singleton instance
db_connection = DatabaseConnection()