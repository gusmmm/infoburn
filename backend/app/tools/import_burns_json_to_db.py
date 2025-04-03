"""
Import Tool for Burns JSON Data

This module imports burns data from JSON files to MongoDB.
Processes files from the burns data directory, validates them,
and inserts them into the burns collection.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.prompt import Prompt

from pydantic import BaseModel

# Initialize console for rich output
console = Console()


class ImportRecord(BaseModel):
    """Model for tracking import records"""
    file_id: str
    file_name: str
    status: str
    error_message: Optional[str] = None
    import_date: datetime = datetime.now()


class BurnsDataImporter:
    """Service for importing burns data from JSON files to MongoDB"""
    
    def __init__(self, data_path: Path, reports_path: Path):
        """
        Initialize the burns data importer.
        
        Args:
            data_path (Path): Directory containing JSON files to import
            reports_path (Path): Directory to save reports
        """
        self.data_path = data_path
        self.reports_path = reports_path
        self.tracking_file = reports_path / "burns_import_tracking.csv"
        self.success_count = 0
        self.error_count = 0
        self.errors: List[Dict[str, Any]] = []
        self.records: List[ImportRecord] = []
        self._ensure_reports_dir()
    
    def _ensure_reports_dir(self):
        """Ensure reports directory exists and create tracking file if needed"""
        self.reports_path.mkdir(parents=True, exist_ok=True)
        if not self.tracking_file.exists():
            pd.DataFrame(columns=[
                'file_id', 'file_name', 'status', 
                'error_message', 'import_date'
            ]).to_csv(self.tracking_file, index=False)
    
    def _add_tracking_record(self, record: ImportRecord):
        """Add a new import tracking record"""
        self.records.append(record)
    
    def _save_tracking_report(self):
        """Save tracking data and generate HTML report"""
        # Convert records to DataFrame
        df = pd.DataFrame([r.model_dump() for r in self.records])
        
        if not df.empty:
            df.to_csv(self.tracking_file, mode='a', header=False, index=False)
        
        # Generate HTML report
        summary_file = self.reports_path / f"burns_import_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        all_records = pd.read_csv(self.tracking_file)
        
        summary_html = f"""
        <html>
        <head>
            <title>Burns Import Summary Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; }}
                .summary {{ margin: 20px 0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f5f5f5; }}
                .error {{ color: #e74c3c; }}
                .success {{ color: #27ae60; }}
            </style>
        </head>
        <body>
            <h1>Burns Import Summary Report</h1>
            <div class="summary">
                <h2>Status Summary</h2>
                {all_records['status'].value_counts().to_frame().to_html()}
            </div>
            <div class="details">
                <h2>Import Details</h2>
                {all_records.to_html(classes='table', index=False)}
            </div>
        </body>
        </html>
        """
        
        summary_file.write_text(summary_html)
        console.print(f"[green]Summary report saved to {summary_file}[/green]")
    
    async def process_json_file(self, file_path: Path) -> bool:
        """
        Process a single JSON file and import to MongoDB.
        
        Args:
            file_path (Path): Path to the JSON file
        
        Returns:
            bool: True if successful, False otherwise
        """
        file_id = file_path.stem
        file_name = file_path.name
        
        try:
            # Read the JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Import to MongoDB
            from backend.app.config.database import db_connection
            burns_collection = db_connection.db.burns
            
            # Check if document already exists
            existing_doc = await burns_collection.find_one({"ID": file_id})
            
            if existing_doc:
                # Update the existing document
                result = await burns_collection.update_one(
                    {"ID": file_id},
                    {"$set": data}
                )
                status = "updated"
            else:
                # Insert a new document
                result = await burns_collection.insert_one(data)
                status = "inserted"
            
            # Add success tracking record
            self._add_tracking_record(ImportRecord(
                file_id=file_id,
                file_name=file_name,
                status=status
            ))
            
            return True
            
        except Exception as e:
            # Log the error
            error_message = str(e)
            self.errors.append({
                "file": file_name,
                "error": error_message
            })
            
            # Add error tracking record
            self._add_tracking_record(ImportRecord(
                file_id=file_id,
                file_name=file_name,
                status="error",
                error_message=error_message
            ))
            
            return False
    
    def create_results_table(self) -> Table:
        """Create a rich table with import results"""
        table = Table(
            "Metric", "Value",
            title="Import Results",
            show_lines=True,
            title_style="bold magenta",
            header_style="bold cyan"
        )
        
        table.add_row("Total Files Processed", str(self.success_count + self.error_count))
        table.add_row("Successfully Imported", f"[green]{self.success_count}[/green]")
        table.add_row("Failed", f"[red]{self.error_count}[/red]")
        
        return table
    
    def create_errors_table(self) -> Table:
        """Create a rich table with error details"""
        if not self.errors:
            return None
            
        table = Table(
            "File", "Error",
            title="Import Errors",
            show_lines=True,
            title_style="bold red",
            header_style="bold cyan"
        )
        
        for error in self.errors:
            table.add_row(error["file"], error["error"])
            
        return table
    
    async def import_all(self):
        """Import all JSON files from the data directory"""
        try:
            from backend.app.config.database import db_connection
            await db_connection.connect()
            
            json_files = list(self.data_path.glob("*.json"))
            if not json_files:
                console.print(Panel(
                    "[yellow]No JSON files found in directory[/yellow]",
                    title="Warning"
                ))
                return
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True
            ) as progress:
                task = progress.add_task(
                    "[cyan]Importing burns data...", 
                    total=len(json_files)
                )
                
                for file_path in json_files:
                    success = await self.process_json_file(file_path)
                    if success:
                        self.success_count += 1
                    else:
                        self.error_count += 1
                    progress.advance(task)
            
            console.print("\n")
            console.print(self.create_results_table())
            
            if errors_table := self.create_errors_table():
                console.print("\n")
                console.print(errors_table)
            
            # Save tracking report
            self._save_tracking_report()
                
        except Exception as e:
            console.print(f"[red]Error during import: {str(e)}[/red]")
        finally:
            await db_connection.close()


async def main():
    """Main entry point"""
    # Configure paths
    data_path = Path("/home/gusmmm/Desktop/infoburn/data/output/json/burns")
    reports_path = Path("/home/gusmmm/Desktop/infoburn/reports")
    
    # Show welcome message
    console.print(Panel(
        "[bold blue]Burns Data Importer[/bold blue]",
        subtitle="Import burns data from JSON files to MongoDB",
        border_style="blue"
    ))
    
    # Display configured paths
    console.print(f"[blue]Data directory:[/blue] {data_path}")
    console.print(f"[blue]Reports directory:[/blue] {reports_path}")
    
    # Create importer and run import
    importer = BurnsDataImporter(data_path, reports_path)
    
    # Ask user if they want to proceed
    proceed = Prompt.ask(
        "Proceed with import?", 
        choices=["y", "n"], 
        default="y"
    )
    
    if proceed.lower() == "y":
        await importer.import_all()
    else:
        console.print("[yellow]Import cancelled by user[/yellow]")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())