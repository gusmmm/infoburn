import asyncio
import json
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

from ..models.admission import AdmissionModel
from ..config.database import db_connection

console = Console()

class DataImporter:
    """Tool for importing admission data into MongoDB"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.stats = {"processed": 0, "success": 0, "failed": 0}
    
    async def connect_db(self) -> bool:
        """Establish database connection"""
        try:
            await db_connection.connect()
            return True
        except Exception as e:
            console.print(f"[red]Database connection failed: {e}[/red]")
            return False
    
    async def close_db(self):
        """Close database connection"""
        await db_connection.close()
    
    async def import_file(self, file_path: Path) -> bool:
        """Import single JSON file to database"""
        try:
            data = json.loads(file_path.read_text())
            admission = AdmissionModel(**data)
            
            collection = db_connection.db.admission_data
            await collection.insert_one(admission.model_dump(by_alias=True))
            
            self.stats["success"] += 1
            return True
            
        except Exception as e:
            console.print(f"[red]Error importing {file_path.name}: {e}[/red]")
            self.stats["failed"] += 1
            return False
    
    async def import_all(self):
        """Import all JSON files from directory"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Importing files...", total=None)
            
            for file_path in self.data_dir.glob("*.json"):
                self.stats["processed"] += 1
                progress.update(task, description=f"[cyan]Processing {file_path.name}")
                await self.import_file(file_path)
    
    def print_results(self):
        """Display import results"""
        console.print(Panel.fit(
            f"""[green]Import completed![/green]
            \nProcessed: {self.stats['processed']} files
            \nSuccessful: [green]{self.stats['success']}[/green]
            \nFailed: [red]{self.stats['failed']}[/red]""",
            title="Import Results",
            border_style="blue"
        ))

async def main():
    """Main function for the import tool"""
    console.print(Panel.fit(
        "[bold blue]InfoBurn Data Import Tool[/bold blue]",
        border_style="blue"
    ))
    
    # Get data directory
    default_dir = Path.home() / "Desktop/infoburn/data/output/json/admission_data"
    data_dir = Path(Prompt.ask(
        "[yellow]Enter data directory path[/yellow]",
        default=str(default_dir)
    ))
    
    if not data_dir.exists():
        console.print(f"[red]Directory not found: {data_dir}[/red]")
        return
    
    # Initialize importer
    importer = DataImporter(data_dir)
    
    # Connect to database
    if not await importer.connect_db():
        return
    
    try:
        # Confirm import
        if Confirm.ask("[yellow]Start import process?[/yellow]"):
            await importer.import_all()
            importer.print_results()
    finally:
        await importer.close_db()

if __name__ == "__main__":
    asyncio.run(main())