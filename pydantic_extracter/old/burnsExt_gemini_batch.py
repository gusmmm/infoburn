import os
import re
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt, IntPrompt
from rich.table import Table

from pydantic_extracter.old.burns_extracter_gemini_genai import BurnsExtracter
from typing import List, Optional, Tuple
import time
from pydantic_extracter.rate_limiter import RateLimiter

class BurnsExtracterBatch:
    """
    Batch processor for extracting burns data from multiple markdown files.
    Uses BurnsExtracter for individual file processing with options to skip already processed files.
    """
    
    def __init__(self, extracter: BurnsExtracter, requests_per_minute: Optional[int] = None, skip_existing: bool = True):
        """
        Initialize the batch processor.
        
        Args:
            extracter (BurnsExtracter): Configured BurnsExtracter instance
            requests_per_minute (Optional[int]): Maximum API requests per minute, if None no limit
            skip_existing (bool): Whether to skip processing files that already have JSON outputs
        """
        self.extracter = extracter
        self.console = Console()
        self.rate_limiter = RateLimiter(requests_per_minute) if requests_per_minute else None
        self.skip_existing = skip_existing
    
    def _json_exists_for_file(self, md_file: Path) -> bool:
        """
        Check if a corresponding JSON file already exists for a markdown file.
        
        Args:
            md_file (Path): Path to the markdown file
            
        Returns:
            bool: True if JSON exists, False otherwise
        """
        file_id = md_file.stem  # Get filename without extension
        json_path = self.extracter.output_dir / f"{file_id}.json"
        return json_path.exists()
    
    def _filter_already_processed(self, files: List[Path]) -> Tuple[List[Path], List[Path]]:
        """
        Filter out files that already have corresponding JSON outputs.
        
        Args:
            files (List[Path]): List of markdown files to check
            
        Returns:
            Tuple[List[Path], List[Path]]: Tuple containing (files_to_process, skipped_files)
        """
        if not self.skip_existing:
            return files, []
            
        files_to_process = []
        skipped_files = []
        
        for file in files:
            if self._json_exists_for_file(file):
                skipped_files.append(file)
            else:
                files_to_process.append(file)
                
        return files_to_process, skipped_files
    
    def _get_files_for_year(self, year: str) -> List[Path]:
        """
        Get all markdown files for a specific year prefix.
        
        Args:
            year (str): Year prefix (e.g., "23" for 2023)
            
        Returns:
            List[Path]: List of markdown files matching the year prefix
        """
        pattern = f"{year}*.md"
        return sorted(self.extracter.input_dir.glob(pattern))
        
    def _get_files_for_range(self, start_year: str, end_year: str) -> List[Path]:
        """
        Get all markdown files within a year range.
        
        Args:
            start_year (str): Starting year prefix
            end_year (str): Ending year prefix
            
        Returns:
            List[Path]: List of markdown files within the year range
        """
        files = []
        for year in range(int(start_year), int(end_year) + 1):
            year_prefix = f"{year:02d}"  # Convert to 2-digit format
            files.extend(self._get_files_for_year(year_prefix))
        return sorted(files)
    
    def _validate_year_input(self, year: str) -> bool:
        """Validate year input format."""
        return bool(re.match(r"^\d{2}$", year))
        
    def _validate_range_input(self, range_str: str) -> Optional[Tuple[str, str]]:
        """Validate year range input format and return start and end years."""
        if match := re.match(r"^(\d{2})-(\d{2})$", range_str):
            start, end = match.groups()
            if int(start) <= int(end):
                return start, end
        return None
        
    def show_menu(self) -> List[Path]:
        """
        Display interactive menu for selecting files to process.
        
        Returns:
            List[Path]: List of selected files to process
        """
        self.console.print(Panel(
            "[bold blue]Batch Burns Data Extractor[/bold blue]",
            subtitle="Select files to process",
            border_style="blue"
        ))
        
        # Show statistics first if skip_existing is enabled
        if self.skip_existing:
            self.show_processing_stats()
    
        # Show options
        table = Table(show_header=False, border_style="blue")
        table.add_row("[1]", "Process specific year (e.g., 23 for 2023)")
        table.add_row("[2]", "Process year range (e.g., 22-25)")
        table.add_row("[3]", "Process all files")
        table.add_row("[4]", "Force reprocess specific file")
        table.add_row("[5]", "Show processing statistics")
        table.add_row("[0]", "Exit")
        
        self.console.print(table)
        
        choice = IntPrompt.ask("Select an option", choices=["0", "1", "2", "3", "4", "5"])
        
        if choice == 0:
            return []
            
        elif choice == 1:
            while True:
                year = Prompt.ask("Enter year (2 digits)")
                if self._validate_year_input(year):
                    files = self._get_files_for_year(year)
                    if not files:
                        self.console.print(f"[yellow]No files found for year {year}[/yellow]")
                        continue
                    break
                self.console.print("[red]Invalid year format. Use 2 digits (e.g., 23)[/red]")
            return files
            
        elif choice == 2:
            while True:
                range_str = Prompt.ask("Enter year range (e.g., 22-25)")
                if range_tuple := self._validate_range_input(range_str):
                    start_year, end_year = range_tuple
                    files = self._get_files_for_range(start_year, end_year)
                    if not files:
                        self.console.print(f"[yellow]No files found in range {start_year}-{end_year}[/yellow]")
                        continue
                    break
                self.console.print("[red]Invalid range format. Use YY-YY (e.g., 22-25)[/red]")
            return files
            
        elif choice == 3:
            files = sorted(self.extracter.input_dir.glob("*.md"))
            if not files:
                self.console.print("[yellow]No markdown files found[/yellow]")
                return []
            return files
            
        elif choice == 4:
            # Force reprocess a specific file
            filename = Prompt.ask("Enter filename to reprocess (e.g., 2301.md)")
            if not filename.endswith(".md"):
                filename += ".md"
            
            file_path = self.extracter.input_dir / filename
            if not file_path.exists():
                self.console.print(f"[red]File not found: {filename}[/red]")
                return []
                
            # Force process just this one file
            self.force_process_file(file_path)
            return []
            
        elif choice == 5:
            # Show detailed statistics
            self.show_processing_stats()
            return []
    
    def process_files(self, files: List[Path]) -> None:
        """
        Process multiple files and show progress, skipping files that already have outputs if configured.
        
        Args:
            files (List[Path]): List of files to process
        """
        if not files:
            self.console.print("[yellow]No files to process[/yellow]")
            return
        
        # Filter files if skip_existing is enabled
        files_to_process, skipped_files = self._filter_already_processed(files)
        
        # Show skipped files if any
        if skipped_files:
            skipped_count = len(skipped_files)
            self.console.print(f"[yellow]Skipping {skipped_count} already processed files:[/yellow]")
            
            # Show first few skipped files if there are many
            max_to_show = min(5, len(skipped_files))
            for file in skipped_files[:max_to_show]:
                self.console.print(f"  [dim]⏩ {file.name}[/dim]")
                
            if len(skipped_files) > max_to_show:
                self.console.print(f"  [dim]... and {len(skipped_files) - max_to_show} more[/dim]")
        
        # If no files left to process after filtering
        if not files_to_process:
            self.console.print("[yellow]All files have already been processed. Nothing to do.[/yellow]")
            return
        
        # Show rate limit info if active
        if self.rate_limiter:
            self.console.print(
                f"[blue]Rate limiting enabled: "
                f"maximum {self.rate_limiter.requests_per_minute} requests per minute[/blue]"
            )
            
        # Show summary before processing
        self.console.print(Panel(
            f"[bold green]Found {len(files_to_process)} files to process[/bold green]" +
            (f" ({len(skipped_files)} skipped)" if skipped_files else ""),
            border_style="green"
        ))
        
        # Create progress bar with custom columns - FIX: Remove Console() from Progress constructor
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%")
        )
        
        with progress:
            task = progress.add_task("[cyan]Processing files...", total=len(files_to_process))
            
            successful = []
            failed = []
            
            for file in files_to_process:
                try:
                    # Apply rate limiting if enabled
                    if self.rate_limiter:
                        self.rate_limiter.wait()
                        
                    progress.update(task, description=f"[cyan]Processing {file.name}...")
                    output_path = self.extracter.process_file(file.name)
                    successful.append((file.name, output_path))
                    
                except Exception as e:
                    failed.append((file.name, str(e)))
                    self.console.print(f"[red]Error processing {file.name}: {e}[/red]")
                    
                finally:
                    progress.advance(task)
            
        # Show summary
        if successful:
            self.console.print("\n[bold green]Successfully processed files:[/bold green]")
            for filename, output_path in successful:
                self.console.print(f"✓ {filename} -> {output_path}")
                
        if failed:
            self.console.print("\n[bold red]Failed to process files:[/bold red]")
            for filename, error in failed:
                self.console.print(f"✗ {filename}: {error}")
                
        # Show final summary
        total = len(successful) + len(failed)
        self.console.print(Panel(
            f"[bold]Processing complete[/bold]\n"
            f"Total files: {total}\n"
            f"Successful: {len(successful)}\n"
            f"Failed: {len(failed)}",
            border_style="blue"
        ))
    
    def force_process_file(self, file_path: Path) -> Optional[Path]:
        """
        Force process a single file even if it already has a JSON output.
        
        Args:
            file_path (Path): Path to the markdown file to process
            
        Returns:
            Optional[Path]: Path to the output JSON file if successful, None otherwise
        """
        try:
            self.console.print(f"[yellow]Force processing file: {file_path.name}[/yellow]")
            
            # Apply rate limiting if enabled
            if self.rate_limiter:
                self.rate_limiter.wait()
                
            output_path = self.extracter.process_file(file_path.name)
            self.console.print(f"[green]Successfully processed {file_path.name}[/green]")
            return output_path
            
        except Exception as e:
            self.console.print(f"[red]Error processing {file_path.name}: {e}[/red]")
            return None

    def show_processing_stats(self) -> None:
        """
        Show statistics about processed and unprocessed files.
        """
        all_md_files = list(self.extracter.input_dir.glob("*.md"))
        all_json_files = list(self.extracter.output_dir.glob("*.json"))
        
        md_file_ids = {file.stem for file in all_md_files}
        json_file_ids = {file.stem for file in all_json_files}
        
        processed_ids = md_file_ids.intersection(json_file_ids)
        unprocessed_ids = md_file_ids - json_file_ids
        orphaned_ids = json_file_ids - md_file_ids
        
        # Create a table for statistics
        table = Table(title="Processing Statistics")
        table.add_column("Category", style="cyan")
        table.add_column("Count", justify="right", style="green")
        table.add_column("Details", style="dim")
        
        table.add_row(
            "Total Markdown Files", 
            str(len(all_md_files)),
            f"Files in {self.extracter.input_dir}"
        )
        table.add_row(
            "Processed Files", 
            str(len(processed_ids)),
            "Files with corresponding JSON outputs"
        )
        table.add_row(
            "Unprocessed Files", 
            str(len(unprocessed_ids)),
            "Files without JSON outputs"
        )
        table.add_row(
            "Orphaned JSON Files", 
            str(len(orphaned_ids)),
            "JSON files without corresponding markdown files"
        )
        
        self.console.print(table)
        
        # Show examples of each category
        def show_examples(ids, title, style):
            if ids:
                self.console.print(f"\n[{style}]{title}:[/{style}]")
                for id in sorted(list(ids)[:5]):  # Show first 5 examples
                    self.console.print(f"  [{style}]{id}[/{style}]")
                if len(ids) > 5:
                    self.console.print(f"  [dim]... and {len(ids) - 5} more[/dim]")
        
        show_examples(unprocessed_ids, "Unprocessed Files", "yellow")
        show_examples(orphaned_ids, "Orphaned JSON Files", "red")


def main():
    """Main function to run the batch processor."""
    console = Console()
    
    try:
        # Get API key
        from core_tools.key_manager import KeyManager
        key_manager = KeyManager()
        api_key = key_manager.get_key('GEMINI_API_KEY')
    except (ImportError, AttributeError):
        console.print("[yellow]KeyManager not found, attempting to use environment variable[/yellow]")
        api_key = os.environ.get("GOOGLE_API_KEY")
    
    if not api_key:
        api_key = Prompt.ask("[yellow]Please enter your Google API key[/yellow]", password=True)
    
    # Setup paths
    input_dir = Path("/home/gusmmm/Desktop/infoburn/data/output/markdown/clean")
    output_dir = Path("/home/gusmmm/Desktop/infoburn/data/output/json/burns")
    
    # Ask about skipping existing files
    skip_existing = Prompt.ask(
        "Skip files that already have JSON outputs?",
        choices=["y", "n"],
        default="y"
    ) == "y"
    
    # Ask for rate limiting
    use_rate_limit = Prompt.ask(
        "Enable rate limiting?",
        choices=["y", "n"],
        default="y"
    ) == "y"
    
    requests_per_minute = None
    if use_rate_limit:
        requests_per_minute = IntPrompt.ask(
            "Enter maximum requests per minute",
            default=15
        )
    
    # Create extracters with options
    extracter = BurnsExtracter(api_key, input_dir, output_dir)
    batch_extracter = BurnsExtracterBatch(
        extracter,
        requests_per_minute=requests_per_minute,
        skip_existing=skip_existing
    )
    
    # Show menu and process files
    while True:
        files = batch_extracter.show_menu()
        if not files:  # User selected exit
            break
        batch_extracter.process_files(files)
        
        if not Prompt.ask("\nProcess more files?", choices=["y", "n"], default="n") == "y":
            break
    
    console.print("[bold blue]Batch processing complete![/bold blue]")

if __name__ == "__main__":
    main()