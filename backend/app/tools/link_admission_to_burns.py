"""
MongoDB Document Reference Updater

This module adds a 'burns' reference field to admission data documents,
linking them to the corresponding burns documents with the same ID.
The tool validates relationships, reports issues, and ensures atomic updates.
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional, Any, Tuple
import logging

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.prompt import Confirm

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent.parent
sys.path.append(str(parent_dir))

from backend.app.config.database import db_connection

# Initialize console for rich output
console = Console()

class AdmissionBurnsLinker:
    """
    Service for establishing references between admission_data and burns documents.
    
    This class provides tools to:
    1. Find matches between admission_data and burns collections based on ID
    2. Update admission_data documents to include references to burns documents
    3. Validate the integrity of references both before and after update
    4. Generate comprehensive reports on the linking process
    5. Support atomic updates through MongoDB transactions
    """
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize the admission-burns document linker.
        
        Args:
            dry_run (bool): If True, no actual updates will be performed
        """
        self.dry_run = dry_run
        self.matched_ids = []
        self.unmatched_admission_ids = []
        self.unmatched_burns_ids = []
        self.success_count = 0
        self.error_count = 0
        self.errors = []
        
    async def find_matching_documents(self) -> Dict[str, Dict]:
        """
        Find admission and burns documents that match by ID.
        
        Returns:
            Dict[str, Dict]: Dictionary mapping IDs to pairs of documents
        """
        # Get all admission document IDs
        admission_ids_cursor = db_connection.db.admission_data.distinct("ID")
        admission_ids = await admission_ids_cursor
        
        # Get all burns document IDs
        burns_ids_cursor = db_connection.db.burns.distinct("ID")
        burns_ids = await burns_ids_cursor
        
        # Convert to sets for efficient comparison
        admission_ids_set = set(admission_ids)
        burns_ids_set = set(burns_ids)
        
        # Find matching and unmatching IDs
        matching_ids = admission_ids_set.intersection(burns_ids_set)
        self.matched_ids = list(matching_ids)
        self.unmatched_admission_ids = list(admission_ids_set - burns_ids_set)
        self.unmatched_burns_ids = list(burns_ids_set - admission_ids_set)
        
        # Sort lists for consistent output
        self.matched_ids.sort()
        self.unmatched_admission_ids.sort()
        self.unmatched_burns_ids.sort()
        
        console.print(f"[green]Found {len(self.matched_ids)} matching document pairs[/green]")
        console.print(f"[yellow]Found {len(self.unmatched_admission_ids)} admission documents without matching burns[/yellow]")
        console.print(f"[yellow]Found {len(self.unmatched_burns_ids)} burns documents without matching admission[/yellow]")
        
        return {id: {"admission_id": id, "burns_id": id} for id in self.matched_ids}
    
    async def check_existing_references(self) -> Tuple[int, List[str]]:
        """
        Check for existing burns references in admission_data documents.
        
        Returns:
            Tuple[int, List[str]]: Count of documents with references and list of their IDs
        """
        # Find documents that already have a burns field
        cursor = db_connection.db.admission_data.find(
            {"burns": {"$exists": True}},
            {"ID": 1}
        )
        
        documents = await cursor.to_list(length=None)
        existing_refs = [doc.get("ID") for doc in documents if "ID" in doc]
        
        console.print(f"[blue]Found {len(existing_refs)} admission documents with existing 'burns' references[/blue]")
        
        return len(existing_refs), existing_refs
    
    def create_matching_table(self) -> Table:
        """
        Create a rich table displaying matching status between collections.
        
        Returns:
            Table: Rich table with matching information
        """
        table = Table(
            title="Collection Matching Summary",
            show_lines=True,
            title_style="bold blue",
            header_style="bold cyan"
        )
        
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="yellow")
        table.add_column("Examples", style="green")
        
        # Matched IDs
        examples = ", ".join(self.matched_ids[:3])
        if len(self.matched_ids) > 3:
            examples += f"... ({len(self.matched_ids) - 3} more)"
            
        table.add_row(
            "Matched Documents",
            str(len(self.matched_ids)),
            examples
        )
        
        # Unmatched admission IDs
        examples = ", ".join(self.unmatched_admission_ids[:3])
        if len(self.unmatched_admission_ids) > 3:
            examples += f"... ({len(self.unmatched_admission_ids) - 3} more)"
            
        table.add_row(
            "Admissions Without Burns",
            str(len(self.unmatched_admission_ids)),
            examples
        )
        
        # Unmatched burns IDs
        examples = ", ".join(self.unmatched_burns_ids[:3])
        if len(self.unmatched_burns_ids) > 3:
            examples += f"... ({len(self.unmatched_burns_ids) - 3} more)"
            
        table.add_row(
            "Burns Without Admission",
            str(len(self.unmatched_burns_ids)),
            examples
        )
        
        return table
    
    def create_results_table(self) -> Table:
        """
        Create a rich table displaying update results.
        
        Returns:
            Table: Rich table with update results
        """
        table = Table(
            title="Update Results",
            show_lines=True,
            title_style="bold magenta",
            header_style="bold cyan"
        )
        
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")
        
        table.add_row("Documents to Update", str(len(self.matched_ids)))
        table.add_row("Successfully Updated", f"[green]{self.success_count}[/green]")
        table.add_row("Failed Updates", f"[red]{self.error_count}[/red]")
        
        if self.dry_run:
            table.add_row("Mode", "[yellow]DRY RUN - No actual updates performed[/yellow]")
        
        return table
    
    def create_errors_table(self) -> Optional[Table]:
        """
        Create a rich table displaying error details.
        
        Returns:
            Optional[Table]: Rich table with error details or None if no errors
        """
        if not self.errors:
            return None
            
        table = Table(
            title="Update Errors",
            show_lines=True,
            title_style="bold red",
            header_style="bold cyan"
        )
        
        table.add_column("ID", style="cyan")
        table.add_column("Error", style="red")
        
        for error in self.errors:
            table.add_row(error["id"], error["message"])
            
        return table
    
    async def update_admission_references(self) -> bool:
        """
        Update admission_data documents to include references to burns documents.
        
        Returns:
            bool: True if all updates were successful, False otherwise
        """
        if not self.matched_ids:
            console.print("[yellow]No matching IDs found to update[/yellow]")
            return False
            
        console.print(Panel(f"Updating {len(self.matched_ids)} admission documents with burns references", 
                            title="Starting Update Process", 
                            border_style="blue"))
        
        if self.dry_run:
            console.print("[yellow]DRY RUN MODE: No actual updates will be performed[/yellow]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("[cyan]{task.completed}/{task.total}[/cyan]"),
            transient=True
        ) as progress:
            # Create a progress task
            task = progress.add_task(
                "[cyan]Updating admission documents...", 
                total=len(self.matched_ids)
            )
            
            # Use transactions for atomic updates if available
            session = None
            try:
                # Create MongoDB session (requires MongoDB 4.0+)
                session = await db_connection.client.start_session()
                
                for doc_id in self.matched_ids:
                    if self.dry_run:
                        # In dry run mode, just simulate success
                        self.success_count += 1
                        progress.update(task, advance=1)
                        continue
                        
                    try:
                        async with session.start_transaction():
                            # Get the burns document to reference
                            burns_doc = await db_connection.db.burns.find_one(
                                {"ID": doc_id},
                                {"_id": 1}
                            )
                            
                            if not burns_doc or "_id" not in burns_doc:
                                raise ValueError(f"Could not find burns document with ID: {doc_id}")
                            
                            # Update the admission document with a reference to the burns document
                            result = await db_connection.db.admission_data.update_one(
                                {"ID": doc_id},
                                {"$set": {
                                    "burns": str(burns_doc["_id"]),
                                    "updated_at": datetime.now()
                                }},
                                session=session
                            )
                            
                            if result.modified_count == 1:
                                self.success_count += 1
                            else:
                                self.error_count += 1
                                self.errors.append({
                                    "id": doc_id,
                                    "message": f"Document not updated (modified_count={result.modified_count})"
                                })
                                
                    except Exception as e:
                        self.error_count += 1
                        self.errors.append({
                            "id": doc_id,
                            "message": str(e)
                        })
                        
                    progress.update(task, advance=1)
                    
            except Exception as e:
                console.print(f"[red]Error starting MongoDB session: {str(e)}[/red]")
                console.print("[yellow]Falling back to non-transactional updates[/yellow]")
                
                # Fall back to non-transactional updates
                session = None
                
                # Reset counters from failed transaction attempts
                self.success_count = 0
                self.error_count = 0
                self.errors = []
                progress.update(task, completed=0)
                
                # Perform updates without transactions
                for doc_id in self.matched_ids:
                    if self.dry_run:
                        # In dry run mode, just simulate success
                        self.success_count += 1
                        progress.update(task, advance=1)
                        continue
                        
                    try:
                        # Get the burns document to reference
                        burns_doc = await db_connection.db.burns.find_one(
                            {"ID": doc_id},
                            {"_id": 1}
                        )
                        
                        if not burns_doc or "_id" not in burns_doc:
                            raise ValueError(f"Could not find burns document with ID: {doc_id}")
                        
                        # Update the admission document with a reference to the burns document
                        result = await db_connection.db.admission_data.update_one(
                            {"ID": doc_id},
                            {"$set": {
                                "burns": str(burns_doc["_id"]),
                                "updated_at": datetime.now()
                            }}
                        )
                        
                        if result.modified_count == 1:
                            self.success_count += 1
                        else:
                            self.error_count += 1
                            self.errors.append({
                                "id": doc_id,
                                "message": f"Document not updated (modified_count={result.modified_count})"
                            })
                            
                    except Exception as e:
                        self.error_count += 1
                        self.errors.append({
                            "id": doc_id,
                            "message": str(e)
                        })
                        
                    progress.update(task, advance=1)
            
            finally:
                # Close session if open
                if session:
                    await session.end_session()
        
        return self.error_count == 0
    
    async def verify_references(self) -> Tuple[int, int]:
        """
        Verify that all intended references were correctly established.
        
        Returns:
            Tuple[int, int]: Count of correct references and count of missing/incorrect references
        """
        correct_count = 0
        incorrect_count = 0
        
        if self.dry_run:
            console.print("[yellow]Skipping verification in dry run mode[/yellow]")
            return 0, 0
            
        console.print("[cyan]Verifying references...[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task("[cyan]Checking references...", total=len(self.matched_ids))
            
            for doc_id in self.matched_ids:
                # Get the burns document ID
                burns_doc = await db_connection.db.burns.find_one(
                    {"ID": doc_id},
                    {"_id": 1}
                )
                
                if not burns_doc or "_id" not in burns_doc:
                    incorrect_count += 1
                    continue
                    
                burns_id = str(burns_doc["_id"])
                
                # Get the admission document
                admission_doc = await db_connection.db.admission_data.find_one(
                    {"ID": doc_id},
                    {"burns": 1}
                )
                
                if not admission_doc:
                    incorrect_count += 1
                    continue
                    
                # Check if the reference is correct
                if admission_doc.get("burns") == burns_id:
                    correct_count += 1
                else:
                    incorrect_count += 1
                    
                progress.update(task, advance=1)
                
        console.print(f"[green]Successfully verified {correct_count} references[/green]")
        if incorrect_count > 0:
            console.print(f"[red]Found {incorrect_count} incorrect or missing references[/red]")
            
        return correct_count, incorrect_count
    
    async def run(self) -> None:
        """
        Run the full admission-burns linking process.
        """
        console.print(Panel("Starting Admission-Burns Linking Process", title="Document Reference Updater", border_style="blue"))
        
        # Connect to the database
        console.print("[cyan]Connecting to database...[/cyan]")
        await db_connection.connect()
        
        try:
            # Step 1: Find matching documents
            console.print("\n[bold blue]Step 1:[/bold blue] Finding matching documents...")
            await self.find_matching_documents()
            console.print(self.create_matching_table())
            
            # Step 2: Check for existing references
            console.print("\n[bold blue]Step 2:[/bold blue] Checking existing references...")
            existing_count, existing_ids = await self.check_existing_references()
            
            # Step 3: Update admission documents with references to burns
            if len(self.matched_ids) > 0:
                console.print("\n[bold blue]Step 3:[/bold blue] Updating admission documents...")
                
                # Ask for confirmation before proceeding
                if not self.dry_run and not Confirm.ask(
                    f"Ready to update {len(self.matched_ids)} admission documents. Continue?",
                    default=False
                ):
                    console.print("[yellow]Update cancelled by user[/yellow]")
                    return
                
                await self.update_admission_references()
                console.print(self.create_results_table())
                
                if errors_table := self.create_errors_table():
                    console.print("\n")
                    console.print(errors_table)
                    
                # Step 4: Verify references
                console.print("\n[bold blue]Step 4:[/bold blue] Verifying references...")
                if not self.dry_run:
                    correct_count, incorrect_count = await self.verify_references()
                    
                    verification_result = (
                        f"[green]✓ SUCCESS: All {correct_count} references verified correctly[/green]"
                        if incorrect_count == 0 else
                        f"[red]⚠ WARNING: Found {incorrect_count} incorrect references[/red]"
                    )
                    
                    console.print(Panel(verification_result, title="Verification Result"))
            else:
                console.print("[yellow]No matching documents to update[/yellow]")
                
        except Exception as e:
            console.print(f"[bold red]Error during linking process: {str(e)}[/bold red]")
        finally:
            # Close the database connection
            await db_connection.close()


async def main():
    """Main entry point for the Admission-Burns Linking Tool."""
    try:
        # Parse command line arguments
        import argparse
        parser = argparse.ArgumentParser(description='Link admission_data documents to burns documents')
        parser.add_argument('--dry-run', action='store_true', help='Run without making actual changes')
        args = parser.parse_args()
        
        # Create and run the linker
        linker = AdmissionBurnsLinker(dry_run=args.dry_run)
        await linker.run()
        
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))