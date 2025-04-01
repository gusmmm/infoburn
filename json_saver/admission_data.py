"""
JSON Saver Module for Burns Critical Care Unit

This module processes CSV data from the Burns Critical Care Unit,
validates it using a Pydantic model, and saves each patient record
as an individual JSON file for MongoDB import.

The module:
1. Reads CSV data preserving ID as string type
2. Validates each row against the AdmissionDataPatient model
3. Creates JSON objects for each patient
4. Saves individual JSON files named by patient ID
"""

import sys
import json
from pathlib import Path
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TaskID
from datetime import datetime
import traceback
from typing import Dict, List, Optional, Any, Union
from pydantic import ValidationError

# Add parent directory to path to import from other modules
sys.path.append(str(Path(__file__).parent.parent))
from pydantic_classifier.admission_data_model import AdmissionDataPatient

# Console for rich output
console = Console()

class AdmissionDataConverter:
    """
    Converts CSV data to validated JSON files using Pydantic models.
    
    This class handles the conversion process from CSV source data to
    individual JSON files, ensuring data validation through Pydantic models
    and preparing the data format suitable for MongoDB import.
    
    Attributes:
        input_csv_path: Path to the source CSV file
        output_dir_path: Directory where JSON files will be saved
        df: Pandas DataFrame containing the loaded CSV data
        errors: List of errors encountered during processing
        success_count: Count of successfully processed records
    """
    
    def __init__(self, 
                 input_csv_path: Union[str, Path], 
                 output_dir_path: Union[str, Path]):
        """
        Initialize the converter with input and output paths.
        
        Args:
            input_csv_path: Path to the source CSV file
            output_dir_path: Directory where JSON files will be saved
        """
        self.input_csv_path = Path(input_csv_path)
        self.output_dir_path = Path(output_dir_path)
        self.df = None
        self.errors = []
        self.success_count = 0
        
    def load_csv_data(self) -> bool:
        """
        Load CSV data with proper string typing for ID column.
        
        Returns:
            bool: True if data loaded successfully, False otherwise
        """
        try:
            # Ensure ID is loaded as string to preserve leading zeros
            dtype_dict = {"ID": str}
            self.df = pd.read_csv(self.input_csv_path, dtype=dtype_dict)
            
            # Handle missing values properly
            self.df = self.df.replace({pd.NA: None})
            
            console.print(f"[green]✓ Successfully loaded[/green] {len(self.df)} records from {self.input_csv_path}")
            return True
            
        except Exception as e:
            console.print(f"[red]Error loading CSV data: {str(e)}[/red]")
            console.print(traceback.format_exc())
            return False
        
    def prepare_output_directory(self) -> bool:
        """
        Create output directory if it doesn't exist.
        
        Returns:
            bool: True if directory exists or was created successfully
        """
        try:
            self.output_dir_path.mkdir(parents=True, exist_ok=True)
            console.print(f"[green]✓ Output directory ready:[/green] {self.output_dir_path}")
            return True
        except Exception as e:
            console.print(f"[red]Error creating output directory: {str(e)}[/red]")
            console.print(traceback.format_exc())
            return False
    
    def convert_row_to_model(self, row: pd.Series) -> Optional[AdmissionDataPatient]:
        """
        Convert a DataFrame row to a validated Pydantic model.
        
        Args:
            row: A pandas Series representing one row from the DataFrame
            
        Returns:
            Optional[AdmissionDataPatient]: Validated model or None if validation failed
        """
        try:
            # Convert row to dictionary
            row_dict = row.to_dict()
            
            # Format dates properly if they exist
            date_fields = ['data_ent', 'data_alta', 'data_nasc']
            for field in date_fields:
                if field in row_dict and row_dict[field] is not None and pd.notna(row_dict[field]):
                    # Parse date in format dd-mm-yyyy
                    try:
                        date_str = str(row_dict[field])
                        if date_str and '-' in date_str:
                            date_obj = datetime.strptime(date_str, "%d-%m-%Y")
                            row_dict[field] = date_obj.date()
                    except ValueError:
                        # If we can't parse the date, set to None
                        row_dict[field] = None
                else:
                    row_dict[field] = None
            
            # Create and validate model
            model = AdmissionDataPatient(**row_dict)
            return model
            
        except ValidationError as e:
            self.errors.append({
                "id": row.get("ID", "Unknown"),
                "error": str(e),
                "row": row.to_dict()
            })
            return None
        except Exception as e:
            self.errors.append({
                "id": row.get("ID", "Unknown"),
                "error": f"Unexpected error: {str(e)}",
                "row": row.to_dict()
            })
            console.print(traceback.format_exc())
            return None
    
    def model_to_json_dict(self, model: AdmissionDataPatient) -> Dict:
        """
        Convert Pydantic model to a dictionary ready for JSON serialization.
        
        ID is the unique ID field.
        
        Args:
            model: Validated AdmissionDataPatient model
            
        Returns:
            Dict: Dictionary ready for JSON serialization
        """
        # Convert model to dictionary
        data_dict = model.model_dump()
        
        # Set _id field for MongoDB and remove original ID
        data_dict["ID"] = data_dict.pop("ID")
        
        return data_dict
    
    def save_json_file(self, data: Dict, filename: str) -> bool:
        """
        Save data as JSON to the specified filename.
        
        Args:
            data: Dictionary data to save
            filename: Name of the output file
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            output_path = self.output_dir_path / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, default=str, indent=2)
            return True
        except Exception as e:
            self.errors.append({
                "id": data.get("ID", "Unknown"),
                "error": f"Error saving file {filename}: {str(e)}",
                "data": data
            })
            return False
    
    def process_data(self) -> bool:
        """
        Process all data rows, validate and save as JSON files.
        
        Returns:
            bool: True if processing completed (even with some errors),
                 False if critical failure occurred
        """
        if self.df is None:
            if not self.load_csv_data():
                return False
                
        if not self.prepare_output_directory():
            return False
            
        total_rows = len(self.df)
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Processing records...", total=total_rows)
            
            for index, row in self.df.iterrows():
                try:
                    # Skip rows without ID
                    if pd.isna(row.get('ID')) or not row.get('ID'):
                        progress.update(task, advance=1)
                        self.errors.append({
                            "row_index": index,
                            "error": "Missing ID field",
                            "row": row.to_dict()
                        })
                        continue
                    
                    # Convert row to model
                    model = self.convert_row_to_model(row)
                    if model is None:
                        progress.update(task, advance=1)
                        continue
                    
                    # Convert model to JSON dict
                    json_dict = self.model_to_json_dict(model)
                    
                    # Create filename based on ID
                    filename = f"{json_dict['ID']}.json"
                    
                    # Save JSON file
                    if self.save_json_file(json_dict, filename):
                        self.success_count += 1
                    
                    progress.update(task, advance=1)
                    
                except Exception as e:
                    self.errors.append({
                        "row_index": index,
                        "error": f"Unexpected error: {str(e)}",
                        "row": row.to_dict() if row is not None else "Unknown"
                    })
                    progress.update(task, advance=1)
                    console.print(traceback.format_exc())
        
        return True
    
    def display_summary(self) -> None:
        """
        Display processing summary, including success and error counts.
        """
        console.print(Panel.fit(
            f"[bold green]Processing Summary[/bold green]\n\n"
            f"Total records: {len(self.df) if self.df is not None else 0}\n"
            f"Successfully processed: [green]{self.success_count}[/green]\n"
            f"Errors: [yellow]{len(self.errors)}[/yellow]\n\n"
            f"JSON files saved to: {self.output_dir_path}",
            title="Burns Critical Care Unit Data Conversion"
        ))
        
        if self.errors:
            console.print(f"[yellow]Warning: {len(self.errors)} records had errors during processing.[/yellow]")
            console.print("First 5 errors:")
            for i, error in enumerate(self.errors[:5]):
                console.print(f"  [yellow]{i+1}. ID: {error.get('id', error.get('row_index', 'Unknown'))}, Error: {error['error']}[/yellow]")
            
            # Save error log
            error_log_path = self.output_dir_path / "error_log.json"
            try:
                with open(error_log_path, 'w', encoding='utf-8') as f:
                    json.dump(self.errors, f, ensure_ascii=False, default=str, indent=2)
                console.print(f"[yellow]Complete error log saved to: {error_log_path}[/yellow]")
            except Exception as e:
                console.print(f"[red]Failed to save error log: {str(e)}[/red]")


def main() -> int:
    """
    Main entry point for the CSV to JSON converter.
    
    Process csv data from the Burns Critical Care Unit,
    validate it with Pydantic models, and save as JSON files.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        # Display welcome header
        console.print(Panel.fit("[bold cyan]CSV to JSON Converter[/bold cyan]", 
                               title="Burns Critical Care Unit"))
        
        # Set up paths
        project_root = Path(__file__).parent.parent
        input_csv_path = project_root / "data" / "source" / "gsheets" / "Doentes_typed.csv"
        output_dir_path = project_root / "data" / "output" / "json" / "admission_data"
        
        # Initialize converter
        converter = AdmissionDataConverter(input_csv_path, output_dir_path)
        
        # Show configuration info
        console.print("[blue]Configuration:[/blue]")
        console.print(f"- Input CSV: {input_csv_path}")
        console.print(f"- Output directory: {output_dir_path}")
        console.print()
        
        # Process data
        if converter.process_data():
            converter.display_summary()
            return 0
        else:
            console.print("[red]Processing failed due to critical errors[/red]")
            return 1
            
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        console.print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())