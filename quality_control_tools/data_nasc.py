from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
import json
import re
from datetime import datetime
from rich.table import Table
from rich.console import Console
from rich.panel import Panel

from quality_control_tools.base import BaseQualityControl

class BirthDateQualityControl(BaseQualityControl):
    """
    Quality control module for birth dates (data_nasc) column in burn patient datasets.
    
    This module extends BaseQualityControl to provide specialized validation
    and analysis of patient birth dates (data_nasc), ensuring:
    - Detection of missing values in data_nasc column
    - Validation of date format (dd-mm-yyyy)
    - Verification that birth years are within reasonable range (1900-2025)
    - Statistical summaries of patient birth years
    """
    
    def __init__(self, 
                 filename: str,
                 date_column: str = "data_nasc",
                 source_dir: Optional[Path] = None):
        """
        Initialize the birth date quality control module.
        
        Args:
            filename: Name of the CSV file to analyze
            date_column: Name of the birth date column (default: "data_nasc")
            source_dir: Directory containing the source files (optional)
        """
        super().__init__(filename, source_dir)
        self.date_column = date_column
        self.missing_dates: List[int] = []
        self.invalid_format_dates: Dict[int, str] = {}
        self.invalid_year_range: Dict[int, Dict[str, str]] = {}
        self.year_stats: Dict[str, Dict] = {}
        
        # Define valid year range for birth dates
        self.MIN_YEAR = 1900
        self.MAX_YEAR = 2025
    
    def load_data(self) -> None:
        """
        Load data with proper string typing for the birth date column.
        """
        try:
            # Specify dtype to ensure date column is read as string
            dtype_dict = {self.date_column: str}
            self.df = pd.read_csv(self.csv_path, dtype=dtype_dict)
            
            # Read metadata
            with open(self.meta_path, 'r') as f:
                self.metadata = json.load(f)
                
            self.console.print("[green]Data loaded with birth date column preserved as string[/green]")
        except Exception as e:
            self.console.print(f"[red]Error loading data: {str(e)}[/red]")
            raise
    
    def check_missing_values(self) -> bool:
        """
        Check for missing values in the birth date column.
        
        Returns:
            bool: True if there are no missing values, False otherwise
        """
        if self.df is None:
            self.load_data()
            
        # Find rows with missing dates
        missing_mask = self.df[self.date_column].isna()
        self.missing_dates = self.df.index[missing_mask].tolist()
        
        return len(self.missing_dates) == 0
    
    def display_missing_values(self) -> None:
        """
        Display information about missing birth date values if any are found.
        """
        if not self.missing_dates:
            self.console.print(Panel.fit("[green]No missing birth date values found![/green]", 
                                       title="Birth Date Completeness"))
            return
            
        self.console.print(Panel.fit(
            f"[yellow]Found {len(self.missing_dates)} rows with missing birth date values[/yellow]",
            title="Missing Birth Dates"))
        
        # Create a table of missing dates
        table = Table(title="Rows with Missing Birth Dates")
        table.add_column("Row Number", style="cyan")
        
        for row_idx in self.missing_dates:
            table.add_row(str(row_idx))
            
        self.console.print(table)
        self.console.print()
    
    def validate_date_format(self) -> bool:
        """
        Validate that all dates follow the dd-mm-yyyy format.
        
        Returns:
            bool: True if all dates have valid format, False otherwise
        """
        if self.df is None:
            self.load_data()
            
        # Skip missing values
        date_series = self.df[self.date_column].dropna()
        
        valid = True
        for idx, date_val in zip(date_series.index, date_series):
            date_str = str(date_val)
            
            # Check if format is valid (dd-mm-yyyy)
            if not re.match(r'^(\d{2}-\d{2}-\d{4})$', date_str):
                self.invalid_format_dates[idx] = date_str
                valid = False
                continue
                
            # Additional validation: check if it's a valid date
            try:
                day, month, year = map(int, date_str.split('-'))
                datetime(year=year, month=month, day=day)
            except ValueError:
                self.invalid_format_dates[idx] = date_str
                valid = False
                
        return valid
    
    def check_year_range(self) -> bool:
        """
        Check if birth years are within valid range (1900-2025).
        
        Returns:
            bool: True if all years are within range, False otherwise
        """
        if self.df is None:
            self.load_data()
            
        # Reset invalid year range dictionary
        self.invalid_year_range = {}
        
        valid = True
        for idx, date_val in zip(self.df.index, self.df[self.date_column]):
            if pd.isna(date_val):
                continue
                
            date_str = str(date_val)
            if not re.match(r'^(\d{2}-\d{2}-\d{4})$', date_str):
                continue
                
            try:
                year = int(date_str.split('-')[2])
                if year < self.MIN_YEAR or year > self.MAX_YEAR:
                    self.invalid_year_range[idx] = {
                        'date': date_str,
                        'year': str(year)
                    }
                    valid = False
            except Exception:
                continue
                
        return valid
    
    def display_invalid_formats(self) -> None:
        """
        Display information about invalid date formats if any are found.
        """
        if not self.invalid_format_dates:
            self.console.print(Panel.fit("[green]All birth dates have valid format (dd-mm-yyyy)![/green]", 
                                       title="Birth Date Format"))
            return
            
        self.console.print(Panel.fit(
            f"[yellow]Found {len(self.invalid_format_dates)} birth dates with invalid format[/yellow]",
            title="Invalid Date Formats"))
        
        table = Table(title="Invalid Birth Date Formats")
        table.add_column("Row Number", style="cyan")
        table.add_column("Date Value", style="magenta")
        
        for row_idx, date_val in self.invalid_format_dates.items():
            table.add_row(str(row_idx), str(date_val))
            
        self.console.print(table)
        self.console.print()
    
    def display_invalid_years(self) -> None:
        """
        Display information about birth years outside valid range.
        """
        if not self.invalid_year_range:
            self.console.print(Panel.fit(
                f"[green]All birth years are within valid range ({self.MIN_YEAR}-{self.MAX_YEAR})![/green]", 
                title="Birth Year Range"))
            return
            
        self.console.print(Panel.fit(
            f"[yellow]Found {len(self.invalid_year_range)} birth dates outside valid range[/yellow]",
            title="Invalid Birth Years"))
        
        table = Table(title="Invalid Birth Years")
        table.add_column("Row Number", style="cyan")
        table.add_column("Birth Date", style="magenta")
        table.add_column("Year", style="red")
        
        for row_idx, data in self.invalid_year_range.items():
            table.add_row(str(row_idx), data['date'], data['year'])
            
        self.console.print(table)
        self.console.print()
    
    def analyze_birth_years(self) -> None:
        """
        Analyze birth years distribution.
        """
        if self.df is None:
            self.load_data()
            
        # Reset year stats
        self.year_stats = {}
        
        # Process valid dates
        for idx, date_val in zip(self.df.index, self.df[self.date_column]):
            if pd.isna(date_val):
                continue
                
            date_str = str(date_val)
            if not re.match(r'^(\d{2}-\d{2}-\d{4})$', date_str):
                continue
                
            try:
                year = str(date_str.split('-')[2])
                if year not in self.year_stats:
                    self.year_stats[year] = {'count': 0}
                self.year_stats[year]['count'] += 1
            except Exception:
                continue
    
    def display_year_statistics(self) -> None:
        """
        Display statistics about birth years distribution.
        """
        if not self.year_stats:
            self.analyze_birth_years()
            
        if not self.year_stats:
            self.console.print("[yellow]No valid birth years to analyze[/yellow]")
            return
            
        table = Table(title="Birth Year Distribution")
        table.add_column("Year", style="cyan")
        table.add_column("Count", style="green")
        
        for year in sorted(self.year_stats.keys()):
            table.add_row(year, str(self.year_stats[year]['count']))
            
        self.console.print(table)
        self.console.print()
    
    def run_all_checks(self) -> None:
        """
        Run all birth date quality control checks and display results.
        """
        try:
            self.console.print(Panel.fit(f"[bold blue]Running Birth Date Quality Control on {self.csv_path.name}[/bold blue]"))
            self.console.print()
            
            if self.df is None:
                self.load_data()
                
            self.check_missing_values()
            self.display_missing_values()
            
            self.validate_date_format()
            self.display_invalid_formats()
            
            self.check_year_range()
            self.display_invalid_years()
            
            self.analyze_birth_years()
            self.display_year_statistics()
            
        except Exception as e:
            self.console.print(f"[red]Error during birth date quality control: {str(e)}[/red]")
            raise


def main():
    """
    Example usage of the BirthDateQualityControl class.
    """
    try:
        console = Console()
        
        console.print(Panel.fit("[bold cyan]Birth Date Quality Control Tool[/bold cyan]", 
                              title="Burns Critical Care Unit"))
        console.print()
        console.print("[bold]Please select an option:[/bold]")
        console.print("[1] Run birth date quality control on default file (Doentes_typed.csv)")
        console.print("[2] Specify a different CSV file")
        console.print("[3] Exit")
        console.print()
        
        choice = input("Enter choice [1-3]: ")
        
        if choice == "3":
            console.print("[yellow]Exiting program[/yellow]")
            return
        
        filename = "Doentes_typed.csv"
        
        if choice == "2":
            filename = input("Enter CSV filename: ")
        
        birth_qc = BirthDateQualityControl(filename)
        birth_qc.run_all_checks()
        
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {str(e)}[/red]")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    main()