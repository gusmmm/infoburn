import json
import time
import re
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from enum import Enum
from collections import defaultdict
import copy

# Pydantic and Google GenAI
from pydantic import BaseModel, Field, ValidationError
from google import genai
from google.genai import types
from google.api_core import exceptions as google_exceptions

# Environment and Rich UI
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.table import Table

# Local Imports
from pydantic_extracter.genai_client import GenAIClientManager
from pydantic_extracter.medical_history.medical_history_template import get_medical_history_prompt_template

# Import the SNOMED CT diagnosis lookup function
from core_tools.diagnosis import find_diagnosis_snomed_code

#local model imports
from pydantic_classifier.medical_history import SnomedConcept, DiseaseCategory, Disease, PreviousMedicalHistory

# --- Configuration ---
load_dotenv()
GEMINI_MODEL_NAME = "gemini-2.5-flash-preview-04-17"
DEFAULT_GEMINI_RATE_LIMIT_RPM = 10
DEFAULT_SNOMED_RATE_LIMIT_RPM = 30
GEMINI_TEMPERATURE = 0.1
GEMINI_RESPONSE_MIME_TYPE = 'application/json'
GEMINI_SYSTEM_INSTRUCTION = "You are a meticulous data scientist specializing in extracting structured medical information from clinical texts."
GEMINI_THINKING_BUDGET = 4096

# --- Prompt Template ---
EXTRACTION_PROMPT_TEMPLATE = get_medical_history_prompt_template()

class MedicalHistoryExtractorService:
    """
    Extracts previous medical history from markdown files using Google Gemini API
    and enriches it with SNOMED CT codes. Allows filtering files by ID range or year range.
    Uses GenAIClientManager for API access.
    """
    def __init__(self,
                input_dir: str,
                output_dir: str,
                glossary_path: str,
                gemini_rate_limit_rpm: int = DEFAULT_GEMINI_RATE_LIMIT_RPM,
                snomed_rate_limit_rpm: int = DEFAULT_SNOMED_RATE_LIMIT_RPM):
        """
        Initializes the MedicalHistoryExtractorService.
        Args:
            input_dir: Path to the directory containing input markdown files.
            output_dir: Path to the directory where output JSON files will be saved.
            glossary_path: Path to the glossary file (optional).
            gemini_rate_limit_rpm: Maximum requests per minute allowed for the Gemini API.
            snomed_rate_limit_rpm: Maximum requests per minute allowed for SNOMED lookups.
        """
        self.console = Console()
        self.client: Optional[genai.Client] = None  # Initialize client attribute

        try:
            # Use GenAIClientManager to get the client
            client_manager = GenAIClientManager(console=self.console)
            self.client = client_manager.get_client()  # This handles API key loading and client creation
        except ValueError as e:
            # Error during client initialization (e.g., missing API key) is fatal
            self.console.print(f"[bold red]Error initializing service: {e}[/bold red]")
            raise  # Stop execution if essential setup fails

        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.glossary_path = Path(glossary_path)
        self.glossary_content: Optional[str] = None  # Lazy loaded

        # Gemini Rate Limiting Setup
        self.gemini_rate_limit_rpm = gemini_rate_limit_rpm
        if self.gemini_rate_limit_rpm <= 0:
            self.console.print("[yellow]Warning: Gemini rate limit must be positive. Disabling Gemini rate limiting.[/yellow]")
            self.gemini_sleep_duration = 0
        else:
            self.gemini_sleep_duration = 60.0 / self.gemini_rate_limit_rpm
            self.console.print(f"[blue]Gemini rate limiting enabled: {self.gemini_rate_limit_rpm} RPM (delay: {self.gemini_sleep_duration:.2f} seconds between API calls).[/blue]")

        # SNOMED Rate Limiting Setup
        self.snomed_rate_limit_rpm = snomed_rate_limit_rpm
        if self.snomed_rate_limit_rpm <= 0:
            self.console.print("[yellow]Warning: SNOMED rate limit must be positive. Disabling SNOMED rate limiting.[/yellow]")
            self.snomed_sleep_duration = 0
        else:
            self.snomed_sleep_duration = 60.0 / self.snomed_rate_limit_rpm
            self.console.print(f"[blue]SNOMED rate limiting enabled: {self.snomed_rate_limit_rpm} RPM (delay: {self.snomed_sleep_duration:.2f} seconds between lookups).[/blue]")

        self._ensure_output_dir()
        self.console.print(f"Input directory: '{self.input_dir}'")
        self.console.print(f"Output directory: '{self.output_dir}'")
        self.console.print(f"Glossary path: '{self.glossary_path}'")
        self.console.print(f"Using Gemini Model: '{GEMINI_MODEL_NAME}'")

    def _ensure_output_dir(self):
        """Ensures the output directory exists, creating it if necessary."""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self.console.print(f"[bold red]Error creating output directory '{self.output_dir}': {e}[/bold red]")
            raise

    def _load_glossary(self) -> str:
        """Loads the glossary content from the specified file."""
        if self.glossary_content is None: # Load only once
            try:
                self.glossary_content = self.glossary_path.read_text(encoding='utf-8')
                self.console.print(f"[blue]Glossary loaded successfully from '{self.glossary_path}'.[/blue]")
            except FileNotFoundError:
                self.console.print(f"[bold red]Error: Glossary file not found at '{self.glossary_path}'. Proceeding without glossary.[/bold red]")
                self.glossary_content = "" # Set to empty string if not found
            except Exception as e:
                self.console.print(f"[bold red]Error reading glossary file '{self.glossary_path}': {e}. Proceeding without glossary.[/bold red]")
                self.glossary_content = ""
        return self.glossary_content

    def _get_markdown_files(self,
                            limit: Optional[int] = None,
                            file_id_range: Optional[Tuple[int, int]] = None,
                            year_range: Optional[Tuple[int, int]] = None
                           ) -> List[Path]:
        """
        Gets a list of markdown files from the input directory, applying optional filters.

        Args:
            limit: Maximum number of files to return (applied after other filters).
            file_id_range: A tuple (start_id, end_id) to filter files by numeric stem ID.
            year_range: A tuple (start_year, end_year) to filter files by year derived
                        from the first two digits of the stem (e.g., 23 for 2023).

        Returns:
            A sorted list of filtered markdown file paths.
        """
        if not self.input_dir.is_dir():
            self.console.print(f"[bold red]Error: Input directory '{self.input_dir}' not found or is not a directory.[/bold red]")
            return []

        # Get all markdown files initially
        all_files = sorted(list(self.input_dir.glob("*.md")))
        files_to_process = all_files # Start with all files
        filter_applied = False

        # --- Apply File ID Range Filter ---
        if file_id_range:
            filter_applied = True
            start_id, end_id = file_id_range
            self.console.print(f"[blue]Filtering by File ID range: {start_id} to {end_id}[/blue]")
            id_filtered_files = [] # Use a temporary list for this filter
            for file_path in all_files: # Filter from the original full list
                try:
                    file_id = int(file_path.stem)
                    if start_id <= file_id <= end_id:
                        id_filtered_files.append(file_path)
                except ValueError:
                    self.console.print(f"[yellow]Warning: Could not parse file ID from '{file_path.name}'. Skipping for ID range filter.[/yellow]")
            files_to_process = id_filtered_files # Update the list to process

        # --- Apply Year Range Filter ---
        # Only apply if ID range was NOT applied
        elif year_range:
            filter_applied = True
            start_year, end_year = year_range
            start_yy = start_year % 100
            end_yy = end_year % 100
            self.console.print(f"[blue]Filtering by Year range: {start_year} ({start_yy:02d}) to {end_year} ({end_yy:02d})[/blue]")
            year_pattern = re.compile(r"^\d{2}")
            year_filtered_files = [] # Use a temporary list for this filter
            for file_path in all_files: # Filter from the original full list
                match = year_pattern.match(file_path.stem)
                if match:
                    try:
                        file_yy = int(match.group(0))
                        if start_yy <= file_yy <= end_yy:
                            year_filtered_files.append(file_path)
                    except ValueError:
                         self.console.print(f"[yellow]Warning: Could not parse year from '{file_path.name}'. Skipping for year range filter.[/yellow]")
                else:
                    self.console.print(f"[yellow]Warning: Filename '{file_path.name}' does not start with two digits. Skipping for year range filter.[/yellow]")
            files_to_process = year_filtered_files # Update the list to process

        # --- Apply Limit ---
        # Apply limit to the result of filtering (or the full list if no filter applied)
        if limit is not None and limit > 0:
            if len(files_to_process) > limit:
                self.console.print(f"[yellow]Limiting processing to the first {limit} files (after applying filters).[/yellow]")
                return files_to_process[:limit]
            # Only print limit message if no range filter was active but limit is set
            elif not filter_applied:
                 self.console.print(f"[yellow]Processing limit set to {limit} files.[/yellow]")
                 # No need to slice if limit >= len(files_to_process)

        return files_to_process # Return the correctly filtered (and potentially limited) list

    def _read_file(self, file_path: Path) -> Optional[str]:
        """Reads content from a single markdown file."""
        try:
            return file_path.read_text(encoding='utf-8')
        except FileNotFoundError:
            self.console.print(f"[red]Error: File not found '{file_path}'. Skipping.[/red]")
            return None
        except Exception as e:
            self.console.print(f"[red]Error reading file '{file_path}': {e}. Skipping.[/red]")
            return None

    def _extract_history(self, medical_text: str) -> Optional[PreviousMedicalHistory]:
        """
        Extracts medical history from the medical text using the Gemini API via the managed client.

        Args:
            medical_text: The content of the medical case file.

        Returns:
            A PreviousMedicalHistory object containing the extracted data, or None if extraction fails.
        """
        if not self.client:
            self.console.print("[bold red]Error: Gemini client is not initialized. Cannot perform extraction.[/bold red]")
            return None

        glossary = self._load_glossary()
        
        # Format the enum values as a string
        category_enums = ", ".join([f'"{item.value}"' for item in DiseaseCategory])
        
        # Get the JSON schema
        schema_json = PreviousMedicalHistory.model_json_schema()
        
        # Remove irrelevant parts if needed to make it more focused
        if 'properties' in schema_json and 'ID' in schema_json['properties']:
            schema_json['properties'].pop('ID', None)  # Remove ID from schema if present
        
        # Format the template with all required values
        prompt = EXTRACTION_PROMPT_TEMPLATE.format(
            medical_text=medical_text,
            glossary=glossary if glossary else "No glossary provided.",
            category_enums=category_enums,
            schema_json=json.dumps(schema_json, indent=2)
        )

        try:
            # Configure generation settings using constants
            generation_config = {
                "temperature": GEMINI_TEMPERATURE,
                "response_mime_type": GEMINI_RESPONSE_MIME_TYPE,
            }

            self.console.print(f"[grey50]Sending request to Gemini...[/grey50]")
            response = self.client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt,
                config=generation_config,
            )

            # Attempt to parse the JSON response using the Pydantic model
            if response.text:
                try:
                    # Parse the JSON string from the response text
                    response_data = json.loads(response.text)
                    
                    # Handle case where Gemini returns a simple list of diseases
                    if isinstance(response_data, list):
                        self.console.print("[yellow]Received a simple list of diseases instead of proper JSON structure. Adapting format...[/yellow]")
                        # Convert the list to proper structure with required provenance field
                        formatted_data = {
                            "previous_diseases": [
                                {
                                    "name": disease_name, 
                                    "provenance": "Automatically extracted from text without specific provenance data"
                                } 
                                for disease_name in response_data if disease_name
                            ]
                        }
                        response_data = formatted_data
                    
                    # Validate the parsed data against the Pydantic model
                    validated_data = PreviousMedicalHistory.model_validate(response_data)
                    return validated_data
                    
                except json.JSONDecodeError as json_err:
                    self.console.print(f"[red]Error decoding JSON response: {json_err}[/red]")
                    self.console.print(f"Raw response text: {response.text[:500]}...") # Log part of the raw response
                    return None
                except ValidationError as val_err:
                    self.console.print(f"[red]Validation Error: Extracted data does not match schema: {val_err}[/red]")
                    # Try to show the problematic part if possible
                    try:
                        response_data_preview = json.loads(response.text)
                        self.console.print(f"Raw response data preview: {response_data_preview}")
                    except Exception:
                        self.console.print(f"Raw response text preview: {response.text[:500]}...")
                    return None
            else:
                 self.console.print("[yellow]Warning: Received empty response from API.[/yellow]")
                 # Return an empty structure instead of None if appropriate
                 return PreviousMedicalHistory(previous_diseases=[])

        except google_exceptions.GoogleAPIError as api_err:
            self.console.print(f"[bold red]Google API Error during extraction: {api_err}[/bold red]")
            # Specific handling for common errors like QuotaExceeded, InvalidArgument etc. can be added here
            if isinstance(api_err, google_exceptions.ResourceExhausted):
                 self.console.print("[bold yellow]Quota possibly exceeded. Consider adding delays or requesting quota increase.[/bold yellow]")
            return None
        except Exception as e:
            self.console.print(f"[bold red]An unexpected error occurred during extraction: {e}[/bold red]")
            return None


    def _enrich_diseases_with_snomed(self, diseases: List[Disease]) -> List[Disease]:
        """
        Enriches a list of Disease objects with SNOMED CT codes using find_diagnosis_snomed_code.
        Applies rate limiting between SNOMED lookup calls.
        """
        if not diseases:
            return []

        self.console.print(f"[cyan]Enriching {len(diseases)} diseases with SNOMED CT codes...[/cyan]")
        enriched_diseases = []
        num_diseases = len(diseases)
        for idx, disease in enumerate(diseases): # Use enumerate for rate limiting logic
            disease_name = disease.name
            if not disease_name:
                self.console.print("[yellow]Skipping disease with missing name during SNOMED enrichment.[/yellow]")
                enriched_diseases.append(disease)
                continue

            snomed_result = None
            try:
                snomed_result = find_diagnosis_snomed_code(disease_name)
            except Exception as e:
                self.console.print(f"[red]Error during SNOMED lookup for '{disease_name}': {e}[/red]")

            if snomed_result:
                try:
                    snomed_concept = SnomedConcept.model_validate(snomed_result)
                    disease.snomed_classification = snomed_concept
                except ValidationError as val_err:
                    self.console.print(f"[yellow]Warning: SNOMED result for '{disease_name}' failed validation: {val_err}. Result: {snomed_result}[/yellow]")
                    disease.snomed_classification = None
            else:
                disease.snomed_classification = None

            enriched_diseases.append(disease)

            # --- SNOMED Rate Limiting Delay ---
            # Apply delay after each lookup, except the last one in the list for this file
            if self.snomed_sleep_duration > 0 and idx < num_diseases - 1:
                # self.console.print(f"[dim]Waiting {self.snomed_sleep_duration:.2f}s before next SNOMED lookup...[/dim]") # Optional verbose log
                time.sleep(self.snomed_sleep_duration)
            # ---------------------------------

        return enriched_diseases

    def _save_json(self, data: PreviousMedicalHistory, input_file_path: Path):
        """Saves the extracted data, including the file-derived ID, to a JSON file."""
        output_filename = input_file_path.stem + ".json"
        output_path = self.output_dir / output_filename

        file_id = input_file_path.stem

        try:
            # Use model_dump for Pydantic v2, exclude None values for cleaner output
            data_dict = data.model_dump(exclude_none=True, mode='json')
            data_dict['ID'] = file_id # Ensure ID is set correctly

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=4, ensure_ascii=False)

        except IOError as e:
            self.console.print(f"[red]Error saving JSON file '{output_path}': {e}[/red]")
        except Exception as e:
            self.console.print(f"[red]Unexpected error saving JSON '{output_path}': {e}[/red]")


    def process_files(self,
                      limit: Optional[int] = None,
                      file_id_range: Optional[Tuple[int, int]] = None,
                      year_range: Optional[Tuple[int, int]] = None):
        """
        Processes markdown files based on specified filters: extracts history,
        enriches with SNOMED, saves JSON.

        Args:
            limit: Maximum number of files to process.
            file_id_range: A tuple (start_id, end_id) to filter files by numeric stem ID.
            year_range: A tuple (start_year, end_year) to filter files by year derived
                        from the first two digits of the stem.
        """
        markdown_files = self._get_markdown_files(limit=limit, file_id_range=file_id_range, year_range=year_range)
        if not markdown_files:
            self.console.print("[yellow]No markdown files found matching the specified criteria.[/yellow]")
            return

        self.console.print(f"Found {len(markdown_files)} markdown files to process.")

        progress = Progress(
            TextColumn("[progress.description]{task.description}"), BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"), TimeRemainingColumn(),
        )

        with progress:
            task = progress.add_task("[cyan]Processing files...", total=len(markdown_files))
            success_count = 0
            fail_count = 0

            for i, file_path in enumerate(markdown_files): # Use enumerate for Gemini rate limiting
                progress.update(task, description=f"[cyan]Processing: {file_path.name}")

                medical_text = self._read_file(file_path)
                if medical_text is None:
                    fail_count += 1; progress.advance(task); continue

                # Step 1: Initial Extraction (Gemini API Call)
                extracted_data = self._extract_history(medical_text)
                if extracted_data is None:
                    self.console.print(f"[yellow]Failed initial extraction for '{file_path.name}'. Skipping.[/yellow]")
                    fail_count += 1; progress.advance(task); continue

                # Step 2: Enrichment (SNOMED API Calls - rate limited internally)
                if extracted_data.previous_diseases:
                    extracted_data.previous_diseases = self._enrich_diseases_with_snomed(extracted_data.previous_diseases)
                else:
                     self.console.print(f"[cyan]No previous diseases found/extracted for '{file_path.name}'. Skipping enrichment.[/cyan]")

                # Step 3: Save
                self._save_json(extracted_data, file_path)
                success_count += 1
                progress.advance(task)

                # --- Gemini Rate Limiting Delay ---
                if self.gemini_sleep_duration > 0 and i < len(markdown_files) - 1:
                    time.sleep(self.gemini_sleep_duration)
                # ---------------------------------

        self.console.print("-" * 30)
        self.console.print(f"[bold green]Processing complete.[/bold green]")
        self.console.print(f"Successfully processed and saved: {success_count}")
        self.console.print(f"Failed/Skipped: {fail_count}")
        self.console.print("-" * 30)


# --- Main Execution & Test ---
if __name__ == "__main__":
    console = Console()
    console.print("[bold blue]Medical History Extractor[/bold blue]")

    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    INPUT_DIR = PROJECT_ROOT / "data" / "output" / "markdown" / "clean"
    OUTPUT_DIR = PROJECT_ROOT / "data" / "output" / "json" / "medical_history"
    GLOSSARY_PATH = PROJECT_ROOT / "documentation" / "PT-glossario.md"

    # --- User Interaction for Filtering ---
    console.print("\n[bold yellow]Select Processing Mode:[/bold yellow]")
    console.print("1. Process All Files")
    console.print("2. Process by File ID Range (e.g., 2301 to 2315)")
    console.print("3. Process by Year Range (e.g., 2023 to 2024)")
    console.print("4. Process First N Files (Limit)")

    mode = IntPrompt.ask("Enter choice (1-4)", choices=["1", "2", "3", "4"], default=1)

    limit: Optional[int] = None
    file_id_range: Optional[Tuple[int, int]] = None
    year_range: Optional[Tuple[int, int]] = None

    if mode == 2:
        while True:
            start_id = IntPrompt.ask("Enter start File ID")
            end_id = IntPrompt.ask("Enter end File ID")
            if start_id <= end_id:
                file_id_range = (start_id, end_id)
                break
            else:
                console.print("[red]Error: Start ID must be less than or equal to End ID.[/red]")
    elif mode == 3:
         while True:
            start_year = IntPrompt.ask("Enter start Year (e.g., 2023)")
            end_year = IntPrompt.ask("Enter end Year (e.g., 2024)")
            if 2000 <= start_year <= 2099 and 2000 <= end_year <= 2099: # Basic year validation
                if start_year <= end_year:
                    year_range = (start_year, end_year)
                    break
                else:
                    console.print("[red]Error: Start Year must be less than or equal to End Year.[/red]")
            else:
                console.print("[red]Error: Please enter valid 4-digit years (e.g., 2023).[/red]")
    elif mode == 4:
        limit = IntPrompt.ask("Enter the maximum number of files to process", default=10)
        if limit <= 0:
            console.print("[yellow]Limit must be positive. Processing all files instead.[/yellow]")
            limit = None # Reset to process all if invalid limit given

    # --- Initialize and Run Service ---
    try:
        console.print("\n[bold yellow]Initializing Extractor Service...[/bold yellow]")
        extractor_service = MedicalHistoryExtractorService(
            input_dir=str(INPUT_DIR),
            output_dir=str(OUTPUT_DIR),
            glossary_path=str(GLOSSARY_PATH),
            gemini_rate_limit_rpm=DEFAULT_GEMINI_RATE_LIMIT_RPM,
            snomed_rate_limit_rpm=DEFAULT_SNOMED_RATE_LIMIT_RPM
        )

        console.print("\n[bold green]Starting Processing Run...[/bold green]")
        extractor_service.process_files(
            limit=limit,
            file_id_range=file_id_range,
            year_range=year_range
        )

    except ValueError as e:
        console.print(f"[bold red]Initialization failed: {e}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred during execution: {e}[/bold red]")
