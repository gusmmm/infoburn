from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
import json
import re
from rich.table import Table
from rich.console import Console
from rich.panel import Panel

from quality_control_tools.base import BaseQualityControl

class IDQualityControl(BaseQualityControl):
    """
    Quality control module for the ID column in burn patient datasets.
    
    This module extends BaseQualityControl to provide specialized validation
    and analysis of patient IDs, ensuring IDs are treated as strings to maintain
    leading zeros and original formatting. It includes:
    - Detection of missing values in ID column
    - Validation of ID format (4 or 5 digits)
    - Analysis of ID components (year prefix and serial number)
    - Statistical summaries of patient counts by year
    """
    
    def __init__(self, 
                 filename: str,
                 id_column: str = "ID", 
                 source_dir: Optional[Path] = None):
        """
        Initialize the ID quality control module.
        
        Args:
            filename: Name of the CSV file to analyze
            id_column: Name of the ID column in the dataset (default: "ID")
            source_dir: Directory containing the source files (optional)
        """
        super().__init__(filename, source_dir)
        self.id_column = id_column
        self.missing_ids: List[int] = []
        self.invalid_format_ids: Dict[int, str] = {}
        self.year_stats: Dict[str, Dict] = {}
    
    def load_data(self) -> None:
        """
        Load data with proper string typing for the ID column.
        This overrides the parent method to ensure IDs are read as strings.
        """
        try:
            # Specify dtype to ensure ID column is read as string
            dtype_dict = {self.id_column: str}
            self.df = pd.read_csv(self.csv_path, dtype=dtype_dict)
            
            # Read metadata
            with open(self.meta_path, 'r') as f:
                self.metadata = json.load(f)
                
            self.console.print("[green]Data loaded with ID column preserved as strings[/green]")
        except Exception as e:
            self.console.print(f"[red]Error loading data: {str(e)}[/red]")
            raise
    
    def check_missing_values(self) -> bool:
        """
        Check for missing values in the ID column.
        
        Returns:
            bool: True if there are no missing values, False otherwise
        """
        if self.df is None:
            self.load_data()
            
        # Find rows with missing IDs
        missing_mask = self.df[self.id_column].isna()
        self.missing_ids = self.df.index[missing_mask].tolist()
        
        return len(self.missing_ids) == 0
    
    def display_missing_values(self) -> None:
        """
        Display information about missing ID values if any are found.
        Creates a visually clear panel and table with the missing values.
        """
        if not self.missing_ids:
            self.console.print(Panel.fit("[green]No missing ID values found![/green]", 
                                        title="ID Completeness"))
            return
            
        self.console.print(Panel.fit(
            f"[yellow]Found {len(self.missing_ids)} rows with missing ID values[/yellow]",
            title="Missing IDs"))
        
        # Create a table of missing IDs
        table = Table(title="Rows with Missing IDs")
        table.add_column("Row Number", style="cyan")
        
        for row_idx in self.missing_ids:
            table.add_row(str(row_idx))
            
        self.console.print(table)
        self.console.print()
    
    def validate_id_format(self) -> bool:
        """
        Validate that all IDs have 4 or 5 digits.
        Since IDs are preserved as strings, this ensures proper format checking.
        
        Returns:
            bool: True if all IDs have valid formats, False otherwise
        """
        if self.df is None:
            self.load_data()
            
        # Skip missing values
        id_series = self.df[self.id_column].dropna()
        
        # Check each ID
        valid = True
        for idx, id_val in zip(id_series.index, id_series):
            # ID should already be a string due to dtype specification in load_data
            # But ensure it's treated as string just in case
            id_str = str(id_val)
            
            # Check if format is valid (4 or 5 digits)
            if not re.match(r'^\d{4,5}$', id_str):
                self.invalid_format_ids[idx] = id_str
                valid = False
                
        return valid
    
    def display_invalid_formats(self) -> None:
        """
        Display information about invalid ID formats if any are found.
        Creates a user-friendly table showing row numbers and invalid values.
        """
        if not self.invalid_format_ids:
            self.console.print(Panel.fit("[green]All IDs have valid format (4-5 digits)![/green]", 
                                        title="ID Format"))
            return
            
        self.console.print(Panel.fit(
            f"[yellow]Found {len(self.invalid_format_ids)} IDs with invalid format[/yellow]",
            title="Invalid ID Formats"))
        
        # Create a table of invalid IDs
        table = Table(title="Invalid ID Formats")
        table.add_column("Row Number", style="cyan")
        table.add_column("ID Value", style="magenta")
        
        for row_idx, id_val in self.invalid_format_ids.items():
            table.add_row(str(row_idx), str(id_val))
            
        self.console.print(table)
        self.console.print()
    
    def analyze_id_components(self) -> None:
        """
        Analyze and extract year and serial components from IDs.
        Compiles statistics by year including count, min and max serial.
        
        The year component is the first 2 digits (e.g., "09" = 2009),
        and the serial component is the remaining 2-3 digits.
        """
        if self.df is None:
            self.load_data()
            
        # Reset year stats
        self.year_stats = {}
        
        # Skip missing values
        id_series = self.df[self.id_column].dropna()
        
        for id_val in id_series:
            # ID should already be a string due to dtype specification in load_data
            id_str = str(id_val)
            
            # Skip invalid formats
            if not re.match(r'^\d{4,5}$', id_str):
                continue
                
            # Extract year (first 2 digits)
            year = id_str[:2]
            
            # Extract serial (last 2 or 3 digits)
            serial = id_str[2:]
            
            # Update year statistics
            if year not in self.year_stats:
                self.year_stats[year] = {
                    'count': 0,
                    'min_serial': serial,
                    'max_serial': serial
                }
                
            self.year_stats[year]['count'] += 1
            
            # Update min/max serials
            if serial < self.year_stats[year]['min_serial']:
                self.year_stats[year]['min_serial'] = serial
                
            if serial > self.year_stats[year]['max_serial']:
                self.year_stats[year]['max_serial'] = serial
    
    def display_year_statistics(self) -> None:
        """
        Display statistics about IDs grouped by year.
        Shows count, minimum and maximum serial numbers for each year.
        
        The table is sorted by year and includes the full year format (20XX).
        """
        if not self.year_stats:
            self.analyze_id_components()
            
        # Create a table for year statistics
        table = Table(title="ID Statistics by Year")
        table.add_column("Year", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Min Serial", style="yellow")
        table.add_column("Max Serial", style="yellow")
        
        # Sort by year
        for year in sorted(self.year_stats.keys()):
            stats = self.year_stats[year]
            year_full = f"20{year}"  # Convert to full year format
            
            table.add_row(
                year_full,
                str(stats['count']),
                stats['min_serial'],
                stats['max_serial']
            )
            
        self.console.print(table)
        self.console.print()
    
    def run_all_checks(self) -> None:
        """
        Run all ID quality control checks and display results.
        This provides a comprehensive analysis of the ID column in one method call.
        """
        try:
            self.console.print(Panel.fit(f"[bold blue]Running ID Quality Control on {self.csv_path.name}[/bold blue]"))
            self.console.print()
            
            # Load data if not already loaded
            if self.df is None:
                self.load_data()
                
            # Run checks
            self.check_missing_values()
            self.display_missing_values()
            
            self.validate_id_format()
            self.display_invalid_formats()
            
            self.analyze_id_components()
            self.display_year_statistics()
            
        except Exception as e:
            self.console.print(f"[red]Error during ID quality control: {str(e)}[/red]")
            raise

    def examine_specific_year(self, year_prefix: str) -> None:
        """
        Examine ID details for a specific year prefix.
        
        Args:
            year_prefix: The 2-digit year prefix to examine (e.g., "09" for 2009)
        """
        if self.df is None:
            self.load_data()
            
        # Filter IDs by year prefix
        filtered_ids = []
        for idx, id_val in zip(self.df.index, self.df[self.id_column]):
            if pd.notna(id_val) and str(id_val).startswith(year_prefix):
                filtered_ids.append((idx, str(id_val)))
                
        # Display results
        year_full = f"20{year_prefix}"
        if not filtered_ids:
            self.console.print(f"[yellow]No IDs found for year {year_full}[/yellow]")
            return
            
        self.console.print(Panel.fit(
            f"[bold]Found {len(filtered_ids)} IDs for year {year_full}[/bold]",
            title=f"Year {year_full} IDs"))
        
        # Create a table of IDs
        table = Table(title=f"IDs from Year {year_full}")
        table.add_column("Row", style="cyan")
        table.add_column("ID", style="green")
        table.add_column("Serial", style="yellow")
        
        for idx, id_val in filtered_ids:
            serial = id_val[2:]
            table.add_row(str(idx), id_val, serial)
            
        self.console.print(table)
        self.console.print()


def main():
    """
    Example usage of the IDQualityControl class with a user-friendly menu interface.
    """
    try:
        console = Console()
        
        # Create menu
        console.print(Panel.fit("[bold cyan]ID Quality Control Tool[/bold cyan]", 
                               title="Burns Critical Care Unit"))
        console.print()
        console.print("[bold]Please select an option:[/bold]")
        console.print("[1] Run ID quality control on default file (Doentes_typed.csv)")
        console.print("[2] Specify a different CSV file")
        console.print("[3] Examine IDs for a specific year")
        console.print("[4] Exit")
        console.print()
        
        choice = input("Enter choice [1-4]: ")
        
        if choice == "4":
            console.print("[yellow]Exiting program[/yellow]")
            return
        
        filename = "Doentes_typed.csv"  # Default filename
        
        if choice == "2":
            filename = input("Enter CSV filename: ")
        
        # Initialize quality control
        id_qc = IDQualityControl(filename)
        
        if choice == "3":
            year_prefix = input("Enter 2-digit year prefix (e.g., 09 for 2009): ")
            if re.match(r'^\d{2}$', year_prefix):
                id_qc.examine_specific_year(year_prefix)
            else:
                console.print("[red]Invalid year format. Please enter exactly 2 digits.[/red]")
        else:
            # Run all checks
            id_qc.run_all_checks()
        
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {str(e)}[/red]")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    main()