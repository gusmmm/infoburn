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

class DateComparisonQualityControl(BaseQualityControl):
    """
    Quality control module for discharge date (data_alta) in burn patient datasets.
    
    This module extends BaseQualityControl to provide specialized validation
    and analysis of patient discharge dates (data_alta), ensuring:
    - Detection of missing values in data_alta column
    - Validation of date format (dd-mm-yyyy)
    - Verification that data_alta (discharge date) is after data_ent (admission date)
    - Calculation of length of stay statistics
    """
    
    def __init__(self, 
                 filename: str,
                 discharge_column: str = "data_alta", 
                 admission_column: str = "data_ent",
                 id_column: str = "ID",
                 source_dir: Optional[Path] = None):
        """
        Initialize the discharge date quality control module.
        
        Args:
            filename: Name of the CSV file to analyze
            discharge_column: Name of the discharge date column (default: "data_alta")
            admission_column: Name of the admission date column (default: "data_ent")
            id_column: Name of the ID column in the dataset (default: "ID")
            source_dir: Directory containing the source files (optional)
        """
        super().__init__(filename, source_dir)
        self.discharge_column = discharge_column
        self.admission_column = admission_column
        self.id_column = id_column
        self.missing_dates: List[int] = []
        self.invalid_format_dates: Dict[int, str] = {}
        self.chronology_errors: Dict[int, Dict[str, str]] = {}
        self.length_of_stay: Dict[int, int] = {}  # Row index -> LOS in days
        self.stays_by_year: Dict[str, Dict] = {}
    
    def load_data(self) -> None:
        """
        Load data with proper string typing for the date columns.
        This overrides the parent method to ensure dates are read as strings.
        """
        try:
            # Specify dtype to ensure date columns are read as strings
            dtype_dict = {
                self.discharge_column: str,
                self.admission_column: str,
                self.id_column: str
            }
            self.df = pd.read_csv(self.csv_path, dtype=dtype_dict)
            
            # Read metadata
            with open(self.meta_path, 'r') as f:
                self.metadata = json.load(f)
                
            self.console.print("[green]Data loaded with date columns preserved as strings[/green]")
        except Exception as e:
            self.console.print(f"[red]Error loading data: {str(e)}[/red]")
            raise
    
    def check_missing_values(self) -> bool:
        """
        Check for missing values in the discharge date column.
        
        Returns:
            bool: True if there are no missing values, False otherwise
        """
        if self.df is None:
            self.load_data()
            
        # Find rows with missing discharge dates
        missing_mask = self.df[self.discharge_column].isna()
        self.missing_dates = self.df.index[missing_mask].tolist()
        
        return len(self.missing_dates) == 0
    
    def display_missing_values(self) -> None:
        """
        Display information about missing discharge date values if any are found.
        Creates a visually clear panel and table with the missing values.
        """
        if not self.missing_dates:
            self.console.print(Panel.fit("[green]No missing discharge date values found![/green]", 
                                        title="Discharge Date Completeness"))
            return
            
        self.console.print(Panel.fit(
            f"[yellow]Found {len(self.missing_dates)} rows with missing discharge date values[/yellow]",
            title="Missing Discharge Dates"))
        
        # Create a table of missing dates
        table = Table(title="Rows with Missing Discharge Dates")
        table.add_column("Row Number", style="cyan")
        table.add_column("ID", style="magenta")
        table.add_column("Admission Date", style="green")
        
        for row_idx in self.missing_dates:
            id_val = str(self.df.iloc[row_idx][self.id_column]) if row_idx < len(self.df) else "N/A"
            admission_val = str(self.df.iloc[row_idx][self.admission_column]) if row_idx < len(self.df) else "N/A"
            table.add_row(str(row_idx), id_val, admission_val)
            
        self.console.print(table)
        self.console.print()
    
    def validate_date_format(self) -> bool:
        """
        Validate that all discharge dates follow the dd-mm-yyyy format.
        
        Returns:
            bool: True if all dates have valid format, False otherwise
        """
        if self.df is None:
            self.load_data()
            
        # Skip missing values
        date_series = self.df[self.discharge_column].dropna()
        
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
        Display information about invalid discharge date formats if any are found.
        Creates a user-friendly table showing row numbers and invalid values.
        """
        if not self.invalid_format_dates:
            self.console.print(Panel.fit("[green]All discharge dates have valid format (dd-mm-yyyy)![/green]", 
                                        title="Discharge Date Format"))
            return
            
        self.console.print(Panel.fit(
            f"[yellow]Found {len(self.invalid_format_dates)} discharge dates with invalid format[/yellow]",
            title="Invalid Date Formats"))
        
        # Create a table of invalid dates
        table = Table(title="Invalid Discharge Date Formats")
        table.add_column("Row Number", style="cyan")
        table.add_column("Date Value", style="magenta")
        table.add_column("ID", style="yellow")
        
        for row_idx, date_val in self.invalid_format_dates.items():
            id_val = str(self.df.iloc[row_idx][self.id_column]) if row_idx < len(self.df) else "N/A"
            table.add_row(str(row_idx), str(date_val), id_val)
            
        self.console.print(table)
        self.console.print()
    
    def check_date_chronology(self) -> bool:
        """
        Check if discharge date (data_alta) is chronologically after admission date (data_ent).
        
        Returns:
            bool: True if all discharge dates are after admission dates, False otherwise
        """
        if self.df is None:
            self.load_data()
            
        # Reset chronology errors dictionary
        self.chronology_errors = {}
        
        # Work with rows that have both admission and discharge values
        valid_mask = (~self.df[self.admission_column].isna()) & (~self.df[self.discharge_column].isna())
        valid_df = self.df[valid_mask]
        
        chronology_correct = True
        
        for idx, row in valid_df.iterrows():
            admission_val = str(row[self.admission_column])
            discharge_val = str(row[self.discharge_column])
            id_val = str(row[self.id_column])
            
            # Skip invalid formats
            if not re.match(r'^(\d{2}-\d{2}-\d{4})$', admission_val) or not re.match(r'^(\d{2}-\d{2}-\d{4})$', discharge_val):
                continue
            
            try:
                # Parse dates
                admission_day, admission_month, admission_year = map(int, admission_val.split('-'))
                discharge_day, discharge_month, discharge_year = map(int, discharge_val.split('-'))
                
                admission_date = datetime(year=admission_year, month=admission_month, day=admission_day)
                discharge_date = datetime(year=discharge_year, month=discharge_month, day=discharge_day)
                
                # Check chronology
                if discharge_date < admission_date:
                    self.chronology_errors[idx] = {
                        'id': id_val,
                        'admission_date': admission_val,
                        'discharge_date': discharge_val,
                        'days_difference': (admission_date - discharge_date).days
                    }
                    chronology_correct = False
                else:
                    # Store length of stay
                    self.length_of_stay[idx] = (discharge_date - admission_date).days
                    
            except ValueError:
                # If date parsing fails, skip this row
                continue
                
        return chronology_correct
    
    def display_chronology_errors(self) -> None:
        """
        Display information about chronology errors where discharge date is before admission date.
        """
        if not self.chronology_errors:
            self.console.print(Panel.fit("[green]All discharge dates correctly occur after admission dates![/green]", 
                                        title="Date Chronology"))
            return
            
        self.console.print(Panel.fit(
            f"[yellow]Found {len(self.chronology_errors)} rows where discharge date is before admission date[/yellow]",
            title="Date Chronology Errors"))
        
        # Create a table of chronology errors
        table = Table(title="Discharge Date Before Admission Date")
        table.add_column("Row", style="cyan")
        table.add_column("ID", style="magenta")
        table.add_column("Admission Date", style="green")
        table.add_column("Discharge Date", style="red")
        table.add_column("Days Difference", style="yellow")
        
        for row_idx, data in self.chronology_errors.items():
            table.add_row(
                str(row_idx),
                data['id'],
                data['admission_date'],
                data['discharge_date'],
                str(data['days_difference'])
            )
            
        self.console.print(table)
        self.console.print()
    
    def calculate_length_of_stay_stats(self) -> Dict:
        """
        Calculate statistics for length of stay.
        
        Returns:
            Dict: Dictionary containing various length of stay statistics
        """
        if not self.length_of_stay and self.df is not None:
            # If length of stay wasn't calculated yet during chronology check
            self.check_date_chronology()
            
        if not self.length_of_stay:
            return {"error": "No valid length of stay data calculated"}
            
        los_values = list(self.length_of_stay.values())
        
        stats = {
            "count": len(los_values),
            "min_days": min(los_values),
            "max_days": max(los_values),
            "mean_days": sum(los_values) / len(los_values),
            "median_days": sorted(los_values)[len(los_values) // 2]
        }
        
        # Calculate distribution by range
        distribution = {
            "0-7 days": sum(1 for x in los_values if 0 <= x <= 7),
            "8-14 days": sum(1 for x in los_values if 8 <= x <= 14),
            "15-30 days": sum(1 for x in los_values if 15 <= x <= 30),
            "31-60 days": sum(1 for x in los_values if 31 <= x <= 60),
            "61+ days": sum(1 for x in los_values if x >= 61)
        }
        
        stats["distribution"] = distribution
        
        return stats
    
    def display_length_of_stay_stats(self) -> None:
        """
        Display statistics about length of stay calculations.
        """
        stats = self.calculate_length_of_stay_stats()
        
        if "error" in stats:
            self.console.print(f"[yellow]{stats['error']}[/yellow]")
            return
            
        self.console.print(Panel.fit(
            f"[bold]Length of Stay Statistics for {self.csv_path.name}[/bold]",
            title="Patient Stay Duration"))
            
        # Basic statistics table
        basic_table = Table(title="Basic Length of Stay Statistics")
        basic_table.add_column("Metric", style="cyan")
        basic_table.add_column("Value", style="green")
        
        basic_table.add_row("Number of valid stays", str(stats["count"]))
        basic_table.add_row("Minimum stay (days)", str(stats["min_days"]))
        basic_table.add_row("Maximum stay (days)", str(stats["max_days"]))
        basic_table.add_row("Average stay (days)", f"{stats['mean_days']:.2f}")
        basic_table.add_row("Median stay (days)", str(stats["median_days"]))
        
        self.console.print(basic_table)
        self.console.print()
        
        # Distribution table
        dist_table = Table(title="Length of Stay Distribution")
        dist_table.add_column("Stay Duration", style="cyan")
        dist_table.add_column("Count", style="green")
        dist_table.add_column("Percentage", style="yellow")
        
        for duration, count in stats["distribution"].items():
            percentage = (count / stats["count"]) * 100
            dist_table.add_row(duration, str(count), f"{percentage:.1f}%")
            
        self.console.print(dist_table)
        self.console.print()
    
    def analyze_stays_by_year(self) -> None:
        """
        Analyze length of stay statistics by year of admission.
        """
        if self.df is None:
            self.load_data()
            
        # Reset stays by year dictionary
        self.stays_by_year = {}
        
        # Work with rows that have both admission and discharge values
        valid_mask = (~self.df[self.admission_column].isna()) & (~self.df[self.discharge_column].isna())
        valid_df = self.df[valid_mask]
        
        for idx, row in valid_df.iterrows():
            admission_val = str(row[self.admission_column])
            discharge_val = str(row[self.discharge_column])
            
            # Skip invalid formats
            if not re.match(r'^(\d{2}-\d{2}-\d{4})$', admission_val) or not re.match(r'^(\d{2}-\d{2}-\d{4})$', discharge_val):
                continue
            
            try:
                # Parse dates
                admission_day, admission_month, admission_year = map(int, admission_val.split('-'))
                discharge_day, discharge_month, discharge_year = map(int, discharge_val.split('-'))
                
                admission_date = datetime(year=admission_year, month=admission_month, day=admission_day)
                discharge_date = datetime(year=discharge_year, month=discharge_month, day=discharge_day)
                
                # Skip if discharge before admission
                if discharge_date < admission_date:
                    continue
                    
                # Calculate length of stay
                los_days = (discharge_date - admission_date).days
                year_str = str(admission_year)
                
                # Initialize year entry if needed
                if year_str not in self.stays_by_year:
                    self.stays_by_year[year_str] = {
                        'count': 0,
                        'total_days': 0,
                        'min_days': float('inf'),
                        'max_days': 0,
                        'stays': []
                    }
                
                # Update statistics for this year
                self.stays_by_year[year_str]['count'] += 1
                self.stays_by_year[year_str]['total_days'] += los_days
                self.stays_by_year[year_str]['min_days'] = min(self.stays_by_year[year_str]['min_days'], los_days)
                self.stays_by_year[year_str]['max_days'] = max(self.stays_by_year[year_str]['max_days'], los_days)
                self.stays_by_year[year_str]['stays'].append(los_days)
                    
            except ValueError:
                # If date parsing fails, skip this row
                continue
    
    def display_stays_by_year(self) -> None:
        """
        Display statistics about length of stay by year of admission.
        """
        if not self.stays_by_year:
            self.analyze_stays_by_year()
            
        if not self.stays_by_year:
            self.console.print("[yellow]No valid stay data by year available[/yellow]")
            return
            
        self.console.print(Panel.fit("[bold]Length of Stay by Year of Admission[/bold]"))
        
        # Create table
        table = Table(title="Stay Duration Statistics by Year")
        table.add_column("Year", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Min Days", style="yellow")
        table.add_column("Max Days", style="yellow")
        table.add_column("Avg Days", style="yellow")
        table.add_column("Median Days", style="yellow")
        
        for year in sorted(self.stays_by_year.keys()):
            stats = self.stays_by_year[year]
            
            # If we have data for this year
            if stats['count'] > 0:
                avg_days = stats['total_days'] / stats['count']
                # Calculate median
                median_days = sorted(stats['stays'])[len(stats['stays']) // 2]
                
                table.add_row(
                    year,
                    str(stats['count']),
                    str(stats['min_days']),
                    str(stats['max_days']),
                    f"{avg_days:.1f}",
                    str(median_days)
                )
            
        self.console.print(table)
        self.console.print()
    
    def run_all_checks(self) -> None:
        """
        Run all discharge date quality control checks and display results.
        This provides a comprehensive analysis of the data_alta column in one method call.
        """
        try:
            self.console.print(Panel.fit(f"[bold blue]Running Discharge Date Quality Control on {self.csv_path.name}[/bold blue]"))
            self.console.print()
            
            # Load data if not already loaded
            if self.df is None:
                self.load_data()
                
            # Run checks
            self.check_missing_values()
            self.display_missing_values()
            
            self.validate_date_format()
            self.display_invalid_formats()
            
            self.check_date_chronology()
            self.display_chronology_errors()
            
            self.display_length_of_stay_stats()
            
            self.analyze_stays_by_year()
            self.display_stays_by_year()
            
        except Exception as e:
            self.console.print(f"[red]Error during discharge date quality control: {str(e)}[/red]")
            raise


def main():
    """
    Example usage of the DateComparisonQualityControl class with a user-friendly menu interface.
    """
    try:
        console = Console()
        
        # Create menu
        console.print(Panel.fit("[bold cyan]Discharge Date Quality Control Tool[/bold cyan]", 
                              title="Burns Critical Care Unit"))
        console.print()
        console.print("[bold]Please select an option:[/bold]")
        console.print("[1] Run discharge date quality control on default file (Doentes_typed.csv)")
        console.print("[2] Specify a different CSV file")
        console.print("[3] Calculate length of stay statistics")
        console.print("[4] Analyze stays by year")
        console.print("[5] Exit")
        console.print()
        
        choice = input("Enter choice [1-5]: ")
        
        if choice == "5":
            console.print("[yellow]Exiting program[/yellow]")
            return
        
        filename = "Doentes_typed.csv"  # Default filename
        
        if choice == "2":
            filename = input("Enter CSV filename: ")
        
        # Initialize quality control
        date_qc = DateComparisonQualityControl(filename)
        
        if choice == "1":
            date_qc.run_all_checks()
        elif choice == "3":
            date_qc.check_date_chronology()  # This also calculates length of stay
            date_qc.display_length_of_stay_stats()
        elif choice == "4":
            date_qc.analyze_stays_by_year()
            date_qc.display_stays_by_year()
        
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {str(e)}[/red]")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    main()