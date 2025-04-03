# Module: document_reference_manager.py
"""
Document Reference Manager

This module provides tools for managing references between MongoDB collections in the Burns Critical Care Unit
Information System. It enables finding matching documents across collections and creating references between them,
particularly useful for linking admission data with burns records.
"""

# Dependencies:
# - logging: For structured logging of operations and errors
# - typing: For type hints to improve code readability and enable static type checking
# - contextlib: For implementing proper resource management via context managers
# - rich: For beautiful terminal output and interactive user interfaces
# - functools: For function decorators
# - pymongo: For MongoDB database operations

import logging
import sys
from typing import Dict, List, Set, Optional, Any, Callable, Tuple, ContextManager
from contextlib import contextmanager
import functools

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm

from ..config.database_sync import db as db_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@contextmanager
def null_console_context() -> ContextManager[Console]:
    """
    Context manager for creating a null console that properly closes file resources.
    
    Returns:
        ContextManager[Console]: A console that writes to /dev/null with proper resource management
    
    Yields:
        Console: The configured console object
    """
    try:
        file_obj = open('/dev/null', 'w')
        console = Console(file=file_obj)
        yield console
    finally:
        file_obj.close()

def ensure_db_connection(func: Callable) -> Callable:
    """
    Decorator to ensure database connection is established before function execution.
    
    This decorator wraps methods that require database access, handling connection
    establishment and error management. It doesn't close the connection after each
    operation to allow for efficient connection pooling.
    
    Args:
        func: The function to wrap with database connection handling
        
    Returns:
        Callable: Wrapped function with connection handling
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        """Inner wrapper function that handles connection establishment"""
        try:
            # Ensure database connection is established
            if not db_connection.connect():
                self.console.print("[red]Failed to connect to database[/red]")
                return None
            
            # Call the original function
            result = func(self, *args, **kwargs)
            return result
        except Exception as e:
            self.console.print(f"[red]Error in {func.__name__}: {str(e)}[/red]")
            logger.exception(f"Error in {func.__name__}")
            return None
    
    return wrapper


class DocumentReferenceManager:
    """
    Manages references between documents across MongoDB collections.
    
    This class provides functionality for finding matching documents between collections,
    checking existing references, and creating or updating references between related documents.
    It's designed specifically for medical information systems where proper linking of patient
    data across different collections is crucial for comprehensive patient records.
    
    The class follows the Command pattern, with methods to execute specific data linking
    operations, and also incorporates Builder pattern elements for configurable reference creation.
    """
    
    def __init__(self, 
                 source_collection: str, 
                 target_collection: str, 
                 source_field: str = "ID", 
                 target_field: str = "ID", 
                 reference_field: str = "burns",
                 dry_run: bool = False,
                 console: Optional[Console] = None):
        """
        Initialize the DocumentReferenceManager.
        
        Args:
            source_collection: Name of the source collection (e.g., "admission_data")
            target_collection: Name of the target collection (e.g., "burns")
            source_field: Field in source collection to match on (default: "ID")
            target_field: Field in target collection to match on (default: "ID")
            reference_field: Field to store the reference in source documents (default: "burns")
            dry_run: If True, don't make actual changes to the database (default: False)
            console: Rich console for output (default: create new console)
        """
        self.source_collection = source_collection
        self.target_collection = target_collection
        self.source_field = source_field
        self.target_field = target_field
        self.reference_field = reference_field
        self.dry_run = dry_run
        self.console = console or Console()
        
        # Statistics and tracking
        self.matched_ids: Dict[str, Dict[str, Any]] = {}
        self.unmatched_source_ids: Set[str] = set()
        self.unmatched_target_ids: Set[str] = set()
        self.success_count = 0
        self.error_count = 0
    
    @ensure_db_connection
    def find_matching_documents(self) -> Dict[str, Dict[str, Any]]:
        """
        Find documents in both collections that match on the specified fields.
        
        This method:
        1. Retrieves distinct ID values from both collections
        2. Finds the intersection of these IDs (matching pairs)
        3. Retrieves the full documents for each matching ID
        4. Builds a dictionary mapping match values to document details
        5. Tracks unmatched documents for reporting
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of matched documents with matched value as key,
                                      containing source_id, target_id, and match_value
        """
        # Get distinct IDs from both collections
        self.console.print(f"\n[bold blue]Finding matching documents...[/bold blue]")
        
        source_ids = db_connection.db.get_collection(self.source_collection).distinct(self.source_field)
        target_ids = db_connection.db.get_collection(self.target_collection).distinct(self.target_field)
        
        # Convert to sets for efficient comparison
        source_ids_set = set(source_ids)
        target_ids_set = set(target_ids)
        
        # Find the intersection (matching IDs)
        matching_ids = source_ids_set.intersection(target_ids_set)
        
        # Track unmatched IDs
        self.unmatched_source_ids = source_ids_set - target_ids_set
        self.unmatched_target_ids = target_ids_set - source_ids_set
        
        # Prepare result dictionary
        result = {}
        
        # Build matched documents dictionary
        for id_value in matching_ids:
            source_doc = db_connection.db.get_collection(self.source_collection).find_one({self.source_field: id_value})
            target_doc = db_connection.db.get_collection(self.target_collection).find_one({self.target_field: id_value})
            
            if source_doc and target_doc:
                result[id_value] = {
                    "source_id": str(source_doc["_id"]),
                    "target_id": str(target_doc["_id"]),
                    "match_value": id_value
                }
        
        # Store matched IDs for later use
        self.matched_ids = result
        
        # Print results
        self.console.print(f"[green]Found {len(result)} matching documents[/green]")
        self.console.print(f"[yellow]Found {len(self.unmatched_source_ids)} unmatched source documents[/yellow]")
        self.console.print(f"[yellow]Found {len(self.unmatched_target_ids)} unmatched target documents[/yellow]")
        
        return result
    
    @ensure_db_connection
    def check_existing_references(self) -> Tuple[int, List[str]]:
        """
        Check how many documents already have the reference field populated.
        
        This helps identify which documents already have references established,
        avoiding unnecessary updates and providing insight into the current state
        of the data linkage.
        
        Returns:
            tuple[int, List[str]]: A tuple containing:
                - Count of documents with existing references
                - List of their ID values for reference
        """
        self.console.print(f"\n[bold blue]Checking existing references...[/bold blue]")
        
        # Find documents where the reference field exists
        query = {self.reference_field: {"$exists": True}}
        documents = list(db_connection.db.get_collection(self.source_collection).find(query, {self.source_field: 1}))
        
        # Extract IDs
        ids = [doc.get(self.source_field) for doc in documents if self.source_field in doc]
        
        self.console.print(f"[green]Found {len(documents)} documents with existing references[/green]")
        
        return len(documents), ids
    
    def create_matching_table(self) -> Table:
        """
        Create a Rich table showing matching status between collections.
        
        This generates a formatted table for terminal display that summarizes:
        - Total number of matched documents
        - Number of unmatched source documents
        - Number of unmatched target documents 
        - Success and error counts if operations were performed
        
        Returns:
            Table: Rich table with matching information for display
        """
        table = Table(title=f"Document Matching Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")
        
        table.add_row("Total Matched Documents", str(len(self.matched_ids)))
        table.add_row("Unmatched Source Documents", str(len(self.unmatched_source_ids)))
        table.add_row("Unmatched Target Documents", str(len(self.unmatched_target_ids)))
        
        if self.success_count or self.error_count:
            table.add_row("Successfully Updated", str(self.success_count))
            table.add_row("Failed Updates", str(self.error_count))
        
        return table
    
    @ensure_db_connection
    def update_references(self) -> bool:
        """
        Update references in source documents to point to matching target documents.
        
        This method iterates through previously identified matching document pairs and:
        1. Updates the source document to include a reference to the target document
        2. Tracks success and failure counts
        3. Handles error conditions gracefully
        
        In dry-run mode, it simulates updates without modifying the database.
        
        Returns:
            bool: True if all operations were successful, False otherwise
        """
        if not self.matched_ids:
            self.console.print("[yellow]No matched documents found. Run find_matching_documents() first.[/yellow]")
            return False
            
        self.console.print(f"\n[bold blue]Updating references...[/bold blue]")
        
        # Reset counters
        self.success_count = 0
        self.error_count = 0
        
        if self.dry_run:
            self.console.print("[yellow]DRY RUN: No actual changes will be made[/yellow]")
        
        # Process each matched pair
        for match_value, doc_ids in self.matched_ids.items():
            source_id = doc_ids["source_id"]
            target_id = doc_ids["target_id"]
            
            try:
                if not self.dry_run:
                    # Update the source document with a reference to the target
                    result = db_connection.db.get_collection(self.source_collection).update_one(
                        {"_id": source_id},
                        {"$set": {self.reference_field: target_id}}
                    )
                    
                    if result.modified_count > 0:
                        self.success_count += 1
                    else:
                        self.error_count += 1
                        self.console.print(f"[yellow]No changes made for document {match_value}[/yellow]")
                else:
                    # In dry run mode, just count as success
                    self.success_count += 1
                    
            except Exception as e:
                self.error_count += 1
                self.console.print(f"[red]Error updating reference for {match_value}: {str(e)}[/red]")
                logger.exception(f"Error updating reference for {match_value}")
        
        # Print results
        if self.dry_run:
            self.console.print(f"[green]Would update {self.success_count} documents successfully[/green]")
        else:
            self.console.print(f"[green]Updated {self.success_count} documents successfully[/green]")
        
        if self.error_count > 0:
            self.console.print(f"[red]Failed to update {self.error_count} documents[/red]")
            
        return self.error_count == 0
    
    def run(self) -> bool:
        """
        Run the complete reference management process.
        
        This is the main entry point for executing the document reference management workflow.
        It performs all steps in sequence with appropriate user feedback:
        1. Display header information
        2. Find matching documents across collections
        3. Check for existing references
        4. Show matching analysis
        5. Update references with optional user confirmation (non-dry-run mode)
        
        Returns:
            bool: True if all operations were successful, False otherwise
        """
        try:
            # Connect to database
            if not db_connection.connect():
                self.console.print("[red]Failed to connect to database[/red]")
                return False
                
            # Show a header
            self.console.print(Panel(
                f"Document Reference Manager: {self.source_collection} → {self.target_collection}",
                border_style="blue"
            ))
            
            # Step 1: Find matching documents
            self.console.print("[bold blue]Step 1:[/bold blue] Finding matching documents")
            matching_docs = self.find_matching_documents()
            
            if not matching_docs:
                self.console.print("[yellow]No matching documents found. Process aborted.[/yellow]")
                return False
                
            # Step 2: Check existing references
            self.console.print("[bold blue]Step 2:[/bold blue] Checking existing references")
            existing_count, existing_ids = self.check_existing_references()
            
            # Step 3: Show matching table
            self.console.print("[bold blue]Step 3:[/bold blue] Analyzing matches")
            matching_table = self.create_matching_table()
            self.console.print(matching_table)
            
            # Step 4: Confirm and update references
            if not self.dry_run:
                self.console.print("[bold blue]Step 4:[/bold blue] Updating references")
                if Confirm.ask("\nProceed with updating references?", default=False):
                    success = self.update_references()
                    
                    # Show final status
                    self.console.print(self.create_matching_table())
                    return success
                else:
                    self.console.print("[yellow]Operation cancelled by user[/yellow]")
                    return False
            else:
                self.console.print("[bold blue]Step 4:[/bold blue] Simulating updates (dry run)")
                success = self.update_references()
                
                # Show final status
                self.console.print(self.create_matching_table())
                return success
                
        except Exception as e:
            self.console.print(f"[red]Error: {str(e)}[/red]")
            logger.exception("Error in DocumentReferenceManager.run()")
            return False
        finally:
            # Close database connection
            db_connection.close()


class AdmissionBurnsLinker:
    """
    Specialized class for linking admission documents to burns documents.
    
    This class implements the Facade pattern by providing a simplified interface 
    specifically for linking admission_data to burns collections, making it easier
    for users to perform this common task without configuring the underlying
    DocumentReferenceManager directly.
    """
    
    def __init__(self, dry_run: bool = False, console: Optional[Console] = None):
        """
        Initialize the AdmissionBurnsLinker.
        
        Creates a pre-configured DocumentReferenceManager specifically for linking
        admission_data to burns collections using the patient ID as the matching field.
        
        Args:
            dry_run: If True, don't make actual changes to the database (default: False)
            console: Rich console for output (default: create new console)
        """
        self.console = console or Console()
        self.manager = DocumentReferenceManager(
            source_collection="admission_data",
            target_collection="burns",
            source_field="ID",
            target_field="ID",
            reference_field="burns",
            dry_run=dry_run,
            console=self.console
        )
    
    def find_matching_documents(self) -> Dict[str, Dict[str, Any]]:
        """
        Find documents in admission_data and burns collections that match on ID.
        
        Delegates to the DocumentReferenceManager to find matching documents.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of matched documents
        """
        return self.manager.find_matching_documents()
    
    def check_existing_references(self) -> Tuple[int, List[str]]:
        """
        Check how many admission documents already have burns references.
        
        Delegates to the DocumentReferenceManager to check existing references.
        
        Returns:
            tuple[int, List[str]]: Count of documents with existing references and their IDs
        """
        return self.manager.check_existing_references()
    
    def create_matching_table(self) -> Table:
        """
        Create a Rich table showing matching status between collections.
        
        Delegates to the DocumentReferenceManager to create a matching table.
        
        Returns:
            Table: Rich table with matching information
        """
        return self.manager.create_matching_table()
    
    def update_references(self) -> bool:
        """
        Update references in admission documents to point to matching burns documents.
        
        Delegates to the DocumentReferenceManager to update references.
        
        Returns:
            bool: True if all operations were successful, False otherwise
        """
        return self.manager.update_references()
    
    def run(self) -> bool:
        """
        Run the complete admission to burns linking process.
        
        This is the main entry point for linking admission documents to burns documents.
        It delegates to the DocumentReferenceManager to execute the complete reference
        management workflow.
        
        Returns:
            bool: True if all operations were successful, False otherwise
        """
        return self.manager.run()


def main() -> int:
    """
    Main function to run the document reference manager interactively.
    
    Creates a CLI menu for document reference management operations and
    handles user input with appropriate feedback and error handling.
    
    Returns:
        int: Exit code (0 for success, 1 for errors)
    """
    console = Console()
    
    try:
        while True:
            console.print(Panel("Document Reference Manager", border_style="blue"))
            
            console.print("\n[bold cyan]Available Operations:[/bold cyan]")
            console.print("1. Link Admission Data to Burns")
            console.print("2. Link Custom Collections")
            console.print("3. Exit")
            
            choice = console.input("\n[bold green]Select operation (1-3): [/bold green]")
            
            if choice == "1":
                dry_run = Confirm.ask("Run in dry-run mode (no actual changes)?", default=True)
                linker = AdmissionBurnsLinker(dry_run=dry_run, console=console)
                success = linker.run()
                
                if success:
                    console.print("[green]Operation completed successfully[/green]")
                else:
                    console.print("[yellow]Operation completed with warnings[/yellow]")
                    
            elif choice == "2":
                source = console.input("[cyan]Source collection name: [/cyan]")
                target = console.input("[cyan]Target collection name: [/cyan]")
                source_field = console.input("[cyan]Source field to match on [ID]: [/cyan]") or "ID"
                target_field = console.input("[cyan]Target field to match on [ID]: [/cyan]") or "ID"
                reference_field = console.input("[cyan]Reference field to create [reference]: [/cyan]") or "reference"
                dry_run = Confirm.ask("Run in dry-run mode (no actual changes)?", default=True)
                
                manager = DocumentReferenceManager(
                    source_collection=source,
                    target_collection=target,
                    source_field=source_field,
                    target_field=target_field,
                    reference_field=reference_field,
                    dry_run=dry_run,
                    console=console
                )
                
                success = manager.run()
                
                if success:
                    console.print("[green]Operation completed successfully[/green]")
                else:
                    console.print("[yellow]Operation completed with warnings[/yellow]")
                    
            elif choice == "3":
                console.print("[blue]Exiting...[/blue]")
                return 0
            else:
                console.print("[red]Invalid choice. Please select 1-3.[/red]")
            
            # Use 'input' directly to avoid leaking file handles
            input("\n[yellow]Press Enter to continue...[/yellow]")
        
    except KeyboardInterrupt:
        console.print("[yellow]Operation cancelled by user[/yellow]")
        return 1
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        logger.exception("Error in main function")
        return 1


if __name__ == "__main__":
    sys.exit(main())


