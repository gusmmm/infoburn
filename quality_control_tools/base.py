from pathlib import Path
import json
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import Optional, Dict, Any
from datetime import datetime

class BaseQualityControl:
    """
    Base class for quality control operations on CSV files with associated metadata.
    
    This class provides core functionality for:
    - File existence verification
    - Metadata reading and display
    - DataFrame initialization
    - Basic file information reporting
    """
    
    def __init__(self, 
                 filename: str,
                 source_dir: Optional[Path] = None):
        """
        Initialize the quality control base class.
        
        Args:
            filename: Name of the CSV file to analyze
            source_dir: Directory containing the source files (optional)
        """
        self.console = Console()
        
        # Setup paths
        if source_dir is None:
            source_dir = Path(__file__).parent.parent / 'data' / 'source' / 'gsheets'
        
        self.source_dir = source_dir
        self.csv_path = source_dir / filename
        self.meta_path = self.csv_path.with_suffix('.meta.json')
        
        # Initialize attributes
        self.df: Optional[pd.DataFrame] = None
        self.metadata: Optional[Dict[str, Any]] = None
        
        # Verify files exist
        self._verify_files()
        
    def _verify_files(self) -> None:
        """
        Verify that both CSV and metadata files exist.
        
        Raises:
            FileNotFoundError: If either file is missing
        """
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")
        
        if not self.meta_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {self.meta_path}")
            
    def load_data(self) -> None:
        """
        Load both the CSV data and metadata into memory.
        """
        try:
            self.df = pd.read_csv(self.csv_path)
            with open(self.meta_path, 'r') as f:
                self.metadata = json.load(f)
        except Exception as e:
            self.console.print(f"[red]Error loading data: {str(e)}[/red]")
            raise
            
    def display_metadata(self) -> None:
        """
        Display metadata information in a formatted table using rich.
        """
        if not self.metadata:
            self.console.print("[yellow]No metadata loaded. Call load_data() first.[/yellow]")
            return
            
        # Create metadata table
        table = Table(title="📄 File Metadata", show_header=True)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        # Add basic file information
        table.add_row("Filename", self.metadata['filename'])
        table.add_row("Worksheet", self.metadata['worksheet_name'])
        
        # Add data statistics
        table.add_row("Row Count", str(self.metadata['row_count']))
        table.add_row("Column Count", str(self.metadata['column_count']))
        
        # Add temporal information
        download_time = datetime.fromisoformat(self.metadata['download_time'])
        table.add_row("Last Downloaded", download_time.strftime("%Y-%m-%d %H:%M:%S"))
        
        # Add hash information
        table.add_row("Data Hash", self.metadata['data_hash'])
        table.add_row("Revision ID", self.metadata['revision_id'])
        
        # Display the table
        self.console.print()
        self.console.print(table)
        self.console.print()
        
    def display_dataframe_info(self) -> None:
        """
        Display basic information about the loaded DataFrame.
        """
        if self.df is None:
            self.console.print("[yellow]No data loaded. Call load_data() first.[/yellow]")
            return
            
        # Create info panel
        info_text = [
            f"Shape: {self.df.shape[0]} rows × {self.df.shape[1]} columns",
            f"Memory usage: {self.df.memory_usage().sum() / 1024:,.0f} KB",
            f"Missing values: {self.df.isna().sum().sum()} total",
            "\nColumn Types:",
            "─" * 40
        ]
        
        for col, dtype in self.df.dtypes.items():
            info_text.append(f"{col}: {dtype}")
            
        self.console.print(Panel(
            "\n".join(info_text),
            title="📊 DataFrame Information",
            border_style="cyan"
        ))

def main():
    """
    Example usage of the BaseQualityControl class.
    """
    try:
        # Initialize quality control
        qc = BaseQualityControl("Doentes.csv")
        
        # Load the data
        qc.load_data()
        
        # Display information
        qc.display_metadata()
        qc.display_dataframe_info()
        
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {str(e)}[/red]")

if __name__ == "__main__":
    main()