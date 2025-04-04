"""
CSV Typer Module for Doentes.csv

This module processes the Doentes.csv file from the burns unit database,
applying specific formatting rules for ID columns and date fields.

It reads the source CSV, applies type conversions and formatting, and saves
a typed version with consistent data formats to the output directory.
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
import json

# Constants - Update paths
PROJECT_ROOT = Path(__file__).parent.parent  # Goes up from google_sheet_tools to infoburn root
DATE_COLUMNS = ["data_ent", "data_alta", "data_nasc", "data_queim"]
BASE_DIR = PROJECT_ROOT / "data" / "source" / "gsheets"
INPUT_FILE = BASE_DIR / "Doentes.csv"
OUTPUT_DIR = BASE_DIR  # Same as input directory
OUTPUT_FILE = OUTPUT_DIR / "Doentes_typed.csv"

# Initialize rich console
console = Console()

def format_id(id_value) -> str:
    """
    Format ID value as string with at least 4 digits, adding leading zeros if needed.
    
    Args:
        id_value: The ID value to format, could be any type
        
    Returns:
        str: Formatted ID string with leading zeros if needed
    
    Examples:
        >>> format_id(931)
        '0931'
        >>> format_id("2501")
        '2501'
    """
    if pd.isna(id_value):
        return ""
    
    # Convert to string first
    id_str = str(id_value).strip()
    
    # If ID has only 3 digits or fewer, pad with leading zeros to make it 4 digits
    if id_str.isdigit() and len(id_str) <= 3:
        return id_str.zfill(4)
    
    return id_str

def format_date(date_str) -> str:
    """
    Convert date strings to standard format (dd-mm-yyyy).
    Handles various input formats.
    
    Args:
        date_str: The date string to format
        
    Returns:
        str: Formatted date string in dd-mm-yyyy format or empty string if invalid
    """
    if pd.isna(date_str) or not date_str:
        return ""
    
    date_str = str(date_str).strip()
    
    # Try multiple date formats
    date_formats = [
        "%d-%m-%Y", "%d/%m/%Y", 
        "%-d-%-m-%Y", "%-d/%-m/%Y",  # For dates without leading zeros
        "%Y-%m-%d"  # ISO format
    ]
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date.strftime("%d-%m-%Y")
        except ValueError:
            continue
    
    # If none of the formats work, return the original
    return date_str

def process_doentes_csv():
    """Process the Doentes.csv file"""
    console.print(Panel("[bold cyan]CSV Typer for Doentes.csv[/bold cyan]"))
    
    try:
        # Step 1: Check if input file exists
        if not INPUT_FILE.exists():
            console.print(f"[red]Error: Input file not found at {INPUT_FILE}[/red]")
            return 1
            
        # Step 2: Create output directory if it doesn't exist
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Step 3: Load data
        console.print(f"[blue]Loading data from[/blue] {INPUT_FILE}")
        df = pd.read_csv(INPUT_FILE, dtype=str)  # Read all columns as strings initially
        console.print(f"[green]✓ Successfully loaded[/green] {len(df)} records with {len(df.columns)} columns")
        
        # Step 4: Format ID column
        with Progress() as progress:
            task = progress.add_task("[cyan]Formatting ID column...", total=1)
            
            # Format ID column
            if "ID" in df.columns:
                df["ID"] = df["ID"].apply(format_id)
                console.print("[green]✓ ID column formatting complete[/green]")
            else:
                console.print("[yellow]⚠ ID column not found in data[/yellow]")
                
            progress.update(task, advance=0.5)
            
            # Format date columns
            console.print("[blue]Formatting date columns...[/blue]")
            for col in DATE_COLUMNS:
                if col in df.columns:
                    console.print(f"  - Processing {col}")
                    df[col] = df[col].apply(format_date)
                    
            progress.update(task, advance=0.5)
        
        # Step 5: Save formatted data
        console.print(f"[blue]Saving formatted data to[/blue] {OUTPUT_FILE}")
        df.to_csv(OUTPUT_FILE, index=False)
        console.print(f"[green]✓ Successfully saved[/green] {len(df)} records to {OUTPUT_FILE}")
        
        # Step 6: Copy and update metadata
        source_meta_path = INPUT_FILE.with_suffix('.meta.json')
        target_meta_path = OUTPUT_FILE.with_suffix('.meta.json')
        copy_and_update_metadata(source_meta_path, target_meta_path, OUTPUT_FILE.name)
        
        # Step 7: Show summary
        console.print(Panel(f"[bold green]Processing Complete[/bold green]\n"
                     f"Input: {INPUT_FILE}\n"
                     f"Output: {OUTPUT_FILE}\n"
                     f"Updated metadata: {target_meta_path}", 
                     expand=False))
        return 0
        
    except Exception as e:
        console.print(Panel(f"[bold red]Processing Failed[/bold red]\n{str(e)}", 
                     expand=False))
        return 1


def copy_and_update_metadata(source_meta_path: Path, target_meta_path: Path, new_filename: str) -> bool:
    """Copy and update metadata files"""
    try:
        # If source exists, copy and update it
        if source_meta_path.exists():
            with open(source_meta_path, 'r') as f:
                metadata = json.load(f)
                
            # Update filename in metadata
            metadata['filename'] = new_filename
            
            # Save updated metadata
            with open(target_meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            return True
            
        return False
        
    except Exception as e:
        console.print(f"[red]Error updating metadata: {str(e)}[/red]")
        return False

def main():
    """
    Main entry point for CSV typer tool.
    Provides a user interface for processing Doentes.csv file.
    """
    try:
        console.print(Panel.fit(
            "[bold cyan]CSV Typer Tool[/bold cyan]",
            title="Burns Critical Care Unit"))
            
        # Check if input file exists
        if not INPUT_FILE.exists():
            console.print(f"[red]Error: Input file not found at {INPUT_FILE}[/red]")
            return 1
            
        # Process the CSV file
        process_doentes_csv()
        
        return 0
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        import traceback
        console.print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    main()