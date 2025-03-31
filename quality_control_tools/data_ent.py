from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
import pandas as pd
import json
import re
from datetime import datetime
from rich.table import Table
from rich.console import Console
from rich.panel import Panel

from quality_control_tools.base import BaseQualityControl

class DateEntQualityControl(BaseQualityControl):
    """
    Quality control module for the entry date (data_ent) column in burn patient datasets.
    
    This module extends BaseQualityControl to provide specialized validation
    and analysis of patient admission dates (data_ent), ensuring:
    - Detection of missing values in data_ent column
    - Validation of date format (dd-mm-yyyy)
    - Verification that the year in data_ent matches the year in patient ID
    - Statistical summaries of patient admissions by year
    """
    
    def __init__(self, 
                 filename: str,
                 date_column: str = "data_ent", 
                 id_column: str = "ID",
                 source_dir: Optional[Path] = None):
        """
        Initialize the date entry quality control module.
        
        Args:
            filename: Name of the CSV file to analyze
            date_column: Name of the date column in the dataset (default: "data_ent")
            id_column: Name of the ID column in the dataset (default: "ID")
            source_dir: Directory containing the source files (optional)
        """
        super().__init__(filename, source_dir)
        self.date_column = date_column
        self.id_column = id_column
        self.missing_dates: List[int] = []
        self.invalid_format_dates: Dict[int, str] = {}
        self.year_mismatch: Dict[int, Dict[str, str]] = {}
        self.year_stats: Dict[str, Dict] = {}
    
    def load_data(self) -> None:
        """
        Load data with proper string typing for the date and ID columns.
        This overrides the parent method to ensure dates and IDs are read as strings.
        """
        try:
            # Specify dtype to ensure columns are read as strings
            dtype_dict = {
                self.date_column: str,
                self.id_column: str
            }
            self.df = pd.read_csv(self.csv_path, dtype=dtype_dict)
            
            # Read metadata
            with open(self.meta_path, 'r') as f:
                self.metadata = json.load(f)
                
            self.console.print("[green]Data loaded with date and ID columns preserved as strings[/green]")
        except Exception as e:
            self.console.print(f"[red]Error loading data: {str(e)}[/red]")
            raise
    
    def check_missing_values(self) -> bool:
        """
        Check for missing values in the date column.
        
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
        Display information about missing date values if any are found.
        Creates a visually clear panel and table with the missing values.
        """
        if not self.missing_dates:
            self.console.print(Panel.fit("[green]No missing admission date values found![/green]", 
                                        title="Date Entry Completeness"))
            return
            
        self.console.print(Panel.fit(
            f"[yellow]Found {len(self.missing_dates)} rows with missing admission date values[/yellow]",
            title="Missing Admission Dates"))
        
        # Create a table of missing dates
        table = Table(title="Rows with Missing Admission Dates")
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
            # Ensure it's treated as string
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
                # Invalid date (e.g. 31-02-2009)
                self.invalid_format_dates[idx] = date_str
                valid = False
                
        return valid
    
    def display_invalid_formats(self) -> None:
        """
        Display information about invalid date formats if any are found.
        Creates a user-friendly table showing row numbers and invalid values.
        """
        if not self.invalid_format_dates:
            self.console.print(Panel.fit("[green]All admission dates have valid format (dd-mm-yyyy)![/green]", 
                                        title="Admission Date Format"))
            return
            
        self.console.print(Panel.fit(
            f"[yellow]Found {len(self.invalid_format_dates)} admission dates with invalid format[/yellow]",
            title="Invalid Date Formats"))
        
        # Create a table of invalid dates
        table = Table(title="Invalid Admission Date Formats")
        table.add_column("Row Number", style="cyan")
        table.add_column("Date Value", style="magenta")
        
        for row_idx, date_val in self.invalid_format_dates.items():
            table.add_row(str(row_idx), str(date_val))
            
        self.console.print(table)
        self.console.print()
    
    def check_year_consistency(self) -> bool:
        """
        Check if the year in data_ent matches the year in the ID.
        
        The year in ID is represented by the first 2 digits (e.g., "09" = 2009).
        
        Returns:
            bool: True if all years match, False otherwise
        """
        if self.df is None:
            self.load_data()
            
        # Reset mismatch dictionary
        self.year_mismatch = {}
        
        # Work with rows that have both ID and date values
        valid_mask = (~self.df[self.id_column].isna()) & (~self.df[self.date_column].isna())
        valid_df = self.df[valid_mask]
        
        consistent = True
        for idx, row in valid_df.iterrows():
            id_val = str(row[self.id_column])
            date_val = str(row[self.date_column])
            
            # Skip invalid formats
            if not re.match(r'^\d{4,5}$', id_val) or not re.match(r'^(\d{2}-\d{2}-\d{4})$', date_val):
                continue
            
            # Extract years
            id_year_prefix = id_val[:2]
            id_year_full = f"20{id_year_prefix}"
            
            try:
                date_year = date_val.split('-')[2]  # Extract year from dd-mm-yyyy
                
                # Check if years match
                if id_year_full != date_year:
                    self.year_mismatch[idx] = {
                        'id': id_val,
                        'id_year': id_year_full,
                        'date': date_val,
                        'date_year': date_year
                    }
                    consistent = False
            except Exception:
                # If date parsing fails, skip this row
                pass
                
        return consistent
    
    def display_year_inconsistencies(self) -> None:
        """
        Display information about inconsistencies between ID year and date year.
        Creates a detailed table showing row numbers, IDs, dates, and their respective years.
        """
        if not self.year_mismatch:
            self.console.print(Panel.fit("[green]All admission years match ID year prefixes![/green]", 
                                        title="Year Consistency"))
            return
            
        self.console.print(Panel.fit(
            f"[yellow]Found {len(self.year_mismatch)} rows with inconsistent years between ID and admission date[/yellow]",
            title="Year Inconsistencies"))
        
        # Create a table of inconsistencies
        table = Table(title="Year Inconsistencies")
        table.add_column("Row", style="cyan")
        table.add_column("ID", style="magenta")
        table.add_column("ID Year", style="red")
        table.add_column("Admission Date", style="magenta")
        table.add_column("Date Year", style="green")
        
        for row_idx, data in self.year_mismatch.items():
            table.add_row(
                str(row_idx),
                data['id'],
                data['id_year'],
                data['date'],
                data['date_year']
            )
            
        self.console.print(table)
        self.console.print()
    
    def analyze_admission_by_year(self) -> None:
        """
        Analyze admission dates by year.
        Compiles statistics for each year including count, earliest and latest admission dates.
        """
        if self.df is None:
            self.load_data()
            
        # Reset year stats
        self.year_stats = {}
        
        # Skip missing values and invalid formats
        valid_dates = []
        for idx, date_val in zip(self.df.index, self.df[self.date_column]):
            if pd.isna(date_val):
                continue
                
            date_str = str(date_val)
            if not re.match(r'^(\d{2}-\d{2}-\d{4})$', date_str):
                continue
                
            # Try to parse the date
            try:
                day, month, year = map(int, date_str.split('-'))
                parsed_date = datetime(year=year, month=month, day=day)
                valid_dates.append((idx, date_str, parsed_date, year))
            except ValueError:
                continue
                
        # Compile statistics by year
        for idx, date_str, parsed_date, year in valid_dates:
            year_str = str(year)
            
            if year_str not in self.year_stats:
                self.year_stats[year_str] = {
                    'count': 0,
                    'earliest_date': parsed_date,
                    'earliest_str': date_str,
                    'latest_date': parsed_date,
                    'latest_str': date_str,
                    'months': set()
                }
            
            self.year_stats[year_str]['count'] += 1
            
            # Update earliest/latest dates
            if parsed_date < self.year_stats[year_str]['earliest_date']:
                self.year_stats[year_str]['earliest_date'] = parsed_date
                self.year_stats[year_str]['earliest_str'] = date_str
                
            if parsed_date > self.year_stats[year_str]['latest_date']:
                self.year_stats[year_str]['latest_date'] = parsed_date
                self.year_stats[year_str]['latest_str'] = date_str
                
            # Track months with admissions
            self.year_stats[year_str]['months'].add(parsed_date.month)
    
    def display_year_statistics(self) -> None:
        """
        Display statistics about admission dates grouped by year.
        Shows count, earliest and latest admission dates, and number of months with admissions.
        """
        if not self.year_stats:
            self.analyze_admission_by_year()
            
        # Create a table for year statistics
        table = Table(title="Admission Date Statistics by Year")
        table.add_column("Year", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Earliest Date", style="yellow")
        table.add_column("Latest Date", style="yellow")
        table.add_column("Months With Admissions", style="magenta")
        
        # Sort by year
        for year in sorted(self.year_stats.keys()):
            stats = self.year_stats[year]
            
            table.add_row(
                year,
                str(stats['count']),
                stats['earliest_str'],
                stats['latest_str'],
                str(len(stats['months']))
            )
            
        self.console.print(table)
        self.console.print()
    
    def run_all_checks(self) -> None:
        """
        Run all admission date quality control checks and display results.
        This provides a comprehensive analysis of the data_ent column in one method call.
        """
        try:
            self.console.print(Panel.fit(f"[bold blue]Running Admission Date Quality Control on {self.csv_path.name}[/bold blue]"))
            self.console.print()
            
            # Load data if not already loaded
            if self.df is None:
                self.load_data()
                
            # Run checks
            self.check_missing_values()
            self.display_missing_values()
            
            self.validate_date_format()
            self.display_invalid_formats()
            
            self.check_year_consistency()
            self.display_year_inconsistencies()
            
            self.analyze_admission_by_year()
            self.display_year_statistics()
            
        except Exception as e:
            self.console.print(f"[red]Error during admission date quality control: {str(e)}[/red]")
            raise

    def examine_specific_year(self, year: str) -> None:
        """
        Examine admission date details for a specific year.
        
        Args:
            year: The 4-digit year to examine (e.g., "2009")
        """
        if self.df is None:
            self.load_data()
            
        # Filter dates by year
        filtered_dates = []
        for idx, date_val in zip(self.df.index, self.df[self.date_column]):
            if pd.isna(date_val):
                continue
                
            date_str = str(date_val)
            if not re.match(r'^(\d{2}-\d{2}-\d{4})$', date_str):
                continue
                
            try:
                date_year = date_str.split('-')[2]
                if date_year == year:
                    filtered_dates.append((idx, date_str))
            except Exception:
                continue
                
        # Display results
        if not filtered_dates:
            self.console.print(f"[yellow]No admission dates found for year {year}[/yellow]")
            return
            
        self.console.print(Panel.fit(
            f"[bold]Found {len(filtered_dates)} admission dates for year {year}[/bold]",
            title=f"Year {year} Admissions"))
        
        # Create a table of dates
        table = Table(title=f"Admission Dates from Year {year}")
        table.add_column("Row", style="cyan")
        table.add_column("Date", style="green")
        table.add_column("Month", style="yellow")
        
        for idx, date_val in filtered_dates:
            month = date_val.split('-')[1]
            table.add_row(str(idx), date_val, month)
            
        self.console.print(table)
        self.console.print()


def main():
    """
    Example usage of the DateEntQualityControl class with a user-friendly menu interface.
    """
    try:
        console = Console()
        
        # Create menu
        console.print(Panel.fit("[bold cyan]Admission Date Quality Control Tool[/bold cyan]", 
                               title="Burns Critical Care Unit"))
        console.print()
        console.print("[bold]Please select an option:[/bold]")
        console.print("[1] Run admission date quality control on default file (Doentes_typed.csv)")
        console.print("[2] Specify a different CSV file")
        console.print("[3] Examine admission dates for a specific year")
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
        date_qc = DateEntQualityControl(filename)
        
        if choice == "3":
            year = input("Enter 4-digit year (e.g., 2009): ")
            if re.match(r'^\d{4}$', year):
                date_qc.examine_specific_year(year)
            else:
                console.print("[red]Invalid year format. Please enter exactly 4 digits.[/red]")
        else:
            # Run all checks
            date_qc.run_all_checks()
        
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {str(e)}[/red]")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    main()