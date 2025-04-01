"""
This module handles anonymization of sensitive patient data in markdown files.
It uses Google's Gemini AI to identify and replace private information with anonymous identifiers.
"""

import os
import re
import json
from datetime import datetime
from typing import Dict, List, Tuple, Set, Optional, Any
from pathlib import Path
import logging
from core_tools.key_manager import KeyManager

from google import genai
from google.genai import types
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.prompt import Prompt
from rich import print as rprint

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_INPUT_DIR = PROJECT_ROOT / "data" / "output" / "markdown" / "clean"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "output" / "markdown" / "anonymized"

# Get Gemini API key from environment variable
key_manager = KeyManager()
GEMINI_API_KEY = key_manager.get_key('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it before running the script.")

class MarkdownAnonymizer:
    """
    Handles the anonymization of sensitive information in markdown files,
    particularly focusing on patient data in European Portuguese.
    
    This class uses Google's Gemini AI to identify and replace private information
    with consistent anonymous identifiers and converts dates to a relative format.
    """
    
    def __init__(self, api_key: str, input_dir: str, output_dir: str, recursive_search: bool = True):
        """
        Initialize the MarkdownAnonymizer with necessary parameters.
        
        Args:
            api_key: Google API key for Gemini AI
            input_dir: Directory containing markdown files to anonymize
            output_dir: Directory where anonymized files will be saved
            recursive_search: Whether to search for files in subdirectories
        """
        self.api_key = api_key or GEMINI_API_KEY
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.recursive_search = recursive_search
        self.console = Console()
        self.entity_map = {}  # Maps original values to anonymized identifiers
        self.reference_date = None  # Will store the day_0 reference date
        
        # Configure Google Gemini AI with the latest SDK
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.0-flash"
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename='anonymizer.log'
        )
        self.logger = logging.getLogger('MarkdownAnonymizer')
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Validate input directory
        if not self.input_dir.exists():
            raise ValueError(f"Input directory does not exist: {input_dir}")

    def find_all_markdown_files(self) -> List[Path]:
        """
        Find all markdown files in the input directory, including subdirectories.
        
        Returns:
            A list of Path objects for all markdown files
        """
        try:
            # Look in the main directory
            files = list(self.input_dir.glob('*.md'))
            
            # Also search in subdirectories if recursive option is enabled
            if hasattr(self, 'recursive_search') and self.recursive_search:
                files.extend(list(self.input_dir.glob('**/*.md')))
                
            return files
        except Exception as e:
            self.logger.error(f"Error finding markdown files: {e}")
            raise

    def list_available_files(self) -> List[str]:
        """
        List all available markdown files in the input directory.
        
        Returns:
            A list of filenames (without path)
        """
        files = self.find_all_markdown_files()
        return [f.name for f in files]

    def find_file_by_name(self, filename: str) -> Optional[Path]:
        """
        Find a file by name, with flexible matching.
        
        Args:
            filename: Name of the file to find
            
        Returns:
            Path object for the file if found, None otherwise
        """
        # Add .md extension if not provided
        if not filename.lower().endswith('.md'):
            filename = f"{filename}.md"
            
        # Try direct match
        file_path = self.input_dir / filename
        if file_path.exists():
            return file_path
            
        # Try case-insensitive match
        try:
            for f in self.input_dir.iterdir():
                if f.is_file() and f.name.lower() == filename.lower():
                    return f
        except Exception:
            pass
            
        # Try searching in subdirectories
        try:
            matches = list(self.input_dir.glob(f"**/{filename}"))
            if matches:
                return matches[0]
                
            # Try case-insensitive search in subdirectories
            for f in self.input_dir.glob("**/*.md"):
                if f.name.lower() == filename.lower():
                    return f
        except Exception:
            pass
            
        return None

    def process_files(self, single_file: str = None):
        """
        Process markdown files to anonymize sensitive information.
        
        Args:
            single_file: Optional filename to process only one specific file
        """
        file_path = None  # Initialize file_path
        if single_file:
            file_path = self.find_file_by_name(single_file)
            
            if not file_path:
                # File not found, show available files
                available_files = self.list_available_files()
                
                if not available_files:
                    self.console.print(Panel("[bold red]No markdown files found in the input directory"))
                    return
                    
                self.console.print(Panel(f"[bold red]File not found: {single_file}"))
                self.console.print("\n[bold]Available files:[/bold]")
                
                for i, f in enumerate(available_files):
                    self.console.print(f"{i+1}. {f}")
                    
                # Allow the user to select a file
                choice = Prompt.ask(
                    "\n[bold]Select a file by number or press Enter to cancel[/bold]",
                    default=""
                )
                
                if not choice:
                    return
                    
                try:
                    file_index = int(choice) - 1
                    if 0 <= file_index < len(available_files):
                        file_path = self.input_dir / available_files[file_index]
                    else:
                        self.console.print("[bold red]Invalid selection[/bold]")
                        return
                except ValueError:
                    self.console.print("[bold red]Invalid input[/bold]")
                    return

        if file_path:
            markdown_files = [file_path]
        else:
            markdown_files = self.find_all_markdown_files()
        
        if not markdown_files:
            self.console.print(Panel("[bold red]No markdown files found in the input directory"))
            return
            
        self.console.print(Panel(f"[bold green]Found {len(markdown_files)} markdown files to process"))
        
        # Find reference date
        self.reference_date = self.find_reference_date(markdown_files)
        if not self.reference_date:
            self.console.print(Panel("[bold yellow]Warning: No valid dates found. Date anonymization will be skipped."))
        else:
            self.console.print(Panel(f"[bold green]Reference date (day_0): {self.reference_date.strftime('%Y-%m-%d')}"))
        
        # Process each file
        with Progress() as progress:
            task = progress.add_task("[cyan]Anonymizing files...", total=len(markdown_files))
            
            for file_path in markdown_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    anonymized_content = self.anonymize_content(content)
                    
                    output_file = self.output_dir / file_path.name
                    with open(output_file, 'w', encoding='utf-8') as file:
                        file.write(anonymized_content)
                        
                except Exception as e:
                    self.logger.error(f"Error processing {file_path}: {e}")
                
                progress.update(task, advance=1)
        
        # Save entity mapping for reference
        try:
            with open(self.output_dir / 'entity_mapping.json', 'w', encoding='utf-8') as f:
                json.dump(self.entity_map, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving entity mapping: {e}")
            
        self.console.print(Panel("[bold green]Anonymization complete!"))
        self.console.print(f"Anonymized files are saved in: {self.output_dir}")
        self.console.print(f"Entity mapping saved to: {self.output_dir / 'entity_mapping.json'}")


def main():
    """
    Main entry point for the markdown anonymizer.
    """
    console = Console()
    
    console.print(Panel.fit("[bold cyan]Welcome to Markdown Anonymizer[/bold cyan]"))
    
    # Create menu
    console.print("\n[bold]Please select an option:[/bold]")
    console.print("1. Process all markdown files")
    console.print("2. Process a single file (test mode)")
    console.print("3. List available files")
    console.print("4. Exit")
    
    choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4"], default="1")
    
    if choice == "4":
        console.print("[green]Exiting program.[/green]")
        return
        
    # Get API key
    api_key = os.environ.get('GOOGLE_API_KEY') or GEMINI_API_KEY
    if not api_key:
        console.print("[yellow]Google API key not found in environment variables[/yellow]")
        api_key = Prompt.ask("[bold]Enter your Google API key[/bold]")
    
    # Get directories with absolute paths
    input_dir = Prompt.ask(
        "[bold]Enter input directory path[/bold]", 
        default=str(DEFAULT_INPUT_DIR)
    )
    
    # Check if directory exists
    input_path = Path(input_dir).resolve()  # Convert to absolute path
    if not input_path.exists():
        console.print(f"[bold yellow]Warning: Directory {input_path} does not exist[/bold yellow]")
        create_dir = Prompt.ask("[bold]Create this directory?[/bold]", choices=["y", "n"], default="y")
        if create_dir.lower() == "y":
            try:
                os.makedirs(input_path, exist_ok=True)
                console.print(f"[green]Created directory: {input_path}[/green]")
            except Exception as e:
                console.print(f"[bold red]Error creating directory: {e}[/bold red]")
                return
        else:
            alternative = Prompt.ask(
                "[bold]Enter alternative path[/bold]", 
                default=str(Path.cwd())  # Use current working directory as fallback
            )
            input_dir = alternative
    
    output_dir = Prompt.ask(
        "[bold]Enter output directory path[/bold]", 
        default=str(DEFAULT_OUTPUT_DIR)
    )
    
    # Create anonymizer
    try:
        recursive_search = True  # Default to recursive search
        anonymizer = MarkdownAnonymizer(api_key, input_dir, output_dir, recursive_search)
        
        if choice == "3":
            # List available files
            files = anonymizer.list_available_files()
            if files:
                console.print(Panel("[bold green]Available markdown files:[/bold green]"))
                for i, f in enumerate(files):
                    console.print(f"{i+1}. {f}")
            else:
                console.print(Panel("[bold yellow]No markdown files found in the input directory[/bold yellow]"))
            
            # Ask if user wants to process a file
            process_file = Prompt.ask(
                "[bold]Process a file?[/bold]", 
                choices=["y", "n"], 
                default="n"
            )
            
            if process_file.lower() == "y":
                file_choice = Prompt.ask("[bold]Enter file number or name[/bold]")
                try:
                    # Check if it's a number
                    idx = int(file_choice) - 1
                    if 0 <= idx < len(files):
                        anonymizer.process_files(files[idx])
                    else:
                        console.print("[bold red]Invalid file number[/bold red]")
                except ValueError:
                    # It's a name
                    anonymizer.process_files(file_choice)
            
        elif choice == "1":
            # Process all files
            anonymizer.process_files()
        else:
            # Process single file
            console.print(Panel("[bold]Available markdown files:[/bold]"))
            files = anonymizer.list_available_files()
            
            if not files:
                console.print("[bold yellow]No markdown files found in the input directory[/bold yellow]")
                return
                
            for i, f in enumerate(files):
                console.print(f"{i+1}. {f}")
                
            file_choice = Prompt.ask(
                "\n[bold]Enter file number or name (e.g., 2467.md)[/bold]"
            )
            
            try:
                # Check if it's a number
                idx = int(file_choice) - 1
                if 0 <= idx < len(files):
                    anonymizer.process_files(files[idx])
                else:
                    console.print("[bold red]Invalid file number[/bold red]")
            except ValueError:
                # It's a name
                anonymizer.process_files(file_choice)
            
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")

if __name__ == "__main__":
    main()