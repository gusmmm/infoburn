"""
Database Connection Test Script

This script tests the MongoDB connection and basic operations.
"""

import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add the parent directory to the path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

from backend.app.config.database import db_connection

console = Console()

def test_connection():
    """Test the database connection and basic operations"""
    try:
        # Connect to database
        if not db_connection.connect():
            return False
        
        # Setup indexes
        db_connection.setup_indexes()
        
        # Get collection stats
        burns_count = db_connection.db.burns.count_documents({})
        admissions_count = db_connection.db.admission_data.count_documents({})
        
        # Create stats table
        table = Table(title="Database Statistics")
        table.add_column("Collection", style="cyan")
        table.add_column("Document Count", style="green")
        
        table.add_row("Burns", str(burns_count))
        table.add_row("Admissions", str(admissions_count))
        
        console.print(table)
        
        return True
    except Exception as e:
        console.print(f"[red]Error testing database: {str(e)}[/red]")
        return False
    finally:
        db_connection.close()

if __name__ == "__main__":
    console.print(Panel("MongoDB Connection Test", style="bold blue"))
    success = test_connection()
    sys.exit(0 if success else 1)