"""
Simple markdown anonymizer that focuses on identifying and replacing sensitive information.
Uses Google's Gemini AI for entity recognition.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
import json
import logging

from google import genai
from google.genai import types
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

class SimpleAnonymizer:
    """
    Basic version of markdown anonymizer that focuses on identifying and
    replacing sensitive information with anonymous identifiers.
    """
    
    def __init__(self, api_key: str, input_dir: str, output_dir: str):
        """Initialize the anonymizer with basic settings."""
        self.api_key = api_key
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.console = Console()
        self.entity_map = {}  # Maps original values to anonymized identifiers
        
        # Configure Gemini AI
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.5-pro-exp-03-25"
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            filename='anonymizer.log'
        )
        self.logger = logging.getLogger('SimpleAnonymizer')
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
    
    def identify_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Use Gemini AI to identify sensitive information in the text.

        Args:
            text: The markdown content to analyze

        Returns:
            Dictionary mapping entity types to lists of found entities
        """
        self.console.print("\n[bold yellow]Debug: Starting entity identification[/bold yellow]")

        # Define the schema for entity identification
        schema = types.Schema(
            type='OBJECT',
            properties={
                'patient_names': types.Schema(
                    type='ARRAY',
                    items=types.Schema(type='STRING'),
                    description='List of patient names found in the text'
                ),
                'doctor_names': types.Schema(
                    type='ARRAY',
                    items=types.Schema(type='STRING'),
                    description='List of doctor names found in the text'
                ),
                'addresses': types.Schema(
                    type='ARRAY',
                    items=types.Schema(type='STRING'),
                    description='List of addresses found in the text'
                ),
                'phone_numbers': types.Schema(
                    type='ARRAY',
                    items=types.Schema(type='STRING'),
                    description='List of phone numbers found in the text'
                ),
                'id_numbers': types.Schema(
                    type='ARRAY',
                    items=types.Schema(type='STRING'),
                    description='List of identification numbers found in the text'
                )
            }
        )

        try:
            # Print the text being analyzed
            self.console.print("\n[bold blue]Text being analyzed:[/bold blue]")
            self.console.print(Panel(text[:500] + "..." if len(text) > 500 else text))

            # Create the prompt
            prompt = (
                "Your task is to identify sensitive information in Portuguese medical text.\n"
                "DO not anonymize or remove the number of the 'DOCUMENT ID:'  in the header.\n"
                "Review the the answer bofore sending it to the user.\n"
                "Look for and extract these specific items:\n"
                "1. Patient names (full names or just first/last names)\n"
                "2. Doctor names (including titles like 'Dr.' or 'Dra.')\n"
                "3. Addresses (complete or partial)\n"
                "4. Phone numbers (any format)\n"
                "5. ID numbers (any type of identification number)\n\n"
                "Text to analyze:\n" + text + "\n\n"
                "Return the entities in the following JSON format:\n"
                "{\n"
                '  "patient_names": [],\n'
                '  "doctor_names": [],\n'
                '  "addresses": [],\n'
                '  "phone_numbers": [],\n'
                '  "id_numbers": []\n'
                "}"
            )

            self.console.print("\n[yellow]Sending request to Gemini API...[/yellow]")

            # Create the generation config
            generation_config = types.GenerateContentConfig(
                temperature=0,
                response_mime_type='application/json',
                response_schema=schema # Remove the schema
            )

            # Send the request
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=generation_config
            )

            # Print raw response for debugging
            self.console.print("\n[bold blue]Raw API Response:[/bold blue]")
            self.console.print(Panel(str(response)))

            # Extract and print the entities
            if hasattr(response, 'candidates') and response.candidates:
                result = response.candidates[0].content.parts[0].text # Extract the text
                self.console.print("\n[bold green]Extracted Entities:[/bold green]")
                self.console.print(Panel(str(result)))

                # Parse the JSON string
                try:
                    entities = json.loads(result)
                    return entities
                except json.JSONDecodeError as e:
                    self.console.print(f"[bold red]Error decoding JSON: {e}[/bold red]")
                    return {}
            else:
                self.console.print("[bold red]No entities found in API response[/bold red]")
                return {}

        except Exception as e:
            self.logger.error(f"Error identifying entities: {e}")
            self.console.print(f"[bold red]Error during entity identification:[/bold red] {str(e)}")
            # Print the full traceback for debugging
            import traceback
            self.console.print(Panel(traceback.format_exc(), title="[red]Full Error Traceback[/red]"))
            return {}
    
    def anonymize_text(self, text: str) -> str:
        """
        Replace sensitive information with anonymous identifiers.
        
        Args:
            text: Original text content
            
        Returns:
            Anonymized text content
        """
        entities = self.identify_entities(text)
        anonymized = text
        
        # Process each entity type
        entity_types = {
            'patient_names': 'PATIENT',
            'doctor_names': 'DOCTOR',
            'addresses': 'ADDRESS',
            'phone_numbers': 'PHONE',
            'id_numbers': 'ID'
        }
        
        for entity_type, prefix in entity_types.items():
            if entity_type in entities:
                for i, entity in enumerate(entities[entity_type]):
                    if entity not in self.entity_map:
                        self.entity_map[entity] = f"{prefix}_{i+1}"
                    anonymized = anonymized.replace(entity, self.entity_map[entity])
        
        return anonymized
    
    def process_file(self, filepath: Path) -> bool:
        """
        Process a single markdown file with detailed console output.
        
        Args:
            filepath: Path to the markdown file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.console.print(Panel(f"[bold blue]Processing file: {filepath.name}[/bold blue]"))
            
            # Read file
            self.console.print("[yellow]Reading file...[/yellow]")
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Show file content
            self.console.print("\n[bold green]Original Content:[/bold green]")
            self.console.print(Panel(content, title="Original Text"))
            
            # Process content
            self.console.print("\n[yellow]Identifying entities...[/yellow]")
            entities = self.identify_entities(content)
            
            # Show identified entities
            self.console.print("\n[bold green]Identified Entities:[/bold green]")
            for entity_type, entities_list in entities.items():
                if entities_list:
                    self.console.print(f"\n[cyan]{entity_type.replace('_', ' ').title()}:[/cyan]")
                    for entity in entities_list:
                        self.console.print(f"  • {entity}")
            
            # Anonymize content
            self.console.print("\n[yellow]Anonymizing content...[/yellow]")
            anonymized = self.anonymize_text(content)
            
            # Show anonymized content
            self.console.print("\n[bold green]Anonymized Content:[/bold green]")
            self.console.print(Panel(anonymized, title="Anonymized Text"))
            
            # Save file
            output_file = self.output_dir / filepath.name
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(anonymized)
            
            # Show mapping
            self.console.print("\n[bold green]Entity Mapping:[/bold green]")
            for original, anonymized in self.entity_map.items():
                self.console.print(f"[cyan]{original}[/cyan] → [yellow]{anonymized}[/yellow]")
            
            self.console.print(f"\n[bold green]✓[/bold green] File saved to: {output_file}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error processing file {filepath}: {e}")
            self.console.print(f"[bold red]Error:[/bold red] {str(e)}")
            return False

def main():
    """Enhanced command-line interface for testing with detailed output."""
    console = Console()
    
    try:
        # Get API key
        from core_tools.key_manager import KeyManager
        key_manager = KeyManager()
        api_key = key_manager.get_key('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Setup paths
        console.print(Panel.fit("[bold cyan]Markdown Anonymizer[/bold cyan]"))
        
        # Get current working directory
        cwd = Path.cwd()
        console.print(f"[yellow]Current working directory: {cwd}[/yellow]\n")
        
        # List available markdown files
        md_files = list(cwd.glob("**/*.md"))
        if not md_files:
            console.print("[bold red]No markdown files found![/bold red]")
            return
        
        # Show available files
        console.print("[bold green]Available markdown files:[/bold green]")
        for i, file in enumerate(md_files, 1):
            console.print(f"{i}. {file.relative_to(cwd)}")
        
        # Get file selection
        choice = console.input("\n[bold]Enter file number to process (or 'q' to quit): [/bold]")
        if choice.lower() == 'q':
            return
            
        try:
            file_index = int(choice) - 1
            if 0 <= file_index < len(md_files):
                selected_file = md_files[file_index]
            else:
                console.print("[bold red]Invalid file number![/bold red]")
                return
        except ValueError:
            console.print("[bold red]Invalid input![/bold red]")
            return
        
        # Setup anonymizer
        input_dir = selected_file.parent
        output_dir = input_dir / "anonymized"
        
        anonymizer = SimpleAnonymizer(api_key, input_dir, output_dir)
        
        # Process file
        if anonymizer.process_file(selected_file):
            console.print("\n[bold green]Processing completed successfully![/bold green]")
        else:
            console.print("\n[bold red]Error processing file![/bold red]")
            
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")

if __name__ == "__main__":
    main()