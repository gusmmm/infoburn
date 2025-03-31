from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
import json
import re
from rich.table import Table
from rich.console import Console
from rich.panel import Panel

from quality_control_tools.base import BaseQualityControl

class ProcessoQualityControl(BaseQualityControl):
    """
    Quality control module for the Processo column in burn patient datasets.
    
    This module extends BaseQualityControl to provide specialized validation
    and analysis of patient process numbers, ensuring they are treated as strings
    to maintain original formatting. It includes:
    - Detection of missing values in Processo column
    - Validation of Processo format (digits only)
    - Statistical summaries of validation results
    """
    
    def __init__(self, 
                 filename: str,
                 processo_column: str = "processo", 
                 source_dir: Optional[Path] = None):
        """
        Initialize the Processo quality control module.
        
        Args:
            filename: Name of the CSV file to analyze
            processo_column: Name of the processo column in the dataset (default: "Processo")
            source_dir: Directory containing the source files (optional)
        """
        super().__init__(filename, source_dir)
        self.processo_column = processo_column
        self.missing_processos: List[int] = []
        self.invalid_format_processos: Dict[int, str] = {}
    
    def load_data(self) -> None:
        """
        Load data with proper string typing for the Processo column.
        This overrides the parent method to ensure processo values are read as strings.
        
        The method reads the CSV file and specifies the Processo column to be treated
        as a string data type, preventing any automatic type conversion by pandas.
        It also loads the associated metadata file.
        """
        try:
            # Specify dtype to ensure Processo column is read as string
            dtype_dict = {self.processo_column: str}
            self.df = pd.read_csv(self.csv_path, dtype=dtype_dict)
            
            # Read metadata
            with open(self.meta_path, 'r') as f:
                self.metadata = json.load(f)
                
            self.console.print("[green]Data loaded with Processo column preserved as strings[/green]")
        except Exception as e:
            self.console.print(f"[red]Error loading data: {str(e)}[/red]")
            raise
    
    def check_missing_values(self) -> bool:
        """
        Check for missing values in the Processo column.
        
        This method identifies and records the row indices where the Processo
        values are missing. It populates the missing_processos list with these indices.
        
        Returns:
            bool: True if there are no missing values, False otherwise
        """
        if self.df is None:
            self.load_data()
            
        # Find rows with missing processo values
        missing_mask = self.df[self.processo_column].isna()
        self.missing_processos = self.df.index[missing_mask].tolist()
        
        return len(self.missing_processos) == 0
    
    def display_missing_values(self) -> None:
        """
        Display information about missing Processo values if any are found.
        Creates a visually clear panel and table with the missing values.
        
        The method generates a user-friendly output showing which rows have
        missing Processo values, making it easy to identify problematic entries.
        """
        if not self.missing_processos:
            self.console.print(Panel.fit("[green]No missing Processo values found![/green]", 
                                        title="Processo Completeness"))
            return
            
        self.console.print(Panel.fit(
            f"[yellow]Found {len(self.missing_processos)} rows with missing Processo values[/yellow]",
            title="Missing Processos"))
        
        # Create a table of missing processos
        table = Table(title="Rows with Missing Processo Values")
        table.add_column("Row Number", style="cyan")
        
        for row_idx in self.missing_processos:
            table.add_row(str(row_idx))
            
        self.console.print(table)
        self.console.print()
    
    def validate_processo_format(self) -> bool:
        """
        Validate that all Processo values consist of digits only.
        
        This method checks each Processo value to ensure it contains only
        numeric characters. It records any values that contain non-digit
        characters along with their row indices.
        
        Returns:
            bool: True if all Processo values consist of digits only, False otherwise
        """
        if self.df is None:
            self.load_data()
            
        # Skip missing values
        processo_series = self.df[self.processo_column].dropna()
        
        # Check each processo value
        valid = True
        for idx, processo_val in zip(processo_series.index, processo_series):
            # Processo should already be a string due to dtype specification in load_data
            processo_str = str(processo_val)
            
            # Check if format is valid (digits only)
            if not processo_str.isdigit():
                self.invalid_format_processos[idx] = processo_str
                valid = False
                
        return valid
    
    def display_invalid_formats(self) -> None:
        """
        Display information about invalid Processo formats if any are found.
        Creates a user-friendly table showing row numbers and invalid values.
        
        This method provides a clear visualization of which Processo values
        contain non-digit characters, helping to quickly identify entries
        that need correction.
        """
        if not self.invalid_format_processos:
            self.console.print(Panel.fit("[green]All Processo values consist of digits only![/green]", 
                                        title="Processo Format"))
            return
            
        self.console.print(Panel.fit(
            f"[yellow]Found {len(self.invalid_format_processos)} Processo values with invalid format[/yellow]",
            title="Invalid Processo Formats"))
        
        # Create a table of invalid processos
        table = Table(title="Invalid Processo Formats")
        table.add_column("Row Number", style="cyan")
        table.add_column("Processo Value", style="magenta")
        
        for row_idx, processo_val in self.invalid_format_processos.items():
            table.add_row(str(row_idx), str(processo_val))
            
        self.console.print(table)
        self.console.print()
    
    def run_all_checks(self) -> None:
        """
        Run all Processo quality control checks and display results.
        This provides a comprehensive analysis of the Processo column in one method call.
        
        The method executes all validation checks sequentially and displays
        the results in a structured, easy-to-understand format. It handles any
        exceptions that might occur during the process.
        """
        try:
            self.console.print(Panel.fit(f"[bold blue]Running Processo Quality Control on {self.csv_path.name}[/bold blue]"))
            self.console.print()
            
            # Load data if not already loaded
            if self.df is None:
                self.load_data()
                
            # Run checks
            self.check_missing_values()
            self.display_missing_values()
            
            self.validate_processo_format()
            self.display_invalid_formats()
            
        except Exception as e:
            self.console.print(f"[red]Error during Processo quality control: {str(e)}[/red]")
            raise
    
    def display_statistics(self) -> None:
        """
        Display overall statistics about the Processo column.
        
        This method presents a summary of the validation results, including:
        - Total number of records
        - Number of missing values
        - Number of invalid format values
        - Percentage of valid values
        
        The statistics provide a quick overview of the data quality.
        """
        if self.df is None:
            self.load_data()
        
        total_records = len(self.df)
        missing_count = len(self.missing_processos)
        invalid_format_count = len(self.invalid_format_processos)
        valid_count = total_records - missing_count - invalid_format_count
        valid_percentage = (valid_count / total_records) * 100 if total_records > 0 else 0
        
        # Create a table for statistics
        table = Table(title="Processo Quality Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Records", str(total_records))
        table.add_row("Missing Values", str(missing_count))
        table.add_row("Invalid Format Values", str(invalid_format_count))
        table.add_row("Valid Values", str(valid_count))
        table.add_row("Valid Percentage", f"{valid_percentage:.2f}%")
        
        self.console.print(table)
        self.console.print()


def main():
    """
    Example usage of the ProcessoQualityControl class with a user-friendly menu interface.
    """
    try:
        console = Console()
        
        # Create menu
        console.print(Panel.fit("[bold cyan]Processo Quality Control Tool[/bold cyan]", 
                               title="Burns Critical Care Unit"))
        console.print()
        console.print("[bold]Please select an option:[/bold]")
        console.print("[1] Run Processo quality control on default file (Doentes_typed.csv)")
        console.print("[2] Specify a different CSV file")
        console.print("[3] View Processo statistics only")
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
        processo_qc = ProcessoQualityControl(filename)
        
        if choice == "3":
            # Check for missing and invalid first to populate the lists
            processo_qc.check_missing_values()
            processo_qc.validate_processo_format()
            processo_qc.display_statistics()
        else:
            # Run all checks
            processo_qc.run_all_checks()
            # Show statistics at the end
            processo_qc.display_statistics()
        
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {str(e)}[/red]")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    main()