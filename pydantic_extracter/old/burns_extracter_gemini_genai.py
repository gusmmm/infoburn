import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import copy

from google import genai
from google.genai import types
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.prompt import Prompt
from pydantic_classifier.burns_model import BurnLocation, BurnDepth, BurnMechanism, AccidentType, BurnInjury, BurnsModel
from pydantic import TypeAdapter, ValidationError


class BurnsExtracter:
    """
    BurnsExtracter is responsible for extracting burns data from medical text files.
    It returns a pydantic model containing the extracted information.
    The class uses the Gemini AI API for natural language processing tasks.
    """
    
    def __init__(self, api_key: str, input_dir: str, output_dir: str):
        """
        Initialize the burns extracter with basic settings.
        
        Args:
            api_key (str): Google API key for Gemini AI
            input_dir (str): Directory containing markdown files to process
            output_dir (str): Directory where JSON output will be saved
        """
        self.api_key = api_key
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.console = Console()
        
        # Configure Gemini AI
        self.client = genai.Client(api_key=self.api_key)
        #self.model_name = "gemini-2.5-pro-exp-03-25"
        self.model_name = "gemini-2.0-flash"
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            filename='burnextracter.log',
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('BurnsExtracter')
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

   
    
    def _read_markdown_file(self, file_path: Path) -> str:
        """
        Read the content of a markdown file.
        
        Args:
            file_path (Path): Path to the markdown file
        
        Returns:
            str: Content of the markdown file
        
        Raises:
            FileNotFoundError: If the file does not exist
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
    
    def _create_prompt(self, text: str, file_id: str) -> str:
        """
        Create a prompt for the Gemini AI to extract burn information.
        
        Args:
            text (str): Medical text content
            file_id (str): ID from the file name
        
        Returns:
            str: Formatted prompt for Gemini AI
        """
        # Define the prompt with detailed instructions for extraction
        prompt = (
            "You are a medical data extraction assistant. Extract burn injury information from the following medical text. "
            "Return a complete, well-formatted JSON that follows the schema structure exactly. "
            "Ensure all JSON objects and arrays are properly closed with matching braces and brackets.\n\n"
            "Key information to extract:\n"
            "- Total body surface area (TBSA) affected by burns (percentage)\n"
            "- Burn mechanism (Heat, Electrical discharge, Friction, Chemicals, Radiation, or unknown)\n"
            "- Type of accident (domestic, workplace, or other)\n"
            "- The agent that caused the burn (e.g., fire, gas, chemical name)\n"
            "- Whether it involved wildfire, bonfire, fireplace, violence, or was a suicide attempt\n"
            "- Whether escharotomy was performed\n"
            "- Any associated trauma (list them)\n"
            "- Details of each burn injury including:\n"
            "  * Location (head, neck, face, upper extremity, hand, etc.)\n"
            "  * Laterality (left, right, bilateral, or unspecified).\n"
            "  * Depth (1st degree, 2nd degree partial, 2nd degree full, 3rd degree, 4th degree)\n"
            "  * Whether the burn is circumferential\n\n"
            f"The patient ID is: {file_id}\n\n"
            "Medical Text:\n"
            f"{text}\n\n"
            "Provide a complete and accurate extraction. If information is not explicitly mentioned in the text, "
            "or is missing in the text. use null for the result of the fields according to type and do not try to guess or give an opinion. "
            "IMPORTANT: Ensure the JSON response is complete and properly formatted. "
            "Do not truncate or leave any objects incomplete."
        )
        return prompt
    
    def _clean_json_response(self, text: str) -> str:
        """
        Clean and validate the JSON response from Gemini AI.
        
        Args:
            text (str): Raw response text from Gemini AI
            
        Returns:
            str: Cleaned JSON string
            
        Raises:
            ValueError: If JSON cleaning fails
        """
        try:
            # Log the original response for debugging
            self.logger.debug(f"Original response:\n{text}")
            self.console.print("[dim]Starting JSON cleaning process...[/dim]")
            
            # Remove any markdown formatting
            cleaned = text.strip()
            if cleaned != text:
                self.console.print("[dim]Removed whitespace[/dim]")
            
            # Handle code block markers
            if cleaned.startswith("```") and cleaned.endswith("```"):
                cleaned = cleaned[3:-3].strip()
                self.console.print("[dim]Removed code block markers[/dim]")
                
            # Remove json language identifier if present    
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
                self.console.print("[dim]Removed 'json' prefix[/dim]")
                
            # Try to validate JSON structure
            try:
                # First attempt to parse
                json.loads(cleaned)
                self.console.print("[dim]JSON is valid[/dim]")
                return cleaned
            except json.JSONDecodeError as je:
                # Show the problematic part of the JSON
                error_location = je.pos
                context = 40  # Show 40 chars before and after error
                start = max(0, error_location - context)
                end = min(len(cleaned), error_location + context)
                
                self.console.print("\n[yellow]JSON Error Context:[/yellow]")
                self.console.print(Panel(
                    f"{cleaned[start:error_location]}[bold red]█[/bold red]{cleaned[error_location:end]}",
                    title=f"Error at position {error_location}",
                    border_style="yellow"
                ))
                
                # Try to fix common JSON formatting issues
                cleaned_original = cleaned
                cleaned = cleaned.replace("'", '"')  # Replace single quotes with double quotes
                cleaned = cleaned.replace("None", "null")  # Replace Python None with JSON null
                cleaned = cleaned.replace("True", "true")  # Replace Python True with JSON true
                cleaned = cleaned.replace("False", "false")  # Replace Python False with JSON false
                
                if cleaned != cleaned_original:
                    self.console.print("[dim]Applied JSON formatting fixes[/dim]")
                
                # Verify JSON completeness
                def is_json_complete(json_str: str) -> bool:
                    """Check if JSON string is complete by counting braces and brackets"""
                    stack = []
                    for char in json_str:
                        if char in '{[':
                            stack.append(char)
                        elif char in '}]':
                            if not stack:
                                return False
                            if (char == '}' and stack[-1] != '{') or (char == ']' and stack[-1] != '['):
                                return False
                            stack.pop()
                    return len(stack) == 0
                
                if not is_json_complete(cleaned):
                    self.console.print("[bold red]Warning: JSON response appears incomplete[/bold red]")
                    self.logger.warning("Incomplete JSON detected")
                    raise ValueError("Incomplete JSON response from API")
                    
                return cleaned
                
        except Exception as e:
            self.logger.error(f"Error cleaning JSON response: {str(e)}")
            raise ValueError(f"Failed to clean JSON response: {str(e)}")
    
    def _deduplicate_burns(self, burns_model: BurnsModel) -> BurnsModel:
        """
        Remove duplicate burn entries from the BurnsModel.
        
        Args:
            burns_model (BurnsModel): Original burns model
            
        Returns:
            BurnsModel: Burns model with deduplicated burns list
        """
        if not burns_model.burns:
            return burns_model
            
        # Convert burns to hashable format for deduplication
        unique_burns = []
        seen = set()
        
        for burn in burns_model.burns:
            # Create a tuple of burn attributes for comparison
            burn_key = (
                burn.location,
                burn.laterality,
                burn.depth,
                burn.circumferencial
            )
            
            if burn_key not in seen:
                seen.add(burn_key)
                unique_burns.append(burn)
                
        if len(burns_model.burns) != len(unique_burns):
            self.console.print(
                f"[yellow]Warning: Removed {len(burns_model.burns) - len(unique_burns)} duplicate burn entries[/yellow]"
            )
            self.logger.warning(
                f"Removed {len(burns_model.burns) - len(unique_burns)} duplicate burn entries"
            )
            
        # Create new model with deduplicated burns
        model_dict = burns_model.model_dump()
        model_dict['burns'] = unique_burns
        return BurnsModel.model_validate(model_dict)
    
    def extract_burns_data(self, filename: str) -> tuple[BurnsModel, str]:
        """
        Extract burn information from a markdown file using Gemini AI.
        
        Args:
            filename (str): Name of the markdown file (without path)
    
        Returns:
            tuple[BurnsModel, str]: Tuple containing (BurnsModel instance, file_id)
            
        Raises:
            ValueError: If the extraction fails or validation fails
        """
        file_id = filename.split('.')[0]
        file_path = self.input_dir / filename
        
        try:
            # Read the file content
            self.console.print(f"[blue]Reading file: {filename}[/blue]")
            text = self._read_markdown_file(file_path)
            
            # Create the prompt
            prompt = self._create_prompt(text, file_id)
            
            # Create the generation config
            generation_config = types.GenerateContentConfig(
                temperature=0,
                response_mime_type='application/json',
                response_schema=BurnsModel,
                # Remove stop_sequences parameter
            )

            # Create structured request with safety settings
            request = {
                "contents": prompt,
                "config": generation_config,
                
            }
            # print the model name
            self.console.print(f"[blue]Using model: {self.model_name}[/blue]")
            response = self.client.models.generate_content(
                model=self.model_name,
                **request
            )
            
            # Process the response
            if not response.text:
                raise ValueError("Empty response from Gemini API")
            
            # Add detailed response visualization
            self.console.print("\n[bold yellow]Raw API Response:[/bold yellow]")
            self.console.print(Panel(
                response.text,
                title="Gemini API Response",
                border_style="yellow",
                padding=(1,2)
            ))
            
            # Parse and validate JSON response
            try:
                self.logger.info(f"Response from Gemini API: {response.text}")
                
                # Add debug visualization before cleaning
                self.console.print("\n[bold blue]Attempting to clean JSON...[/bold blue]")
                
                try:
                    json_str = self._clean_json_response(response.text)
                    self.console.print("\n[bold green]Cleaned JSON:[/bold green]")
                    self.console.print(Panel(
                        json_str,
                        title="Cleaned JSON",
                        border_style="green",
                        padding=(1,2)
                    ))
                    
                    data = json.loads(json_str)
                    
                except (ValueError, json.JSONDecodeError) as e:
                    self.logger.error(f"JSON parsing error: {str(e)}")
                    self.console.print(f"\n[bold red]JSON Parsing Error:[/bold red]")
                    self.console.print(Panel(
                        str(e),
                        title="Error Details",
                        border_style="red",
                        padding=(1,2)
                    ))
                    raise ValueError(f"Invalid JSON from API: {str(e)}")
                
                # Create BurnsModel instance and deduplicate burns
                burns_model = BurnsModel.model_validate(data)
                burns_model = self._deduplicate_burns(burns_model)
                
                self.console.print("[green]Successfully extracted burn information[/green]")
                
                return burns_model, file_id
                    
            except ValidationError as e:
                self.logger.error(f"Validation error: {e}")
                raise ValueError(f"Failed to validate response against BurnsModel: {e}")
                
        except Exception as e:
            self.logger.error(f"Error extracting burns data: {e}")
            raise
    
    def save_json(self, burns_model: BurnsModel, file_id: str) -> Path:
        """
        Save the BurnsModel as JSON.
        
        Args:
            burns_model (BurnsModel): Pydantic model to save
            file_id (str): ID to use in the filename
            
        Returns:
            Path: Path to the saved JSON file
        """
        output_path = self.output_dir / f"{file_id}.json"
        
        try:
            # Convert the model to a dictionary
            data = burns_model.model_dump(exclude_none=True)
            
            # Add the ID field
            data["ID"] = file_id
            
            # Save to JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            self.console.print(f"[green]Saved JSON to: {output_path}[/green]")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error saving JSON: {e}")
            raise
    
    def process_file(self, filename: str) -> Path:
        """
        Process a single markdown file: extract burns data and save as JSON.
        
        Args:
            filename (str): Name of the markdown file (without path)
            
        Returns:
            Path: Path to the saved JSON file
        """
        try:
            burns_model, file_id = self.extract_burns_data(filename)
            return self.save_json(burns_model, file_id)
        except Exception as e:
            self.console.print(f"[bold red]Error processing file {filename}: {e}[/bold red]")
            raise


def main():
    """Main function to test the BurnsExtracter with a single file."""
    console = Console()
    
    console.print(Panel(
        "[bold blue]Burns Data Extractor[/bold blue]", 
        subtitle="Extract burn information from medical notes",
        border_style="blue"
    ))

    try:
        from core_tools.key_manager import KeyManager
        key_manager = KeyManager()
        api_key = key_manager.get_key('GEMINI_API_KEY')
    except (ImportError, AttributeError):
        console.print("[yellow]KeyManager not found, attempting to use environment variable[/yellow]")
        api_key = os.environ.get("GOOGLE_API_KEY")
    
    if not api_key:
        api_key = Prompt.ask("[yellow]Please enter your Google API key[/yellow]", password=True)
    
    input_dir = Path("/home/gusmmm/Desktop/infoburn/data/output/markdown/clean")
    output_dir = Path("/home/gusmmm/Desktop/infoburn/data/output/json/burns")
    
    extracter = BurnsExtracter(api_key, input_dir, output_dir)
    test_file = "2301.md"
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Processing file...", total=1)
        
        try:
            console.print(f"\n[bold]Processing test file: {test_file}[/bold]")
            output_path = extracter.process_file(test_file)
            progress.update(task, advance=1)
            console.print(f"[bold green]✓ Successfully processed {test_file}[/bold green]")
            console.print(f"[blue]Output saved to: {output_path}[/blue]")
        except Exception as e:
            progress.update(task, advance=1)
            console.print(f"[bold red]✗ Failed to process {test_file}[/bold red]")
            console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    main()