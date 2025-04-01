"""
Enhanced Markdown Cleaner for Medical Notes
------------------------------------------

This script processes markdown files from PDF conversions and formats them
for optimal LLM analysis. It handles:
- Removing duplicate lines and noise
- Standardizing section formatting with clear boundaries
- Adding metadata and document structure
- Creating LLM-friendly content organization

Dependencies:
- rich: For beautiful terminal output
- pathlib: For cross-platform path handling
- logging: For error tracking and debugging

Author: [Your Name]
Version: 2.0
"""

import os
import re
import sys
import logging
import traceback
from pathlib import Path
from typing import List, Dict, Pattern, Optional
from collections import defaultdict
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn


class MarkdownCleaningError(Exception):
    """Custom exception for markdown cleaning errors."""
    pass


class MarkdownCleaner:
    """
    Handles the cleaning and formatting of markdown files for LLM analysis.
    Provides consistent formatting and clear section boundaries.
    """
    
    # Section style templates for different note types
    SECTION_STYLES = {
        "admission": {
            "top": "╔═══════════════════ ADMISSION NOTE START ═══════════════════╗",
            "bottom": "╚════════════════════ ADMISSION NOTE END ════════════════════╝"
        },
        "release": {
            "top": "╔═══════════════════ RELEASE NOTE START ════════════════════╗",
            "bottom": "╚════════════════════ RELEASE NOTE END ═════════════════════╝"
        },
        "provisory - death report": {
            "top": "╔════════════ PROVISORY DEATH REPORT START ═════════════╗",
            "bottom": "╚════════════ PROVISORY DEATH REPORT END ═══════════════╝"
        },
        "final - death report": {
            "top": "╔═════════════ FINAL DEATH REPORT START ══════════════╗",
            "bottom": "╚═════════════ FINAL DEATH REPORT END ════════════════╝"
        }
    }
    
    def __init__(self, input_folder: str, output_folder: str):
        """
        Initialize the cleaner with input and output folders.
        
        Args:
            input_folder (str): Path to folder containing markdown files
            output_folder (str): Path to output folder for cleaned markdown files
        """
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.console = Console()
        
        # Regex patterns for identifying section markers
        self.section_markers = {
            "start": re.compile(r"^(>>|═+)\s*(?:START|start)\s+.*\s*(?:NOTE|note)\s*(<<|═+)\s*$"),
            "end": re.compile(r"^(>>|═+)\s*(?:END|end)\s+.*\s*(?:NOTE|note)\s*(<<|═+)\s*$")
        }
        
        # Markers for document structure
        self.header_marker = "╔══════════════════════════════════════════════════════════════╗"
        self.footer_marker = "╚══════════════════════════════════════════════════════════════╝"
        self.metadata_marker = "║"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('md_cleaning.log'),
                logging.StreamHandler()
            ]
        )
    
    def print_status(self, message: str, style: str = "info") -> None:
        """
        Print beautifully formatted status messages to the terminal.
        
        Args:
            message (str): The message to display
            style (str): The style of the message (info, error, success)
        """
        styles = {
            "info": "blue",
            "error": "red",
            "success": "green"
        }
        self.console.print(Panel(message, style=styles.get(style, "white")))
    
    def _format_section_header(self, section_name: str) -> str:
        """
        Format a section header with clear boundaries for LLM recognition.
        
        Args:
            section_name (str): Name of the section
            
        Returns:
            str: Formatted section header
        """
        return f"{self.header_marker}\n{self.metadata_marker} SECTION: {section_name.upper()} {self.metadata_marker}\n{self.footer_marker}"
    
    def _is_section_marker(self, line: str) -> bool:
        """
        Check if line is a section marker.
        
        Args:
            line (str): Line to check
            
        Returns:
            bool: True if line is a section marker
        """
        return any(pattern.match(line.strip()) for pattern in self.section_markers.values())
    
    def _clean_line(self, line: str) -> str:
        """
        Clean individual line and improve section markers for LLM readability.
        
        Args:
            line (str): Line to clean
            
        Returns:
            str: Cleaned line
        """
        line = line.strip()
        
        # Handle section headers (## style markers)
        if line.startswith("## "):
            section_type = line.lower().replace("## ", "").replace(" note", "").strip()
            if section_type in self.SECTION_STYLES:
                return f"\n{self.SECTION_STYLES[section_type]['top']}"
        
        # Handle section content
        if line.startswith("---"):
            return ""  # Remove old separators
        if line == "```":
            return ""  # Remove code block markers that might confuse LLMs
        
        # Clean up extra whitespace for consistency
        return ' '.join(line.split())
    
    def _remove_duplicates(self, lines: List[str]) -> List[str]:
        """
        Remove duplicate lines while preserving section markers.
        
        Args:
            lines (List[str]): List of content lines
            
        Returns:
            List[str]: Deduplicated lines
        """
        seen_lines = set()
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:  # Skip empty lines
                continue
            
            # Always keep section markers and formatted headers/footers
            if (self._is_section_marker(line) or 
                line.startswith("╔") or 
                line.startswith("╚") or 
                line.startswith("║")):
                cleaned_lines.append(line)
                continue
            
            if line not in seen_lines:
                seen_lines.add(line)
                cleaned_lines.append(line)
        
        return cleaned_lines
    
    def _add_section_tags(self, content: str) -> str:
        """
        Add LLM-friendly tags to key sections for better analysis.
        
        Args:
            content (str): Document content
            
        Returns:
            str: Content with added tags
        """
        # Add LLM-friendly section tags for key medical information
        patterns = [
            (r"(?i)(laboratory results|lab results|laboratory findings|lab data)(:?)", r"<LABORATORY_RESULTS>\1\2"),
            (r"(?i)(vital signs|vitals)(:?)", r"<VITAL_SIGNS>\1\2"),
            (r"(?i)(diagnosis|diagnoses|impression)(:?)", r"<DIAGNOSIS>\1\2"),
            (r"(?i)(treatment plan|treatment|plan of care)(:?)", r"<TREATMENT_PLAN>\1\2"),
            (r"(?i)(medications|medication list|meds)(:?)", r"<MEDICATIONS>\1\2"),
            (r"(?i)(allergies|allergy list)(:?)", r"<ALLERGIES>\1\2"),
            (r"(?i)(medical history|past medical history|pmh)(:?)", r"<MEDICAL_HISTORY>\1\2"),
            (r"(?i)(physical examination|physical exam|exam)(:?)", r"<PHYSICAL_EXAM>\1\2"),
            (r"(?i)(assessment|clinical assessment)(:?)", r"<ASSESSMENT>\1\2")
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        return content
    
    def clean_file(self, input_path: str, output_path: str) -> None:
        """
        Clean and improve a single markdown file for LLM analysis.
        
        Args:
            input_path (str): Path to the input markdown file
            output_path (str): Path to save the cleaned markdown file
            
        Raises:
            MarkdownCleaningError: If there is an error cleaning the file
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add file metadata header
            file_name = os.path.basename(input_path)
            metadata_header = [
                self.header_marker,
                f"{self.metadata_marker} DOCUMENT ID: {file_name[:-3]}",
                f"{self.metadata_marker} DOCUMENT TYPE: MEDICAL NOTES",
                f"{self.metadata_marker} FORMAT: MARKDOWN",
                f"{self.metadata_marker} STATUS: PROCESSED AND STRUCTURED FOR LLM ANALYSIS",
                self.footer_marker,
                "",
                "# Patient Medical Record",
                ""
            ]
            
            # Process content
            lines = content.split('\n')
            current_section = None
            cleaned_lines = []
            
            for line in lines:
                clean_line = self._clean_line(line)
                if not clean_line:
                    continue
                
                # Check for section transitions
                if clean_line.startswith("╔═══") and "START" in clean_line:
                    current_section = next(
                        (k for k, v in self.SECTION_STYLES.items() 
                        if v["top"] == clean_line), None)
                    cleaned_lines.append(clean_line)
                elif current_section and clean_line.strip() and not clean_line.startswith("╔") and not clean_line.startswith("╚"):
                    cleaned_lines.append(clean_line)
                elif current_section and (clean_line.startswith("## ") or clean_line.startswith("#")):
                    # Add section end marker before starting new section
                    cleaned_lines.append(self.SECTION_STYLES[current_section]["bottom"])
                    current_section = None
                    if not clean_line.startswith("# Patient"):  # Skip main title
                        cleaned_lines.append(clean_line)
                else:
                    cleaned_lines.append(clean_line)
            
            # Add final section end marker if needed
            if current_section:
                cleaned_lines.append(self.SECTION_STYLES[current_section]["bottom"])
            
            # Remove duplicates while preserving markers
            final_lines = self._remove_duplicates(cleaned_lines)
            
            # Add LLM-friendly section tags
            content_with_tags = self._add_section_tags('\n'.join(final_lines))
            final_lines = content_with_tags.split('\n')
            
            # Combine metadata and content
            full_content = metadata_header + final_lines
            
            # Add LLM-friendly footer
            full_content.extend([
                "",
                "<!-- END OF DOCUMENT -->",
                f"<!-- PATIENT_ID: {file_name[:-3]} -->",
                "<!-- DOCUMENT_FORMAT: STRUCTURED_MEDICAL_NOTES -->"
            ])
            
            # Write improved content
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(full_content))
            
            logging.info(f"Successfully cleaned {input_path}")
            self.print_status(f"✓ Cleaned: {os.path.basename(input_path)}", "success")
            
        except Exception as e:
            error_msg = f"Error processing {input_path}: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            raise MarkdownCleaningError(error_msg)
    
    def process_files(self) -> None:
        """
        Process all markdown files in the input folder.
        
        Raises:
            MarkdownCleaningError: If there is a critical error during processing
        """
        try:
            # Create output directory if it doesn't exist
            Path(self.output_folder).mkdir(parents=True, exist_ok=True)
            self.print_status(f"✓ Output folder ready: {self.output_folder}", "success")
            
            # Get markdown files
            md_files = [f for f in os.listdir(self.input_folder) if f.endswith('.md')]
            self.print_status(f"Found {len(md_files)} markdown files to process", "info")
            
            # Process each markdown file with progress bar
            with Progress() as progress:
                task = progress.add_task("Cleaning markdown files...", total=len(md_files))
                
                for filename in md_files:
                    try:
                        input_path = os.path.join(self.input_folder, filename)
                        output_path = os.path.join(self.output_folder, filename)
                        self.clean_file(input_path, output_path)
                        progress.update(task, advance=1)
                        
                    except MarkdownCleaningError as e:
                        self.print_status(f"Error with {filename}: {str(e)}", "error")
                        continue
            
            self.print_status("Markdown cleaning completed successfully!", "success")
            
        except Exception as e:
            error_msg = f"Critical error: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            self.print_status(error_msg, "error")
            raise MarkdownCleaningError(error_msg)
    
    def run(self) -> None:
        """
        Execute the markdown cleaning process.
        """
        self.console.print("\n[bold blue]Enhanced Markdown Cleaner for LLM Analysis[/bold blue]")
        self.console.print("=" * 60 + "\n")
        
        try:
            self.process_files()
        except Exception:
            self.print_status("Cleaning failed! Check the logs for details.", "error")
            sys.exit(1)


if __name__ == "__main__":
    # Updated input and output folders
    input_folder = "./data/output/markdown"
    output_folder = "./data/output/markdown/clean"
    
    cleaner = MarkdownCleaner(input_folder, output_folder)
    cleaner.run()


