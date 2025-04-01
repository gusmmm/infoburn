"""
Command-line interface for the markdown anonymizer.
"""

import argparse
import os
from rich.console import Console
from rich.panel import Panel

from markdown_anonymizer.markdown_anonymizer import MarkdownAnonymizer

def parse_arguments():
    """
    Parse command line arguments for the markdown anonymizer.
    
    Returns:
        Parsed argument namespace
    """
    parser = argparse.ArgumentParser(description="Anonymize sensitive information in markdown files")
    
    parser.add_argument(
        "--api-key",
        help="Google API key for Gemini AI (can also use GOOGLE_API_KEY env variable)",
    )
    parser.add_argument(
        "--input-dir",
        default="../data/output/markdown/clean",
        help="Directory containing markdown files to anonymize"
    )
    parser.add_argument(
        "--output-dir",
        default="../data/output/markdown/anonymized",
        help="Directory where anonymized files will be saved"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()

def main():
    """
    Main entry point for the command-line interface.
    """
    args = parse_arguments()
    console = Console()
    
    console.print(Panel.fit("[bold cyan]Markdown Anonymizer[/bold cyan]"))
    
    # Get API key
    api_key = args.api_key or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        console.print("[yellow]Google API key not found in arguments or environment variables[/yellow]")
        api_key = console.input("[bold]Enter your Google API key: [/bold]")
    
    try:
        anonymizer = MarkdownAnonymizer(api_key, args.input_dir, args.output_dir)
        anonymizer.process_files()
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")

if __name__ == "__main__":
    main()