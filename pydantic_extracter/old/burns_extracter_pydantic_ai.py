import os
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import copy

from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.gemini import GeminiModelSettings
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.settings import ModelSettings

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.prompt import Prompt

from pydantic_classifier.burns_model import BurnLocation, BurnDepth, BurnMechanism, AccidentType, BurnInjury, BurnsModel


class BurnsExtracter:
    """
    BurnsExtracter uses Pydantic AI to extract burns data from medical text files.
    It returns a BurnsModel containing the extracted information.
    """
    
    def __init__(self, api_key: str, input_dir: str, output_dir: str):
        """
        Initialize the burns extracter with API key and directories.
        
        Args:
            api_key (str): Gemini API key
            input_dir (str): Directory containing markdown files to process
            output_dir (str): Directory where JSON output will be saved
        """
        self.api_key = api_key
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.console = Console()
        
        # Configure Gemini model
        self.model = GeminiModel('gemini-2.5-pro-exp-03-25', provider=GoogleGLAProvider(api_key=self.api_key))

        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            filename='burnextracter.log',
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('BurnsExtracter')
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create the agent
        self.agent = Agent(
            self.model,
            result_type=BurnsModel,
            system_prompt=self._get_extraction_system_prompt()
        )
    
    def _get_extraction_system_prompt(self) -> str:
        """
        Create a system prompt for the extraction agent.
        
        Returns:
            str: System prompt for the extraction agent
        """
        return """
        You are a medical data extraction specialist tasked with extracting burn injury information 
        from medical notes into a structured JSON format that exactly matches the BurnsModel schema.
        The medical notes are in european portuguese, and are in natural language.

        # IMPORTANT INSTRUCTIONS
        1. Extract ALL fields defined in the schema below
        2. Use EXACTLY the enum values specified for controlled fields
        3. Return null for numeric fields when information is unavailable
        4. Return empty lists for array fields when information is unavailable
        5. Use false as default for boolean fields unless explicitly mentioned
        6. Use "unspecified" for depth if not clearly stated
        7. Do NOT add any fields not defined in the schema
        8. The patient ID will be added separately - do not include it

        # SCHEMA STRUCTURE
        {
          "tbsa": float or null,  // Total Body Surface Area percentage (e.g., 13.0)
          "mechanism": string or null,  // MUST be one of: "Heat", "Electrical discharge", "Friction", "Chemicals", "Radiation", "unknown or unspecified"
          "type_of_accident": string or null,  // MUST be one of: "domestic", "workplace", "other"
          "agent": string or null,  // The specific agent causing the burn (e.g., "gas", "fire", "chemical name")
          "wildfire": boolean,  // Set true only if explicitly mentioned
          "bonfire": boolean,  // Set true only if explicitly mentioned
          "fireplace": boolean,  // Set true only if explicitly mentioned
          "violence": boolean,  // Set true only if explicitly mentioned
          "suicide_attempt": boolean,  // Set true only if explicitly mentioned
          "escharotomy": boolean,  // Set true only if explicitly mentioned
          "associated_trauma": [string] or null,  // List of associated trauma
          "burns": [  // Array of individual burn injuries
            {
              "location": string,  // MUST be one of: "head", "neck", "face", "upper extremity", "hand", "trunk", "thorax", "abdomen", "back of trunk", "perineum", "lower extremity", "foot"
              "laterality": string,  // MUST be one of: "left", "right", "bilateral", "unspecified"
              "depth": string,  // MUST be one of: "1st_degree", "2nd_degree_partial", "2nd_degree_full", "3rd_degree", "4th_degree", "unspecified"
              "circumferencial": boolean  // true if burn encircles the body part
            }
          ]
        }

        # EXTRACTION GUIDELINES
        - For TBSA: Extract the exact percentage mentioned (e.g., "ASQC ~ 13%" → 13.0)
        - For mechanism: Map descriptions to the closest enum value
        - For burn depth:
          * "2nd degree" without specifying → use "2nd_degree_partial"
          * "2nd degree deep/profundo" → use "2nd_degree_full"
        - For burn locations: Create separate entries in the burns array for each affected location
        - For associated trauma: Include any trauma mentioned (e.g., "TCE" → "head trauma")
        - For circumferential burns: Set to true if terms like "circular", "circumferential", or encircling descriptions are used

        Be precise and accurate. The extracted data MUST follow the exact structure and value constraints of the schema.
        """
    
    def _read_markdown_file(self, file_path: Path) -> str:
        """
        Read the content of a markdown file.
        
        Args:
            file_path (Path): Path to the markdown file
        
        Returns:
            str: Content of the markdown file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
    
    def extract_burns_data(self, filename: str) -> BurnsModel:
        """
        Extract burn information from a markdown file using Pydantic AI.
        
        Args:
            filename (str): Name of the markdown file (without path)
        
        Returns:
            tuple: (BurnsModel, str) Pydantic model containing the extracted burn information and file ID
        """
        file_id = filename.split('.')[0]
        file_path = self.input_dir / filename
        
        try:
            # Read the file content
            self.console.print(f"[blue]Reading file: {filename}[/blue]")
            text = self._read_markdown_file(file_path)
            
            # Set optimized model settings for extraction tasks
            model_settings = ModelSettings(
                temperature=0.1,  # Low temperature for more deterministic output
                timeout=120,      # Longer timeout for complex extraction
            )
            
            # Run the extraction
            self.console.print("[yellow]Extracting burn information...[/yellow]")
            result = self.agent.run_sync(
                f"Extract burn information from this medical text. The patient ID is {file_id}:\n\n{text}",
                model_settings=model_settings
            )
            
            # Get the extracted Burns Model
            burns_model = result.data        
            
            self.console.print("[green]Successfully extracted burn information[/green]")
            return burns_model, file_id
                
        except Exception as e:
            self.logger.error(f"Error extracting burns data: {e}")
            raise
    
    def save_json(self, burns_model: BurnsModel, file_id: str) -> Path:
        """
        Save the BurnsModel as JSON with added ID field.
        
        Args:
            burns_model (BurnsModel): Pydantic model to save
            file_id (str): ID to use in the filename and add to the JSON
            
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
            # Create a panel for the processing operation
            self.console.print(Panel(
                f"[bold cyan]Processing File: {filename}[/bold cyan]",
                border_style="cyan"
            ))
            
            # Step 1: Extract data
            self.console.print("\n[bold blue]Step 1:[/bold blue] Extracting burn information...")
            burns_model, file_id = self.extract_burns_data(filename)
            
            # Step 2: Display the extracted Pydantic model
            self.console.print("\n[bold blue]Step 2:[/bold blue] Extracted Pydantic Model:")
            model_dict = burns_model.model_dump(exclude_none=True)
            
            # Display the Pydantic model in a detailed format
            if model_dict.get("tbsa"):
                self.console.print(f"  [green]TBSA:[/green] {model_dict['tbsa']}%")
            if model_dict.get("mechanism"):
                self.console.print(f"  [green]Mechanism:[/green] {model_dict['mechanism']}")
            if model_dict.get("type_of_accident"):
                self.console.print(f"  [green]Type of Accident:[/green] {model_dict['type_of_accident']}")
            if model_dict.get("agent"):
                self.console.print(f"  [green]Agent:[/green] {model_dict['agent']}")
            
            # Display boolean fields that are True
            for field in ["wildfire", "bonfire", "fireplace", "violence", "suicide_attempt", "escharotomy"]:
                if model_dict.get(field) is True:
                    self.console.print(f"  [green]{field.capitalize()}:[/green] Yes")
            
            # Display associated trauma if any
            if model_dict.get("associated_trauma"):
                self.console.print("  [green]Associated Trauma:[/green]")
                for trauma in model_dict["associated_trauma"]:
                    self.console.print(f"    • {trauma}")
            
            # Display burn injuries if any
            if model_dict.get("burns"):
                self.console.print("  [green]Burn Injuries:[/green]")
                for i, burn in enumerate(model_dict["burns"], 1):
                    self.console.print(f"    • Injury #{i}:")
                    self.console.print(f"      - Location: {burn['location']}")
                    self.console.print(f"      - Laterality: {burn['laterality']}")
                    self.console.print(f"      - Depth: {burn['depth']}")
                    if burn.get("circumferencial") is True:
                        self.console.print(f"      - Circumferential: Yes")
            
            # Step 3: Add ID and display the JSON
            self.console.print("\n[bold blue]Step 3:[/bold blue] Creating JSON with ID...")
            data = burns_model.model_dump(exclude_none=True)
            data["ID"] = file_id
            
            # Format and display JSON
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            self.console.print_json(json_str)
            
            # Step 4: Save the JSON file
            self.console.print("\n[bold blue]Step 4:[/bold blue] Saving JSON file...")
            output_path = self.save_json(burns_model, file_id)
            
            self.console.print(Panel(
                f"[bold green]✓ Successfully processed {filename}[/bold green]\n\n"
                f"Output saved to: [blue]{output_path}[/blue]",
                border_style="green"
            ))
            
            return output_path
            
        except Exception as e:
            self.console.print(Panel(
                f"[bold red]Error processing file {filename}:[/bold red]\n\n{str(e)}",
                border_style="red"
            ))
            self.logger.error(f"Error processing file {filename}: {e}")
            raise


def main():
    """Main function to test the BurnsExtracter with a single file."""
    console = Console()
    
    # Create a nice header
    console.print(Panel(
        "[bold blue]Burns Data Extractor[/bold blue]", 
        subtitle="Extract burn information from medical notes using Pydantic AI",
        border_style="blue",
        expand=False
    ))
    
    # Get API key with error handling
    try:
        from core_tools.key_manager import KeyManager
        key_manager = KeyManager()
        api_key = key_manager.get_key('GEMINI_API_KEY')
        console.print("[green]✓ Successfully loaded API key from KeyManager[/green]")
    except (ImportError, AttributeError):
        console.print("[yellow]KeyManager not found, attempting to use environment variable[/yellow]")
        api_key = os.environ.get("GOOGLE_API_KEY")
        if api_key:
            console.print("[green]✓ Successfully loaded API key from environment[/green]")
    
    # If no API key found, ask the user
    if not api_key:
        api_key = Prompt.ask("[yellow]Please enter your Google API key[/yellow]", password=True)
        console.print("[green]✓ API key provided manually[/green]")
    
    # Define input and output directories
    input_dir = Path("/home/gusmmm/Desktop/infoburn/data/output/markdown/clean")
    output_dir = Path("/home/gusmmm/Desktop/infoburn/data/output/json/burns")
    
    console.print(f"[blue]Input directory:[/blue] {input_dir}")
    console.print(f"[blue]Output directory:[/blue] {output_dir}")
    
    # Create the BurnsExtracter instance
    console.print("[yellow]Initializing BurnsExtracter...[/yellow]")
    extracter = BurnsExtracter(api_key, input_dir, output_dir)
    console.print("[green]✓ BurnsExtracter initialized successfully[/green]")
    
    # Process a test file
    test_file = "2301.md"
    
    try:
        output_path = extracter.process_file(test_file)
        console.print("\n[bold green]✓ Processing complete![/bold green]")
    except Exception as e:
        console.print(f"\n[bold red]✗ Processing failed with error:[/bold red]")
        console.print(f"[red]{str(e)}[/red]")
        
    # Program completed
    console.print(Panel(
        "[bold blue]Process Completed[/bold blue]",
        border_style="blue",
        expand=False
    ))


if __name__ == "__main__":
    main()