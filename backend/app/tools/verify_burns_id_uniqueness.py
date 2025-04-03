"""
Burns ID Uniqueness Verification Tool

This module verifies that all IDs in the burns collection are unique
and can be used as references to the admission_data collection.
It provides functionality to check for duplicates, validate references,
and fix inconsistencies.
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.prompt import Prompt, Confirm

# Add parent directory to path to import from other modules
parent_dir = Path(__file__).parent.parent.parent.parent
sys.path.append(str(parent_dir))

from backend.app.config.database import db_connection

# Initialize console for rich output
console = Console()


class BurnsIdVerifier:
    """
    Service for verifying and enforcing ID uniqueness in burns collection.
    
    This class provides tools to:
    1. Check for duplicate IDs in the burns collection
    2. Validate that burn IDs exist in the admission_data collection
    3. Generate reports of inconsistencies
    4. Fix duplicate IDs if needed
    """
    
    def __init__(self):
        """Initialize the burns ID verifier."""
        self.duplicate_ids = []
        self.missing_references = []
        self.orphaned_burns = []
        
    async def check_id_uniqueness(self) -> List[Dict[str, Any]]:
        """
        Check for duplicate IDs in the burns collection.
        
        Returns:
            List[Dict[str, Any]]: List of duplicate documents grouped by ID
        """
        duplicates = []
        
        # Get all IDs and their counts
        pipeline = [
            {"$group": {"_id": "$ID", "count": {"$sum": 1}, "docs": {"$push": "$$ROOT"}}},
            {"$match": {"count": {"$gt": 1}}},
            {"$sort": {"_id": 1}}
        ]
        
        cursor = db_connection.db.burns.aggregate(pipeline)
        duplicate_groups = await cursor.to_list(length=None)
        
        # Store duplicate IDs for later use
        self.duplicate_ids = duplicate_groups
        
        return duplicate_groups
    
    async def validate_burn_references(self) -> List[str]:
        """
        Validate that all burn IDs exist in the admission_data collection.
        
        Returns:
            List[str]: List of burn IDs that don't have matching admission records
        """
        # Get all burn IDs
        burn_ids_cursor = db_connection.db.burns.distinct("ID")
        burn_ids = await burn_ids_cursor
        
        # Get all admission IDs
        admission_ids_cursor = db_connection.db.admission_data.distinct("ID")
        admission_ids = await admission_ids_cursor
        
        # Convert to sets for efficient comparison
        burn_ids_set = set(burn_ids)
        admission_ids_set = set(admission_ids)
        
        # Find burns that don't have corresponding admission records
        orphaned_burns = list(burn_ids_set - admission_ids_set)
        orphaned_burns.sort()  # Sort for consistent output
        
        # Store for later use
        self.orphaned_burns = orphaned_burns
        
        return orphaned_burns
    
    async def find_missing_references(self) -> List[str]:
        """
        Find admission records that don't have corresponding burn records.
        
        Returns:
            List[str]: List of admission IDs that don't have matching burn records
        """
        # Get all burn IDs
        burn_ids_cursor = db_connection.db.burns.distinct("ID")
        burn_ids = await burn_ids_cursor
        
        # Get all admission IDs
        admission_ids_cursor = db_connection.db.admission_data.distinct("ID")
        admission_ids = await admission_ids_cursor
        
        # Convert to sets for efficient comparison
        burn_ids_set = set(burn_ids)
        admission_ids_set = set(admission_ids)
        
        # Find admissions that don't have corresponding burn records
        missing_references = list(admission_ids_set - burn_ids_set)
        missing_references.sort()  # Sort for consistent output
        
        # Store for later use
        self.missing_references = missing_references
        
        return missing_references
    
    def create_duplicate_table(self) -> Table:
        """
        Create a rich table displaying duplicate IDs.
        
        Returns:
            Table: Rich table with duplicate ID information
        """
        table = Table(
            title="Duplicate Burns IDs",
            show_lines=True,
            title_style="bold red",
            header_style="bold cyan"
        )
        
        table.add_column("ID", style="cyan")
        table.add_column("Count", style="yellow")
        table.add_column("Document IDs", style="green")
        
        for duplicate in self.duplicate_ids:
            id_value = duplicate["_id"]
            count = duplicate["count"]
            doc_ids = [str(doc.get("_id", "Unknown")) for doc in duplicate["docs"]]
            doc_ids_str = ", ".join(doc_ids[:3])
            if len(doc_ids) > 3:
                doc_ids_str += f"... ({len(doc_ids) - 3} more)"
                
            table.add_row(id_value, str(count), doc_ids_str)
        
        return table
    
    def create_reference_table(self) -> Table:
        """
        Create a rich table displaying reference inconsistencies.
        
        Returns:
            Table: Rich table with orphaned burns and missing references
        """
        table = Table(
            title="Burns-Admission Reference Inconsistencies",
            show_lines=True,
            title_style="bold yellow",
            header_style="bold cyan"
        )
        
        table.add_column("Issue Type", style="cyan")
        table.add_column("Count", style="yellow")
        table.add_column("Examples", style="green")
        
        # Orphaned burns (burns with no matching admission record)
        examples = ", ".join(self.orphaned_burns[:3])
        if len(self.orphaned_burns) > 3:
            examples += f"... ({len(self.orphaned_burns) - 3} more)"
            
        table.add_row(
            "Orphaned Burns",
            str(len(self.orphaned_burns)),
            examples
        )
        
        # Missing references (admissions with no matching burn record)
        examples = ", ".join(self.missing_references[:3])
        if len(self.missing_references) > 3:
            examples += f"... ({len(self.missing_references) - 3} more)"
            
        table.add_row(
            "Missing Burn Records",
            str(len(self.missing_references)),
            examples
        )
        
        return table
    
    async def fix_duplicate_ids(self) -> bool:
        """
        Fix duplicate IDs by keeping the most recent document and removing others.
        
        Returns:
            bool: True if fixed successfully, False otherwise
        """
        if not self.duplicate_ids:
            console.print("[yellow]No duplicate IDs to fix[/yellow]")
            return False
        
        success_count = 0
        for duplicate in self.duplicate_ids:
            id_value = duplicate["_id"]
            docs = duplicate["docs"]
            
            # Sort documents by updated_at in descending order (most recent first)
            # If updated_at doesn't exist, use created_at; if neither exists, keep as is
            docs.sort(key=lambda x: x.get("updated_at", x.get("created_at", datetime.min)), reverse=True)
            
            # Keep the most recent document and delete others
            for doc in docs[1:]:
                doc_id = doc.get("_id")
                if doc_id:
                    result = await db_connection.db.burns.delete_one({"_id": doc_id})
                    if result.deleted_count > 0:
                        success_count += 1
                        console.print(f"[green]Deleted duplicate document with _id {doc_id} for ID {id_value}[/green]")
                    else:
                        console.print(f"[red]Failed to delete duplicate document with _id {doc_id} for ID {id_value}[/red]")
        
        console.print(f"[green]Fixed {success_count} duplicate documents[/green]")
        return True
    
    async def verify_and_report(self) -> None:
        """
        Run all verification checks and display a comprehensive report.
        """
        console.print(Panel("Starting Burns ID verification", title="Burns ID Verifier", border_style="blue"))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            # Check for duplicate IDs
            task = progress.add_task("[cyan]Checking for duplicate IDs...", total=1)
            await self.check_id_uniqueness()
            progress.update(task, advance=1)
            
            # Validate burn references
            task = progress.add_task("[cyan]Validating burn references...", total=1)
            await self.validate_burn_references()
            progress.update(task, advance=1)
            
            # Find missing references
            task = progress.add_task("[cyan]Finding missing references...", total=1)
            await self.find_missing_references()
            progress.update(task, advance=1)
        
        # Display duplicate IDs report
        if self.duplicate_ids:
            console.print("\n[bold red]Found duplicate IDs in burns collection![/bold red]")
            console.print(self.create_duplicate_table())
        else:
            console.print("\n[bold green]No duplicate IDs found in burns collection![/bold green]")
        
        # Display reference inconsistencies
        if self.orphaned_burns or self.missing_references:
            console.print("\n[bold yellow]Found burns-admission reference inconsistencies![/bold yellow]")
            console.print(self.create_reference_table())
        else:
            console.print("\n[bold green]All burns have matching admission records![/bold green]")
        
        # Offer to fix duplicate IDs
        if self.duplicate_ids and Confirm.ask("\nDo you want to fix duplicate IDs?", default=False):
            await self.fix_duplicate_ids()
            
            # Re-check for duplicate IDs after fixing
            console.print("\n[cyan]Re-checking for duplicate IDs after fixes...[/cyan]")
            duplicate_groups = await self.check_id_uniqueness()
            if duplicate_groups:
                console.print("[bold red]Some duplicate IDs still exist after fixes![/bold red]")
                console.print(self.create_duplicate_table())
            else:
                console.print("[bold green]All duplicate IDs have been fixed![/bold green]")


async def main():
    """Main entry point for the Burns ID Uniqueness Verification Tool."""
    try:
        # Connect to the database
        await db_connection.connect()
        
        # Create and run the verifier
        verifier = BurnsIdVerifier()
        await verifier.verify_and_report()
        
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        return 1
    finally:
        # Close the database connection
        await db_connection.close()
    
    return 0


if __name__ == "__main__":
    asyncio.run(main())