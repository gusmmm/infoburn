import os
import json
import time
import re
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import copy # Needed for deep copying if complex consolidation were added
from enum import Enum # Required for defining Enum types

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
from rich.panel import Panel

# --- Configuration ---
load_dotenv()
# Use the same model as other extractors for consistency
GEMINI_MODEL_NAME = "gemini-2.5-flash-preview-04-17"
DEFAULT_GEMINI_RATE_LIMIT_RPM = 10 # Requests per minute for Gemini API

# --- Pydantic Models ---
# Import the strict models defined in case.py (no defaults)
try:
    from pydantic_classifier.case import (
        ClinicalCaseExtract, AdmissionStatus, OrganicDysfunction,
        Procedure, Infection, OrganSystem
    )
    # Make sure all necessary nested models and enums are imported
except ImportError:
    print("Error: Could not import Pydantic models from pydantic_classifier.case.")
    print("Please ensure the file exists and is in the correct path relative to the project root.")
    # Define dummy models to allow script structure review, but it won't work functionally.
    class BaseModel: pass
    class OrganSystem(str, Enum): UNKNOWN = "Unknown"
    class OrganicDysfunction(BaseModel): pass
    class AdmissionStatus(BaseModel): pass
    class Procedure(BaseModel): pass
    class Infection(BaseModel): pass
    class ClinicalCaseExtract(BaseModel): pass
    # Add dummy enums/classes for any other types used if needed for static analysis

# --- Service Class ---

class CaseExtractorService:
    """
    Extracts general clinical case information (admission status, procedures,
    infections, other features) from markdown clinical case files using
    Google Gemini API, and saves structured data as JSON.
    Allows filtering files by ID range or year range.
    """
    def __init__(self,
                 input_dir: str,
                 output_dir: str,
                 gemini_rate_limit_rpm: int = DEFAULT_GEMINI_RATE_LIMIT_RPM):
        """
        Initializes the CaseExtractorService.

        Args:
            input_dir: Path to the directory containing input markdown files.
            output_dir: Path to the directory where output JSON files will be saved.
            gemini_rate_limit_rpm: Maximum requests per minute allowed for the Gemini API.
        """
        self.console = Console()
        try:
            self.api_key = self._load_api_key()
            self.client = self._initialize_client()
        except ValueError as e:
            self.console.print(f"[bold red]Error initializing service: {e}[/bold red]")
            raise # Re-raise to stop execution if initialization fails

        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)

        # Gemini Rate Limiting Setup
        self.gemini_rate_limit_rpm = gemini_rate_limit_rpm
        if self.gemini_rate_limit_rpm <= 0:
            self.console.print("[yellow]Warning: Gemini rate limit must be positive. Disabling Gemini rate limiting.[/yellow]")
            self.gemini_sleep_duration = 0
        else:
            self.gemini_sleep_duration = 60.0 / self.gemini_rate_limit_rpm
            self.console.print(f"[blue]Gemini rate limiting enabled: {self.gemini_rate_limit_rpm} RPM (delay: {self.gemini_sleep_duration:.2f} seconds between API calls).[/blue]")

        self._ensure_output_dir()
        self.console.print(f"Input directory: '{self.input_dir}'")
        self.console.print(f"Output directory: '{self.output_dir}'")

    def _load_api_key(self) -> str:
        """
        Loads the Gemini API key from the GEMINI_API_KEY environment variable.

        Returns:
            The API key string.

        Raises:
            ValueError: If the environment variable is not found.
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not found.")
        self.console.print("[green]✓ Gemini API key loaded.[/green]")
        return api_key

    def _initialize_client(self) -> genai.Client:
        """
        Initializes the Google Gemini API client using the loaded API key.

        Returns:
            An initialized genai.Client instance.

        Raises:
            ValueError: If client initialization fails.
        """
        try:
            # Configure the client directly with the API key
            client = genai.Client(api_key=self.api_key)
            # Remove the redundant client creation
            # client = genai.Client() # This line is no longer needed
            # Optional: Test connection with a simple listing or model check
            # client.models.list() # Uncomment to verify connection during init
            self.console.print("[green]✓ Gemini client initialized successfully.[/green]")
            return client
        except Exception as e:
            # Catch a broad exception during initialization
            raise ValueError(f"Failed to initialize Gemini client: {e}")

    def _ensure_output_dir(self):
        """
        Ensures the output directory exists. Creates it if it doesn't.

        Raises:
            OSError: If the directory cannot be created.
        """
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.console.print(f"[green]✓ Output directory ensured: '{self.output_dir}'[/green]")
        except OSError as e:
            self.console.print(f"[bold red]Error creating output directory '{self.output_dir}': {e}[/bold red]")
            raise # Re-raise to stop execution

    def _get_markdown_files(self,
                            limit: Optional[int] = None,
                            file_id_range: Optional[Tuple[int, int]] = None,
                            year_range: Optional[Tuple[int, int]] = None
                           ) -> List[Path]:
        """
        Retrieves and filters markdown files from the input directory.

        Applies filtering based on file ID range or year range (derived from the
        first two digits of the filename stem, e.g., '23' for 2023).
        Optionally limits the number of files returned.

        Args:
            limit: Maximum number of files to return.
            file_id_range: Tuple (start_id, end_id) to filter by filename stem integer ID.
            year_range: Tuple (start_year, end_year) to filter by year derived from filename.

        Returns:
            A sorted list of Path objects for the markdown files to be processed.
            Returns an empty list if the input directory is invalid or no files match.
        """
        if not self.input_dir.is_dir():
            self.console.print(f"[bold red]Error: Input directory '{self.input_dir}' not found or is not a directory.[/bold red]")
            return []

        all_files = sorted(list(self.input_dir.glob("*.md")))
        if not all_files:
            self.console.print(f"[yellow]No markdown files found in '{self.input_dir}'.[/yellow]")
            return []

        files_to_process = all_files # Start with all files
        filter_applied = False

        # --- Apply File ID Range Filter ---
        if file_id_range:
            filter_applied = True
            start_id, end_id = file_id_range
            self.console.print(f"[blue]Filtering by File ID range: {start_id} to {end_id}[/blue]")
            id_filtered_files = []
            for file_path in all_files:
                try:
                    file_id = int(file_path.stem)
                    if start_id <= file_id <= end_id:
                        id_filtered_files.append(file_path)
                except ValueError:
                    self.console.print(f"[yellow]Warning: Could not parse file ID from '{file_path.name}'. Skipping for ID range filter.[/yellow]")
            files_to_process = id_filtered_files
            self.console.print(f"Found {len(files_to_process)} files matching ID range.")

        # --- Apply Year Range Filter ---
        # Only apply if ID range was NOT applied
        elif year_range:
            filter_applied = True
            start_year, end_year = year_range
            # Assuming year is the first two digits of the stem (e.g., 23 -> 2023)
            start_yy = start_year % 100
            end_yy = end_year % 100
            self.console.print(f"[blue]Filtering by Year range: {start_year} ({start_yy:02d}) to {end_year} ({end_yy:02d})[/blue]")
            year_pattern = re.compile(r"^\d{2}") # Matches first two digits
            year_filtered_files = []
            for file_path in all_files:
                match = year_pattern.match(file_path.stem)
                if match:
                    try:
                        # Extract the 2-digit year and compare
                        file_yy = int(match.group(0))
                        if start_yy <= file_yy <= end_yy:
                            year_filtered_files.append(file_path)
                    except ValueError:
                         self.console.print(f"[yellow]Warning: Could not parse year from '{file_path.name}'. Skipping for year range filter.[/yellow]")
                else:
                    self.console.print(f"[yellow]Warning: Filename '{file_path.name}' does not start with two digits. Skipping for year range filter.[/yellow]")
            files_to_process = year_filtered_files
            self.console.print(f"Found {len(files_to_process)} files matching year range.")

        # --- Apply Limit ---
        # Apply limit *after* filtering
        if limit is not None and limit > 0:
            if len(files_to_process) > limit:
                self.console.print(f"[yellow]Limiting processing to the first {limit} files (after applying filters).[/yellow]")
                files_to_process = files_to_process[:limit]
            # Only print limit message if no range filter was active but limit is set
            elif not filter_applied:
                 self.console.print(f"[yellow]Processing limit set to {limit} files.[/yellow]")

        if not files_to_process and filter_applied:
             self.console.print("[yellow]No files matched the specified filter criteria.[/yellow]")

        return files_to_process

    def _read_file(self, file_path: Path) -> Optional[str]:
        """
        Reads the content of a single markdown file.

        Args:
            file_path: The Path object of the file to read.

        Returns:
            The content of the file as a string, or None if reading fails.
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            # self.console.print(f"[grey50]Read file: {file_path.name}[/grey50]") # Optional verbose log
            return content
        except FileNotFoundError:
            self.console.print(f"[red]Error: File not found '{file_path}'. Skipping.[/red]")
            return None
        except Exception as e:
            self.console.print(f"[red]Error reading file '{file_path}': {e}. Skipping.[/red]")
            return None

    def _create_prompt(self, medical_text: str, file_id: str) -> str:
        """
        Creates a detailed prompt for the Gemini AI to extract clinical case
        information based on the ClinicalCaseExtract Pydantic schema.

        Args:
            medical_text: The clinical case text read from the markdown file.
            file_id: The identifier derived from the filename (e.g., '2301').

        Returns:
            A formatted prompt string.
        """
        # Construct the prompt using an f-string for clarity
        prompt = f"""You are a specialized medical data extraction AI assistant. Your task is to meticulously analyze the following clinical case text, written in European Portuguese, and extract specific clinical information related to the patient's hospital stay, focusing on admission status, procedures, infections, and other relevant features.

        **Source Text:**
        --- START TEXT ---
        {medical_text}
        --- END TEXT ---

        **Extraction Task:**
        Extract the required information and structure it precisely according to the provided JSON schema. Adhere strictly to the schema's field names, types, and enum values. Translate relevant medical terms to English where appropriate for standardization (e.g., procedure names, dysfunction descriptions).

        **Key Information to Extract (Mandatory Fields):**
        1.  `admission_status`: Information about the patient's state upon admission.
            *   `organic_dysfunctions`: A list of organ dysfunctions present at admission. For each dysfunction:
                *   `system`: The affected organ system (use enum: {', '.join(f'"{s.value}"' for s in OrganSystem)}).
                *   `dysfunction_description`: Specific description (e.g., 'Acute Respiratory Distress Syndrome', 'Septic Shock').
                *   `support_provided`: List of supports (e.g., ['Mechanical Ventilation', 'Norepinephrine']). Use an empty list `[]` if none mentioned for a specific dysfunction.
                *   `provenance`: Quote the exact text supporting the dysfunction finding.
            *   `mechanical_ventilation`: Boolean (`true`/`false`) indicating if the patient was on invasive mechanical ventilation at admission.
            *   `provenance`: Quote the exact text supporting the overall admission status information.
        2.  `procedures`: A list of significant medical or surgical procedures performed during the *entire* hospital stay documented in the text. For each procedure:
            *   `name`: Name of the procedure (e.g., 'Central Venous Catheter Insertion', 'Skin Grafting', 'Bronchoscopy').
            *   `details`: Relevant details (e.g., 'Right subclavian vein', 'Split-thickness graft to left arm'). Use an empty string `""` if no details.
            *   `provenance`: Quote the exact text supporting the procedure finding.
        3.  `infections`: A list of infections identified during the hospital stay. For each infection:
            *   `site`: Site of infection (e.g., 'Bloodstream', 'Lungs', 'Wound').
            *   `pathogen`: Identified pathogen(s) (e.g., 'Pseudomonas aeruginosa', 'MRSA'). Use an empty string `""` if not specified.
            *   `details`: Additional details (e.g., 'Day 5', 'Resistant to Ciprofloxacin'). Use an empty string `""` if no details.
            *   `provenance`: Quote the exact text supporting the infection finding.
        4.  `other_relevant_features`: A list of strings describing other notable clinical features, events, or complications mentioned (e.g., "History of COPD", "Developed AKI on day 7", "Cardiac arrest event").
        5.  `provenance`: Quote the exact text snippet(s) that provide a general summary or overview of the case, if available. Otherwise, use an empty string `""`.

        **Output Requirements:**
        - Return **only** a single, valid JSON object matching the schema below. Do not include any explanatory text before or after the JSON.
        - **Crucially, all fields defined in the schema MUST be present in the output.**
        - If information for a specific field is not found in the text:
            - Use an empty list `[]` for list fields (e.g., `organic_dysfunctions`, `procedures`, `infections`, `other_relevant_features`, `support_provided`).
            - Use `false` for boolean fields (e.g., `mechanical_ventilation`).
            - Use an empty string `""` for string fields (e.g., `dysfunction_description`, `provenance`, `name`, `details`, `site`, `pathogen`) where applicable if no information is found.
            - Use the appropriate enum value like `OrganSystem.UNKNOWN` if the system cannot be determined.
        - Do not guess or infer information not present. Base the extraction solely on the provided text.
        - Ensure all JSON structures (objects `{{}}`, arrays `[]`) are correctly formed and closed.
        - The patient identifier for this case is `{file_id}`. This ID should *not* be included in the JSON output itself, as it will be added later during saving.
        - For all `provenance` fields, include the exact text snippets (direct quotes) from the source text. If multiple snippets support a finding, concatenate them or choose the most representative one. Use an empty string `""` if no specific text supports a required field.

        **JSON Schema Reference (Strict: All fields required):**
        ```json
        {json.dumps(ClinicalCaseExtract.model_json_schema(), indent=2)}
        ```

        Now, analyze the text and provide the structured JSON output, ensuring every field from the schema is included.
        """
        return prompt

    def _extract_case_data(self, medical_text: str, file_id: str) -> Optional[ClinicalCaseExtract]:
        """
        Extracts clinical case information from the medical text using the Gemini API
        and validates it against the ClinicalCaseExtract Pydantic model.

        Args:
            medical_text: The content of the medical case file.
            file_id: The identifier derived from the filename.

        Returns:
            A ClinicalCaseExtract object containing the extracted data, or None if
            extraction or validation fails.
        """
        prompt = self._create_prompt(medical_text, file_id)

        try:
            # Configure generation settings, requesting JSON output based on the schema
            generation_config = types.GenerateContentConfig(
                # system_instruction="You are a meticulous data scientist specializing in extracting structured medical information.", # Optional: System instruction
                temperature=0.1, # Low temperature for more deterministic output
                response_mime_type='application/json',
                response_schema=ClinicalCaseExtract.model_json_schema(),
                thinking_config=genai.types.ThinkingConfig(
                        thinking_budget=4096
                    ),
                # thinking_config=genai.types.ThinkingConfig(thinking_budget=4096), # Optional: If complex reasoning needed
            )

            # Define safety settings (optional, adjust as needed)
            # safety_settings = {
            #     types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: types.SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            #     types.HarmCategory.HARM_CATEGORY_HARASSMENT: types.SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            #     types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: types.SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            #     types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: types.SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            # }

            self.console.print(f"[grey50]Sending request to Gemini for file ID: {file_id}...[/grey50]")
            response = self.client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt,
                config=generation_config,
                #safety_settings=safety_settings # Apply safety settings
            )

            # --- Process Response ---
            # Check for valid response structure
            if not response.candidates or not response.candidates[0].content.parts:
                 self.console.print(f"[yellow]Warning: Received no valid content parts from API for file ID {file_id}.[/yellow]")
                 # Check for prompt feedback (e.g., blocked due to safety)
                 if response.prompt_feedback:
                     self.console.print(f"[yellow]Prompt Feedback: {response.prompt_feedback}[/yellow]")
                 # Check finish reason if available
                 finish_reason = getattr(response.candidates[0], 'finish_reason', None)
                 if finish_reason != types.FinishReason.STOP:
                      self.console.print(f"[yellow]Finish Reason: {finish_reason}[/yellow]")
                 return None

            # Extract the text part containing the JSON
            response_text = response.candidates[0].content.parts[0].text
            self.console.print(f"[grey50]Received response from Gemini for file ID: {file_id}. Validating...[/grey50]")

            if response_text:
                try:
                    # Parse the JSON string from the response text
                    response_data = json.loads(response_text)
                    # Validate the parsed data against the Pydantic model (Strict)
                    validated_data = ClinicalCaseExtract.model_validate(response_data)
                    self.console.print(f"[green]✓ Successfully extracted and validated data for file ID: {file_id}[/green]")
                    return validated_data
                except json.JSONDecodeError as json_err:
                    self.console.print(f"[bold red]Error decoding JSON response for file ID {file_id}: {json_err}[/bold red]")
                    self.console.print(f"Raw response text (first 500 chars): {response_text[:500]}...")
                    return None
                except ValidationError as val_err:
                    self.console.print(f"[bold red]Validation Error for file ID {file_id}: Extracted data does not match schema.[/bold red]")
                    self.console.print(f"[red]{val_err}[/red]")
                    # Log the raw data that failed validation for debugging
                    try:
                        response_data_preview = json.loads(response_text)
                        self.console.print(f"Raw response data preview: {response_data_preview}")
                    except Exception:
                        self.console.print(f"Raw response text preview (first 500 chars): {response_text[:500]}...")
                    return None
            else:
                 self.console.print(f"[yellow]Warning: Received empty response text from API for file ID {file_id}.[/yellow]")
                 return None # Cannot create a valid model from empty text

        except google_exceptions.GoogleAPIError as api_err:
            self.console.print(f"[bold red]Google API Error during extraction for file ID {file_id}: {api_err}[/bold red]")
            if isinstance(api_err, google_exceptions.ResourceExhausted):
                 self.console.print("[bold yellow]Quota possibly exceeded. Consider increasing delay or checking quota limits.[/bold yellow]")
            # Add more specific API error handling if needed (e.g., InvalidArgument)
            return None
        except Exception as e:
            # Catch any other unexpected errors during the API call or processing
            self.console.print(f"[bold red]An unexpected error occurred during extraction for file ID {file_id}: {e}[/bold red]")
            import traceback
            self.console.print(f"[grey50]{traceback.format_exc()}[/grey50]") # Log traceback for debugging
            return None

    def _save_json(self, data: ClinicalCaseExtract, input_file_path: Path):
        """
        Saves the extracted and validated ClinicalCaseExtract data to a JSON file.
        The patient ID is derived from the input file stem and added to the output JSON.

        Args:
            data: The ClinicalCaseExtract object containing the extracted data.
            input_file_path: The Path object of the original input markdown file.
        """
        output_filename = input_file_path.stem + ".json"
        output_path = self.output_dir / output_filename
        file_id = input_file_path.stem  # Get ID from filename

        # Ensure the data object is not None before proceeding
        if data is None:
            # This check might be redundant if _extract_case_data handles None returns properly,
            # but it adds an extra layer of safety.
            self.console.print(f"[red]Error: Cannot save None data for input file '{input_file_path.name}'.[/red]")
            return

        try:
            # Convert the ClinicalCaseExtract model to a dictionary
            # Use mode='json' to ensure Enums are serialized as their values
            data_dict = data.model_dump(mode='json')

            # Add the ID field to the dictionary (this ID is NOT part of the Pydantic model)
            data_dict["ID"] = file_id

            # Write the dictionary to a JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=4, ensure_ascii=False)
            # self.console.print(f"[green]Successfully saved extracted data to '{output_path}'[/green]") # Optional success log per file

        except IOError as e:
            self.console.print(f"[red]Error saving JSON file '{output_path}': {e}[/red]")
        except Exception as e:
            # Catch potential errors during model_dump or file writing
            self.console.print(f"[red]Unexpected error saving JSON for file ID {file_id} to '{output_path}': {e}[/red]")
            import traceback
            self.console.print(f"[grey50]{traceback.format_exc()}[/grey50]")

    def process_files(self,
                  limit: Optional[int] = None,
                  file_id_range: Optional[Tuple[int, int]] = None,
                  year_range: Optional[Tuple[int, int]] = None):
        """
        Processes markdown files based on specified filters: extracts clinical case info,
        and saves results as JSON files.

        Args:
            limit: Maximum number of files to process.
            file_id_range: A tuple (start_id, end_id) to filter files by numeric stem ID.
            year_range: A tuple (start_year, end_year) to filter files by year derived
                        from the first two digits of the stem.
        """
        markdown_files = self._get_markdown_files(limit=limit, file_id_range=file_id_range, year_range=year_range)
        if not markdown_files:
            # _get_markdown_files already prints messages if no files are found or match filters
            self.console.print("[yellow]Exiting processing run.[/yellow]")
            return

        self.console.print(f"Found {len(markdown_files)} markdown files to process.")

        # Setup progress bar
        progress = Progress(
            TextColumn("[progress.description]{task.description}"), BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"), TimeRemainingColumn(),
            console=self.console # Ensure progress bar uses the same console
        )

        success_count = 0
        fail_count = 0

        with progress:
            task_id = progress.add_task("[cyan]Processing files...", total=len(markdown_files))

            for i, file_path in enumerate(markdown_files):
                progress.update(task_id, description=f"[cyan]Processing: {file_path.name}")
                file_id = file_path.stem # Get file ID early for logging

                # --- Read File ---
                medical_text = self._read_file(file_path)
                if medical_text is None:
                    fail_count += 1
                    progress.advance(task_id)
                    # Apply rate limiting delay even if file read fails, to maintain overall rate
                    if self.gemini_sleep_duration > 0 and i < len(markdown_files) - 1:
                         time.sleep(self.gemini_sleep_duration)
                    continue # Skip to next file

                # --- Extract Data ---
                extracted_data = self._extract_case_data(medical_text, file_id)

                if extracted_data is None:
                    self.console.print(f"[yellow]Extraction failed for '{file_path.name}'. Skipping saving.[/yellow]")
                    fail_count += 1
                    # No data to save, advance progress
                    progress.advance(task_id)
                     # Apply rate limiting delay *after* the API call attempt (success or fail)
                    if self.gemini_sleep_duration > 0 and i < len(markdown_files) - 1:
                         time.sleep(self.gemini_sleep_duration)
                    continue # Skip to next file

                # --- Save Data ---
                # No consolidation step needed for this extractor based on current requirements
                self._save_json(extracted_data, file_path)
                success_count += 1
                progress.advance(task_id)

                # --- Gemini Rate Limiting Delay ---
                # Apply delay *after* processing each file (API call + saving)
                # except for the very last file.
                if self.gemini_sleep_duration > 0 and i < len(markdown_files) - 1:
                    # self.console.print(f"[dim]Waiting {self.gemini_sleep_duration:.2f}s before next API call...[/dim]") # Optional verbose log
                    time.sleep(self.gemini_sleep_duration)
                # ---------------------------------

        # --- Final Summary ---
        self.console.print("\n" + "="*30)
        summary_table = Table(title="Processing Summary", show_header=True, header_style="bold magenta")
        summary_table.add_column("Status", style="dim", width=25)
        summary_table.add_column("Count", justify="right")

        summary_table.add_row("Total Files Found", str(len(markdown_files)))
        summary_table.add_row("[green]Successfully Processed", str(success_count))
        summary_table.add_row("[red]Failed/Skipped", str(fail_count))

        self.console.print(summary_table)
        self.console.print("[bold green]Processing complete.[/bold green]\n" + "="*30)


# --- Main Execution & User Interface ---
if __name__ == "__main__":
    console = Console()
    console.print(Panel(
        "[bold blue]🏥 Clinical Case Extractor Service 🏥[/bold blue]",
        subtitle="Extracts admission status, procedures, infections, etc.",
        border_style="blue",
        expand=False
    ))

    # Determine project root relative to this script file
    try:
        # Assumes script is in 'pydantic_extracter' subdirectory of the project root
        PROJECT_ROOT = Path(__file__).resolve().parent.parent
    except IndexError:
        console.print("[bold red]Error: Could not determine project root. Place script appropriately.[/bold red]")
        exit(1) # Exit if project structure is unexpected

    # Define standard input/output directories relative to project root
    INPUT_DIR = PROJECT_ROOT / "data" / "output" / "markdown" / "clean"
    OUTPUT_DIR = PROJECT_ROOT / "data" / "output" / "json" / "case" # Specific output for this extractor

    # --- User Interaction for Filtering ---
    console.print("\n[bold yellow]Select Processing Mode:[/bold yellow]")
    console.print("1. Process All Files")
    console.print("2. Process by File ID Range (e.g., 2301 to 2315)")
    console.print("3. Process by Year Range (e.g., 2023 to 2024)")
    console.print("4. Process First N Files (Limit)")

    # Use IntPrompt for clear choices
    mode = IntPrompt.ask(
        "Enter choice",
        choices=["1", "2", "3", "4"],
        default=1,
        show_choices=False # Choices are printed above
    )

    limit: Optional[int] = None
    file_id_range: Optional[Tuple[int, int]] = None
    year_range: Optional[Tuple[int, int]] = None

    # Get specific filter parameters based on mode
    if mode == 2:
        console.print("[cyan]Enter File ID Range (numeric part of filename):[/cyan]")
        while True:
            start_id = IntPrompt.ask("  Start File ID (e.g., 2301)")
            end_id = IntPrompt.ask("  End File ID (e.g., 2315)")
            if start_id <= end_id:
                file_id_range = (start_id, end_id)
                break
            else:
                console.print("[red]Error: Start ID must be less than or equal to End ID.[/red]")
    elif mode == 3:
        console.print("[cyan]Enter Year Range (YYYY):[/cyan]")
        while True:
            # Use current year as default end year
            current_year = time.localtime().tm_year
            start_year = IntPrompt.ask("  Start Year (YYYY)", default=current_year - 1)
            end_year = IntPrompt.ask("  End Year (YYYY)", default=current_year)
            # Basic validation for plausible years
            if 2000 <= start_year <= 2100 and 2000 <= end_year <= 2100:
                if start_year <= end_year:
                    year_range = (start_year, end_year)
                    break
                else:
                    console.print("[red]Error: Start Year must be less than or equal to End Year.[/red]")
            else:
                console.print("[red]Error: Please enter valid 4-digit years (e.g., 2023).[/red]")
    elif mode == 4:
        console.print("[cyan]Enter Limit:[/cyan]")
        limit = IntPrompt.ask("  Maximum number of files to process", default=10)
        if limit <= 0:
            console.print("[yellow]Limit must be positive. Processing all files instead.[/yellow]")
            limit = None # Reset to process all if invalid limit given

    # --- Initialize and Run Service ---
    try:
        console.print("\n[bold yellow]Initializing Case Extractor Service...[/bold yellow]")
        # Check if input directory exists before initializing service fully
        if not INPUT_DIR.is_dir():
             console.print(f"[bold red]Error: Input directory not found at '{INPUT_DIR}'. Please check the path.[/bold red]")
             exit(1)

        # Create the service instance
        extractor_service = CaseExtractorService(
            input_dir=str(INPUT_DIR),
            output_dir=str(OUTPUT_DIR),
            gemini_rate_limit_rpm=DEFAULT_GEMINI_RATE_LIMIT_RPM
        )

        console.print("\n[bold green]Starting Processing Run...[/bold green]")
        # Call process_files with the determined filters
        extractor_service.process_files(
            limit=limit,
            file_id_range=file_id_range,
            year_range=year_range
        )

        # --- Basic Test Example (Optional) ---
        # You could add a simple test here, similar to burns_extractor.py,
        # to check if a specific JSON file was created if a known file ID was processed.
        # Example:
        # if mode == 2 and file_id_range and file_id_range[0] <= 2301 <= file_id_range[1]:
        #    test_output_file = OUTPUT_DIR / "2301.json"
        #    if test_output_file.exists():
        #        console.print(f"[green]Basic Test Passed: Output file '{test_output_file.name}' exists.[/green]")
        #        # Add more checks: load JSON, verify ID field, etc.
        #    else:
        #        console.print(f"[red]Basic Test Failed: Expected output file '{test_output_file.name}' not found.[/red]")

    except ValueError as e:
        # Catch initialization errors (e.g., missing API key, invalid dirs)
        console.print(f"[bold red]Initialization failed: {e}[/bold red]")
    except Exception as e:
        # Catch any other unexpected errors during setup or execution
        console.print(f"[bold red]An unexpected error occurred during execution: {e}[/bold red]")
        import traceback
        console.print(f"[grey50]{traceback.format_exc()}[/grey50]") # Log full traceback for debugging
