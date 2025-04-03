"""
Document Reference Manager CLI

Command-line interface for linking documents across MongoDB collections.
Usage:
    python scripts/link_collections.py --interactive
    python scripts/link_collections.py --admission-to-burns [--dry-run]
    python scripts/link_collections.py --source=collection1 --target=collection2 [options]
"""

import os
import sys
from pathlib import Path
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm

# Add the parent directory to the path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

from backend.app.tools.document_reference_manager import DocumentReferenceManager, AdmissionBurnsLinker

console = Console()

def link_admissions_to_burns(dry_run: bool = False) -> bool:
    """Link admission_data documents to burns documents"""
    try:
        # Create linker
        linker = AdmissionBurnsLinker(dry_run=dry_run, console=console)
        
        # Run the linker
        success = linker.run()
        
        return success
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return False

def link_collections(
    source: str, 
    target: str, 
    source_field: str = "ID", 
    target_field: str = "ID", 
    reference_field: str = "reference", 
    dry_run: bool = False
) -> bool:
    """Link documents between arbitrary collections"""
    try:
        # Create manager
        manager = DocumentReferenceManager(
            source_collection=source,
            target_collection=target,
            source_field=source_field,
            target_field=target_field,
            reference_field=reference_field,
            dry_run=dry_run,
            console=console
        )
        
        # Run the manager
        success = manager.run()
        
        return success
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return False

def main():
    """Interactive menu for collection management"""
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
                success = link_admissions_to_burns(dry_run=dry_run)
                if not success:
                    console.print("[red]Operation failed or completed with warnings[/red]")
                    
            elif choice == "2":
                source = console.input("[cyan]Source collection name: [/cyan]")
                target = console.input("[cyan]Target collection name: [/cyan]")
                source_field = console.input("[cyan]Source field to match on [ID]: [/cyan]") or "ID"
                target_field = console.input("[cyan]Target field to match on [ID]: [/cyan]") or "ID"
                reference_field = console.input("[cyan]Reference field to create [reference]: [/cyan]") or "reference"
                dry_run = Confirm.ask("Run in dry-run mode (no actual changes)?", default=True)
                
                success = link_collections(
                    source=source,
                    target=target,
                    source_field=source_field,
                    target_field=target_field,
                    reference_field=reference_field,
                    dry_run=dry_run
                )
                
                if not success:
                    console.print("[red]Operation failed or completed with warnings[/red]")
                    
            elif choice == "3":
                console.print("[blue]Exiting...[/blue]")
                break
            else:
                console.print("[red]Invalid choice. Please select 1-3.[/red]")
            
            console.input("\n[yellow]Press Enter to continue...[/yellow]")
            
        return 0
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

# Parse command line arguments
parser = argparse.ArgumentParser(description='Manage references between MongoDB collections')
parser.add_argument('--admission-to-burns', action='store_true', help='Link admission_data to burns')
parser.add_argument('--source', help='Source collection name')
parser.add_argument('--target', help='Target collection name')
parser.add_argument('--source-field', default='ID', help='Field to match in source collection')
parser.add_argument('--target-field', default='ID', help='Field to match in target collection')
parser.add_argument('--reference-field', default='reference', help='Field to store the reference in')
parser.add_argument('--dry-run', action='store_true', help='Run without making actual changes')
parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')

args = parser.parse_args()

if __name__ == "__main__":
    if args.interactive:
        sys.exit(main())
    elif args.admission_to_burns:
        sys.exit(0 if link_admissions_to_burns(dry_run=args.dry_run) else 1)
    elif args.source and args.target:
        sys.exit(0 if link_collections(
            source=args.source,
            target=args.target,
            source_field=args.source_field,
            target_field=args.target_field,
            reference_field=args.reference_field,
            dry_run=args.dry_run
        ) else 1)
    else:
        # Default to interactive mode
        sys.exit(main())