import asyncio
import json
import pandas as pd
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any, Optional
from enum import Enum
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

from ..config.database import db_connection
from ..models.admission import AdmissionCreate
from pydantic import BaseModel, Field, ValidationError

console = Console()

class ImportStatus(str, Enum):
    """Status of JSON file import"""
    IMPORTED = "imported"
    REJECTED = "rejected"
    MISSING = "missing"
    DUPLICATE = "duplicate"

class ImportRecord(BaseModel):
    """Record of a JSON file import attempt"""
    file_id: str = Field(..., description="ID from the admission record")
    file_name: str = Field(..., description="Name of the JSON file")
    status: ImportStatus = Field(..., description="Import status")
    error_message: Optional[str] = Field(None, description="Error message if rejected")
    import_date: datetime = Field(default_factory=datetime.now, description="Date of import attempt")

class AdmissionDataImporter:
    """Service for importing admission data from JSON files to MongoDB"""
    
    def __init__(self, data_path: Path, reports_path: Path):
        self.data_path = data_path
        self.reports_path = reports_path
        self.tracking_file = reports_path / "import_tracking.csv"
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
        summary_file = self.reports_path / f"import_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        all_records = pd.read_csv(self.tracking_file)
        
        summary_html = f"""
        <html>
        <head>
            <title>Import Summary Report</title>
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
            <h1>Import Summary Report</h1>
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
        """Process a single JSON file and import to MongoDB"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            admission = AdmissionCreate(**data)
            
            # Check for existing record
            existing = await db_connection.db.admission_data.find_one({"ID": admission.ID})
            if existing:
                self._add_tracking_record(
                    ImportRecord(
                        file_id=admission.ID,
                        file_name=file_path.name,
                        status=ImportStatus.DUPLICATE,
                        error_message="Record already exists"
                    )
                )
                self.errors.append({
                    "file": file_path.name,
                    "error": f"Admission with ID {admission.ID} already exists"
                })
                return False
            
            # Convert model to dict and handle date serialization
            admission_dict = admission.model_dump(exclude_none=True)
            
            # Convert dates to ISO format strings
            date_fields = ['data_ent', 'data_alta', 'data_nasc']
            for field in date_fields:
                if field in admission_dict and admission_dict[field]:
                    admission_dict[field] = admission_dict[field].isoformat()
        
            # Insert into MongoDB
            result = await db_connection.db.admission_data.insert_one(admission_dict)
            
            if not result.inserted_id:
                raise Exception("Failed to insert document")
            
            self._add_tracking_record(
                ImportRecord(
                    file_id=admission.ID,
                    file_name=file_path.name,
                    status=ImportStatus.IMPORTED
                )
            )
            return True
            
        except ValidationError as e:
            self._add_tracking_record(
                ImportRecord(
                    file_id=data.get('ID', 'unknown'),
                    file_name=file_path.name,
                    status=ImportStatus.REJECTED,
                    error_message=str(e)
                )
            )
            self.errors.append({
                "file": file_path.name,
                "error": f"Validation error: {str(e)}"
            })
            return False
        except json.JSONDecodeError as e:
            self._add_tracking_record(
                ImportRecord(
                    file_id='unknown',
                    file_name=file_path.name,
                    status=ImportStatus.REJECTED,
                    error_message=f"Invalid JSON: {str(e)}"
                )
            )
            self.errors.append({
                "file": file_path.name,
                "error": f"Invalid JSON: {str(e)}"
            })
            return False
        except Exception as e:
            self._add_tracking_record(
                ImportRecord(
                    file_id=data.get('ID', 'unknown'),
                    file_name=file_path.name,
                    status=ImportStatus.REJECTED,
                    error_message=str(e)
                )
            )
            self.errors.append({
                "file": file_path.name,
                "error": f"Unexpected error: {str(e)}"
            })
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
                    "[cyan]Importing admission data...", 
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
    data_path = Path("/home/gusmmm/Desktop/infoburn/data/output/json/admission_data")
    reports_path = Path("/home/gusmmm/Desktop/infoburn/reports")
    importer = AdmissionDataImporter(data_path, reports_path)
    await importer.import_all()

if __name__ == "__main__":
    asyncio.run(main())