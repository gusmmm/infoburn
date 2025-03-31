from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
import json
from rich.table import Table
from rich.console import Console
from rich.panel import Panel

from quality_control_tools.base import BaseQualityControl

class OrigemDestinoQualityControl(BaseQualityControl):
    """
    Quality control module for the Origem (Origin) and Destino (Destination) columns 
    in burn patient datasets.
    
    This module extends BaseQualityControl to provide specialized validation
    and analysis of patient origin and destination data, including:
    - Detection of missing values by year and column
    - Frequency analysis of values in each column
    - Statistical summaries and patterns
    """
    
    def __init__(self, 
                 filename: str,
                 origem_column: str = "origem",
                 destino_column: str = "destino",
                 id_column: str = "ID",
                 source_dir: Optional[Path] = None):
        """
        Initialize the Origem/Destino quality control module.
        
        Args:
            filename: Name of the CSV file to analyze
            origem_column: Name of the origin column (default: "Origem")
            destino_column: Name of the destination column (default: "Destino")
            id_column: Name of the ID column for year extraction (default: "ID")
            source_dir: Directory containing the source files (optional)
        """
        super().__init__(filename, source_dir)
        self.origem_column = origem_column
        self.destino_column = destino_column
        self.id_column = id_column
        self.missing_by_year: Dict[str, Dict] = {}
        self.value_frequencies: Dict[str, pd.Series] = {}

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
        
    def extract_year_from_id(self, id_val: str) -> str:
        """
        Extract year from ID value by taking the first 2 digits.
        For example: ID "09123" -> year "2009"
        
        Args:
            id_val: Patient ID string
            
        Returns:
            str: Full year (e.g., "2009" from "09...")
        """
        if pd.isna(id_val):
            return "Unknown"
        
        # ID should already be a string due to dtype specification in load_data
        # But ensure it's treated as string just in case
        id_str = str(id_val)
        
        # Extract year prefix if ID has at least 2 digits and they're numeric
        if len(id_str) >= 2 and id_str[:2].isdigit():
            year_prefix = id_str[:2]
            return f"20{year_prefix}"
        
        return "Unknown"
        
    def check_missing_values_by_year(self) -> None:
        """
        Analyze missing values in both columns, grouped by year.
        Stores results in self.missing_by_year dictionary.
        """
        if self.df is None:
            self.load_data()
            
        # Add year column based on ID
        self.df['Year'] = self.df[self.id_column].apply(self.extract_year_from_id)
        
        # Initialize missing values dictionary
        self.missing_by_year = {}
        
        # Analyze by year
        for year in sorted(self.df['Year'].unique()):
            year_data = self.df[self.df['Year'] == year]
            
            self.missing_by_year[year] = {
                self.origem_column: {
                    'count': year_data[self.origem_column].isna().sum(),
                    'percentage': (year_data[self.origem_column].isna().mean() * 100)
                },
                self.destino_column: {
                    'count': year_data[self.destino_column].isna().sum(),
                    'percentage': (year_data[self.destino_column].isna().mean() * 100)
                },
                'total_records': len(year_data)
            }
            
    def display_missing_values(self) -> None:
        """
        Display missing values analysis in a clear tabular format.
        Shows counts and percentages by year for each column.
        """
        if not self.missing_by_year:
            self.check_missing_values_by_year()
            
        # Create table for missing values
        table = Table(title="Missing Values Analysis by Year")
        table.add_column("Year", style="cyan")
        table.add_column("Total Records", style="blue")
        table.add_column("Origem Missing", style="yellow")
        table.add_column("Origem %", style="yellow")
        table.add_column("Destino Missing", style="magenta")
        table.add_column("Destino %", style="magenta")
        
        for year, stats in self.missing_by_year.items():
            table.add_row(
                str(year),
                str(stats['total_records']),
                str(stats[self.origem_column]['count']),
                f"{stats[self.origem_column]['percentage']:.1f}%",
                str(stats[self.destino_column]['count']),
                f"{stats[self.destino_column]['percentage']:.1f}%"
            )
            
        self.console.print(table)
        self.console.print()
        
    def analyze_value_frequencies(self) -> None:
        """
        Calculate frequency distributions for both origem and destino columns.
        Stores results in self.value_frequencies dictionary.
        """
        if self.df is None:
            self.load_data()
            
        # Calculate frequencies for each column
        for column in [self.origem_column, self.destino_column]:
            freq = self.df[column].value_counts()
            pct = self.df[column].value_counts(normalize=True) * 100
            self.value_frequencies[column] = pd.concat([freq, pct], axis=1)
            self.value_frequencies[column].columns = ['Count', 'Percentage']
            
    def display_value_frequencies(self) -> None:
        """
        Display frequency analysis for both columns in readable tables.
        Shows counts and percentages for each unique value.
        """
        if not self.value_frequencies:
            self.analyze_value_frequencies()
            
        for column in [self.origem_column, self.destino_column]:
            self.console.print(Panel.fit(
                f"[bold]Value Frequencies for {column}[/bold]"))
            
            table = Table(title=f"{column} Values Distribution")
            table.add_column("Value", style="cyan")
            table.add_column("Count", style="yellow")
            table.add_column("Percentage", style="green")
            
            for value, row in self.value_frequencies[column].iterrows():
                table.add_row(
                    str(value) if pd.notna(value) else "Missing",
                    str(int(row['Count'])),
                    f"{row['Percentage']:.1f}%"
                )
                
            self.console.print(table)
            self.console.print()
            
    def run_all_checks(self) -> None:
        """
        Run all origem/destino quality control checks and display results.
        Provides a comprehensive analysis of both columns in one method call.
        """
        try:
            self.console.print(Panel.fit(
                f"[bold blue]Running Origem/Destino Quality Control on {self.csv_path.name}[/bold blue]"))
            self.console.print()
            
            # Load data if not already loaded
            if self.df is None:
                self.load_data()
                
            # Run and display all checks
            self.check_missing_values_by_year()
            self.display_missing_values()
            
            self.analyze_value_frequencies()
            self.display_value_frequencies()
            
        except Exception as e:
            self.console.print(f"[red]Error during origem/destino quality control: {str(e)}[/red]")
            raise


def main():
    """
    Example usage of the OrigemDestinoQualityControl class with a user-friendly menu interface.
    """
    try:
        console = Console()
        
        # Create menu
        console.print(Panel.fit("[bold cyan]Origem/Destino Quality Control Tool[/bold cyan]", 
                               title="Burns Critical Care Unit"))
        console.print()
        console.print("[bold]Please select an option:[/bold]")
        console.print("[1] Run quality control on default file (Doentes_typed.csv)")
        console.print("[2] Specify a different CSV file")
        console.print("[3] Exit")
        console.print()
        
        choice = input("Enter choice [1-3]: ")
        
        if choice == "3":
            console.print("[yellow]Exiting program[/yellow]")
            return
        
        filename = "Doentes_typed.csv"  # Default filename
        
        if choice == "2":
            filename = input("Enter CSV filename: ")
        
        # Initialize and run quality control
        od_qc = OrigemDestinoQualityControl(filename)
        od_qc.run_all_checks()
        
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {str(e)}[/red]")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    main()