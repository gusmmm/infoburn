import json
import time
import re
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Union
from enum import Enum
from collections import defaultdict
import copy # Needed for deep copying objects during consolidation

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
from pydantic_extracter.genai_client import GenAIClientManager # Import the client manager

# --- Configuration ---
load_dotenv()

# Gemini Configuration
GEMINI_MODEL_NAME = "gemini-2.5-flash-preview-04-17" # Model for extraction
DEFAULT_GEMINI_RATE_LIMIT_RPM = 10 # Default requests per minute for Gemini API
GEMINI_TEMPERATURE = 0.1 # Controls randomness, lower for more deterministic output
GEMINI_RESPONSE_MIME_TYPE = 'application/json' # Expect JSON output
GEMINI_SYSTEM_INSTRUCTION = "You are a meticulous data scientist specializing in extracting structured medical information from clinical texts."
GEMINI_THINKING_BUDGET = 4096 # Token budget for internal thinking process

# Pydantic Models Import (with fallback for design review)
try:
    from pydantic_classifier.burns_model import (
        BurnLocation, BurnDepth, BurnMechanism, AccidentType, BurnInjury, BurnsModel, Laterality
    )
except ImportError:
    print("Error: Could not import Pydantic models from pydantic_classifier.burns_model.")
    print("Please ensure the file exists and is in the correct path.")
    # Define dummy models to allow script execution for design review, but it won't work functionally.
    class BaseModel: pass # Dummy base
    class BurnLocation(str, Enum): HEAD = "head"; TRUNK = "trunk"; ARM = "arm"; LEG = "leg"
    class BurnDepth(str, Enum): FIRST_DEGREE = "1st degree"; SECOND_DEGREE_PARTIAL = "2nd degree partial"; SECOND_DEGREE_FULL = "2nd degree full"; THIRD_DEGREE = "3rd degree"; FOURTH_DEGREE = "4th degree"
    class BurnMechanism(str, Enum): HEAT = "Heat"; CHEMICAL = "Chemicals"; ELECTRICAL = "Electrical discharge"; RADIATION = "Radiation"; FRICTION = "Friction"
    class AccidentType(str, Enum): DOMESTIC = "domestic"; WORKPLACE = "workplace"; LEISURE = "leisure"; ROAD_ACCIDENT = "road accident"; OTHER = "other"
    class Laterality(str, Enum): UNSPECIFIED = "unspecified"; LEFT = "left"; RIGHT = "right"; BILATERAL = "bilateral"
    class BurnInjury(BaseModel): location: Optional[BurnLocation] = None; depth: Optional[BurnDepth] = None; laterality: Optional[Laterality] = Laterality.UNSPECIFIED; circumferencial: Optional[bool] = None; provenance: Optional[str] = None
    class BurnsModel(BaseModel): ID: Optional[str] = None; tbsa: Optional[float] = None; burn_mechanism: Optional[BurnMechanism] = None; accident_type: Optional[AccidentType] = None; agent: Optional[str] = None; wildfire: Optional[bool] = None; bonfire: Optional[bool] = None; fireplace: Optional[bool] = None; violence: Optional[bool] = None; suicide_attempt: Optional[bool] = None; escharotomy: Optional[bool] = None; associated_trauma: List[str] = []; burns: List[BurnInjury] = []

# --- Helper for Severity Ranking ---
# Define severity order for consolidation logic
BURN_DEPTH_SEVERITY = {
    BurnDepth.FOURTH_DEGREE: 5,
    BurnDepth.THIRD_DEGREE: 4,
    BurnDepth.SECOND_DEGREE_FULL: 3,
    BurnDepth.SECOND_DEGREE_PARTIAL: 2,
    BurnDepth.FIRST_DEGREE: 1,
    None: 0 # Handle cases where depth might be missing
}

# --- Prompt Template ---
# Moved the main prompt structure here for easier modification
EXTRACTION_PROMPT_TEMPLATE = """
You are a specialized medical data extraction AI assistant. Your task is to meticulously analyze the following clinical case text, written in European Portuguese, and extract specific information related to burn injuries.

**Source Text:**
--- START TEXT ---
{medical_text}
--- END TEXT ---

**Glossary for Reference (Portuguese Terms):**
--- START GLOSSARY ---
{glossary}
--- END GLOSSARY ---

**Extraction Task:**
Extract the required information and structure it precisely according to the provided JSON schema. Adhere strictly to the schema's field names, types, and enum values.

**Key Information to Extract:**
1.  `tbsa`: Total Body Surface Area affected by burns (as a percentage, e.g., 15.5). If not mentioned, use `null`.
2.  `burn_mechanism`: The primary mechanism causing the burn (e.g., "Heat", "Electrical discharge", "Chemicals"). Use one of the allowed enum values: {mechanism_enums}. If unclear or not mentioned, use `null`.
3.  `accident_type`: The context of the accident (e.g., "domestic", "workplace"). Use one of the allowed enum values: {accident_enums}. If unclear or not mentioned, use `null`.
4.  `agent`: The specific agent causing the burn (e.g., "fire", "hot water", "sulfuric acid", "high voltage"). If not mentioned, use `null`.
5.  `wildfire`, `bonfire`, `fireplace`, `violence`, `suicide_attempt`: Boolean flags (true/false) indicating if these specific circumstances were involved. If not mentioned, use `null` or `false` if context implies absence.
6.  `escharotomy`: Boolean flag (true/false) indicating if an escharotomy procedure was performed. If not mentioned, use `null` or `false`.
7.  `associated_trauma`: A list of strings describing any other significant injuries sustained concurrently with the burns (e.g., ["fractured femur", "head injury"]). If none mentioned, use an empty list `[]`.
8.  `burn_injuries`: A list detailing each distinct burn area. For each burn:
    *   `location`: Anatomical location (e.g., "head", "left hand", "anterior trunk"). Use one of the allowed enum values: {location_enums}.
    *   `laterality`: Side affected ("left", "right", "bilateral", "unspecified"). Use one of the allowed enum values: {laterality_enums}. Default to "unspecified" if not mentioned.
    *   `depth`: Depth of the burn (e.g., "1st degree", "2nd degree partial", "3rd degree"). Use one of the allowed enum values: {depth_enums}. If not mentioned, use `null`.
    *   `circumferencial`: Boolean flag (true/false) indicating if the burn encircles the body part. If not mentioned, use `null` or `false`.
    *   `provenance`: Include the exact sentence(s) or text fragment(s) from the original text that support the burn information you've extracted. Quote the relevant text directly, maintaining the original Portuguese wording.

**Output Requirements:**
- Return **only** a single, valid JSON object matching the schema. Do not include any explanatory text before or after the JSON.
- If a specific piece of information is not found in the text, use `null` for optional fields or appropriate defaults (e.g., empty list `[]` for `associated_trauma`, `false` for boolean flags if absence is implied, "unspecified" for `laterality`). Do not guess or infer information not present.
- Ensure all JSON structures (objects `{{}}`, arrays `[]`) are correctly formed and closed.
- The patient identifier for this case is `{file_id}`. This ID should *not* be included in the JSON output itself, as it will be added later.
- For the `provenance` field, always include the exact text snippets that support each burn injury finding, using direct quotes from the source text.

**JSON Schema Reference (for structure validation):**
```json
{schema_json}
"""

class BurnsExtractorService: 
    """ Extracts burn injury details from markdown clinical case files using Google Gemini API, consolidates findings per location, and saves structured data as JSON. 
    Allows filtering files by ID range or year range. Uses GenAIClientManager for API access. """ 
    def __init__(self, input_dir: str, output_dir: str, glossary_path: str, gemini_rate_limit_rpm: int = DEFAULT_GEMINI_RATE_LIMIT_RPM): 
        """ Initializes the BurnsExtractorService.
        Args:
        input_dir: Path to the directory containing input markdown files.
        output_dir: Path to the directory where output JSON files will be saved.
        glossary_path: Path to the glossary file (optional).
        gemini_rate_limit_rpm: Maximum requests per minute allowed for the Gemini API.
        """
        self.console = Console()
        self.client: Optional[genai.Client] = None # Initialize client attribute

        try:
            # Use GenAIClientManager to get the client
            client_manager = GenAIClientManager(console=self.console)
            self.client = client_manager.get_client() # This handles API key loading and client creation
        except ValueError as e:
            # Error during client initialization (e.g., missing API key) is fatal
            self.console.print(f"[bold red]Error initializing service: {e}[/bold red]")
            raise # Stop execution if essential setup fails

        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.glossary_path = Path(glossary_path)
        self.glossary_content: Optional[str] = None # Lazy loaded

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
        self.console.print(f"Glossary path: '{self.glossary_path}'")
        self.console.print(f"Using Gemini Model: '{GEMINI_MODEL_NAME}'")

# Removed _load_api_key and _initialize_client methods as they are now handled by GenAIClientManager

    def _ensure_output_dir(self):
        """Ensures the output directory exists, creating it if necessary."""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self.console.print(f"[bold red]Error creating output directory '{self.output_dir}': {e}[/bold red]")
            raise # Stop execution if output dir cannot be created

    def _load_glossary(self) -> str:
        """Loads the glossary content from the specified file. Loads only once."""
        if self.glossary_content is None: # Load only if not already loaded
            try:
                if self.glossary_path.is_file():
                    self.glossary_content = self.glossary_path.read_text(encoding='utf-8')
                    self.console.print(f"[blue]Glossary loaded successfully from '{self.glossary_path}'.[/blue]")
                else:
                    self.console.print(f"[yellow]Warning: Glossary file not found at '{self.glossary_path}'. Proceeding without glossary.[/yellow]")
                    self.glossary_content = "" # Set to empty string if not found
            except Exception as e:
                self.console.print(f"[bold red]Error reading glossary file '{self.glossary_path}': {e}. Proceeding without glossary.[/bold red]")
                self.glossary_content = ""
        return self.glossary_content if self.glossary_content else "No glossary provided."

    def _get_markdown_files(self,
                            limit: Optional[int] = None,
                            file_id_range: Optional[Tuple[int, int]] = None,
                            year_range: Optional[Tuple[int, int]] = None
                        ) -> List[Path]:
        """
        Gets a list of markdown files from the input directory, applying optional filters.
        Filters by ID range (numeric stem) or year range (first two digits of stem).

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

        # Get all markdown files initially, sorted naturally
        all_files = sorted(list(self.input_dir.glob("*.md")), key=lambda p: p.stem)
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
                    # Attempt to convert the entire stem to an integer
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
            # Convert full years (e.g., 2023) to two-digit format (e.g., 23)
            start_yy = start_year % 100
            end_yy = end_year % 100
            self.console.print(f"[blue]Filtering by Year range: {start_year} ({start_yy:02d}) to {end_year} ({end_yy:02d})[/blue]")
            year_pattern = re.compile(r"^\d{2}") # Regex to match first two digits
            year_filtered_files = [] # Use a temporary list for this filter
            for file_path in all_files: # Filter from the original full list
                match = year_pattern.match(file_path.stem)
                if match:
                    try:
                        file_yy = int(match.group(0))
                        # Handle year wrap-around if necessary (e.g., 99 to 01) - assumes simple range for now
                        if start_yy <= end_yy:
                            if start_yy <= file_yy <= end_yy:
                                year_filtered_files.append(file_path)
                        else: # Wrap around case e.g., 99 to 02
                            if file_yy >= start_yy or file_yy <= end_yy:
                                year_filtered_files.append(file_path)
                    except ValueError: # Should not happen with regex, but good practice
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

    def _create_prompt(self, medical_text: str, file_id: str) -> str:
        """
        Creates a detailed prompt for the Gemini AI using the template.

        Args:
            medical_text: The clinical case text read from the markdown file.
            file_id: The identifier derived from the filename (e.g., '2301').

        Returns:
            A formatted prompt string.
        """
        glossary = self._load_glossary() # Load glossary content if not already loaded

        # Helper to format enum values for the prompt
        def format_enums(enum_cls):
            return ', '.join(f'"{e.value}"' for e in enum_cls)

        # Format the prompt using the template and dynamic values
        # This .format() call correctly substitutes the placeholders
        prompt = EXTRACTION_PROMPT_TEMPLATE.format(
            medical_text=medical_text,
            glossary=glossary,
            mechanism_enums=format_enums(BurnMechanism),
            accident_enums=format_enums(AccidentType),
            location_enums=format_enums(BurnLocation),
            laterality_enums=format_enums(Laterality),
            depth_enums=format_enums(BurnDepth),
            file_id=file_id,
            schema_json=json.dumps(BurnsModel.model_json_schema(), indent=2)
        )
        return prompt

    def _extract_burns(self, medical_text: str, file_id: str) -> Optional[BurnsModel]:
        """
        Extracts burn information from the medical text using the Gemini API via the managed client.

        Args:
            medical_text: The content of the medical case file.
            file_id: The identifier derived from the filename.

        Returns:
            A BurnsModel object containing the extracted data, or None if extraction fails.
        """
        if not self.client:
            self.console.print("[bold red]Error: Gemini client is not initialized. Cannot perform extraction.[/bold red]")
            return None

        prompt = self._create_prompt(medical_text, file_id)

        try:
            # Configure generation settings using constants
            generation_config = {
                "temperature": GEMINI_TEMPERATURE,
                "response_mime_type": GEMINI_RESPONSE_MIME_TYPE
            }

            # In the new Google Gemini API, we access models differently
            # Instead of client.get_model, we use client.models.generate_content directly
            self.console.print(f"[grey50]Sending request to Gemini for file ID: {file_id}...[/grey50]")
            response = self.client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt,
                config=generation_config,
                # safety_settings can be added here if needed
                # stream=False # Default is False
            )

            # Accessing the response text correctly
            if not response.candidates or not response.candidates[0].content.parts:
                self.console.print(f"[yellow]Warning: Received no valid content parts from API for file ID {file_id}. Response: {response}[/yellow]")
                # Check for prompt feedback (e.g., blocked due to safety)
                if response.prompt_feedback:
                    self.console.print(f"[yellow]Prompt Feedback: {response.prompt_feedback}[/yellow]")
                return None

            response_text = response.candidates[0].content.parts[0].text
            self.console.print(f"[grey50]Received response from Gemini for file ID: {file_id}. Validating...[/grey50]")

            if response_text:
                try:
                    # Parse the JSON string from the response text
                    response_data = json.loads(response_text)

                    # --- FIX: Handle potential field name mismatch ---
                    # If the LLM returned 'burns' instead of 'burn_injuries', rename it
                    # before validation so Pydantic finds the data.
                    # if 'burns' in response_data and 'burn_injuries' not in response_data:
                    #     self.console.print(f"[yellow]Note:[/yellow] LLM returned 'burns' field for {file_id}. Renaming to 'burn_injuries' for validation.")
                    #     response_data['burn_injuries'] = response_data.pop('burns')
                    # --- End FIX ---

                    # Validate the potentially modified data against the Pydantic model
                    validated_data = BurnsModel.model_validate(response_data)
                    # Add a debug print to confirm structure after validation
                    # self.console.print(f"DEBUG: Validated data structure for {file_id}: {validated_data.model_dump(exclude_none=True)}")
                    self.console.print(f"[green]Successfully extracted and validated data for file ID: {file_id}[/green]")
                    return validated_data
                except json.JSONDecodeError as json_err:
                    self.console.print(f"[red]Error decoding JSON response for file ID {file_id}: {json_err}[/red]")
                    self.console.print(f"Raw response text (first 500 chars): {response_text[:500]}...")
                    return None
                except ValidationError as val_err:
                    self.console.print(f"[red]Validation Error for file ID {file_id}: Extracted data does not match schema: {val_err}[/red]")
                    try:
                        response_data_preview = json.loads(response_text) # Try parsing again for preview
                        self.console.print(f"Raw response data preview: {response_data_preview}")
                    except Exception:
                        self.console.print(f"Raw response text preview (first 500 chars): {response_text[:500]}...")
                    return None
            else:
                self.console.print(f"[yellow]Warning: Received empty response text from API for file ID {file_id}.[/yellow]")
                return None # Or return BurnsModel() if an empty model is preferred

        except google_exceptions.GoogleAPIError as api_err:
            self.console.print(f"[bold red]Google API Error during extraction for file ID {file_id}: {api_err}[/bold red]")
            if isinstance(api_err, google_exceptions.ResourceExhausted):
                self.console.print("[bold yellow]Quota possibly exceeded. Consider increasing delay or checking quota limits.[/bold yellow]")
            # Add more specific API error handling if needed
            return None
        except Exception as e:
            # Catch any other unexpected errors during the API call or processing
            self.console.print(f"[bold red]An unexpected error occurred during extraction for file ID {file_id}: {e}[/bold red]")
            import traceback
            self.console.print(f"[grey50]{traceback.format_exc()}[/grey50]") # Log traceback for debugging
            return None

    def _get_burn_severity(self, burn: BurnInjury) -> Tuple[int, bool]:
        """Helper to get a sortable severity score for a burn injury."""
        depth_score = BURN_DEPTH_SEVERITY.get(burn.depth, 0)
        circumferencial_score = burn.circumferencial if burn.circumferencial is not None else False
        # Prioritize depth, then circumferential status
        return (depth_score, circumferencial_score)

    def _consolidate_burn_injuries(self, injuries: List[BurnInjury]) -> List[BurnInjury]:
        """
        Consolidates multiple burn injury entries for the same location.
        Selects the most severe entry based on depth and circumferential status.
        Merges laterality (left + right -> bilateral).

        Args:
            injuries: A list of BurnInjury objects extracted by the AI.

        Returns:
            A consolidated list of BurnInjury objects.
        """
        # Group injuries by location enum value
        grouped_by_location: Dict[BurnLocation, List[BurnInjury]] = defaultdict(list)
        for injury in injuries:
            if injury.location:  # Only process injuries with a location specified
                grouped_by_location[injury.location].append(injury)

        consolidated_injuries: List[BurnInjury] = []

        for location, group in grouped_by_location.items():
            if not group: continue # Should not happen with defaultdict, but safe check

            if len(group) == 1:
                consolidated_injuries.append(group[0])
                continue

            # Find the most severe injury in the group based on depth and circumferential status
            most_severe_injury = max(group, key=self._get_burn_severity)
            # Deep copy to avoid modifying the original object when merging info
            consolidated_injury = copy.deepcopy(most_severe_injury)

            # --- Merge Information ---
            # 1. Laterality: Check if left and right exist for the same location
            lateralities = {inj.laterality for inj in group if inj.laterality}
            has_left = Laterality.LEFT in lateralities
            has_right = Laterality.RIGHT in lateralities

            if has_left and has_right:
                consolidated_injury.laterality = Laterality.BILATERAL
            elif Laterality.BILATERAL in lateralities: # If bilateral is explicitly mentioned, use it
                consolidated_injury.laterality = Laterality.BILATERAL
            elif has_left: # Only left mentioned
                consolidated_injury.laterality = Laterality.LEFT
            elif has_right: # Only right mentioned
                consolidated_injury.laterality = Laterality.RIGHT
            else: # Otherwise, keep the laterality from the most severe entry (might be UNSPECIFIED)
                consolidated_injury.laterality = most_severe_injury.laterality

            # 2. Circumferential: True if *any* entry for this location is circumferential
            is_any_circumferential = any(
                inj.circumferencial for inj in group if inj.circumferencial is True # Explicitly check for True
            )
            consolidated_injury.circumferencial = is_any_circumferential

            # 3. Provenance: Combine unique provenance strings
            all_provenance = set()
            for inj in group:
                # Check if 'provenance' attribute exists and is not None/empty
                if hasattr(inj, 'provenance') and inj.provenance:
                    all_provenance.add(inj.provenance.strip()) # Add stripped string to set

            # Join unique, non-empty provenance strings
            consolidated_injury.provenance = " | ".join(filter(None, all_provenance)) if all_provenance else None

            consolidated_injuries.append(consolidated_injury)

            # Log detailed consolidation for this location
            depth_val = consolidated_injury.depth.value if consolidated_injury.depth else "N/A"
            lat_val = consolidated_injury.laterality.value if consolidated_injury.laterality else "N/A"
            self.console.print(
                f"[dim cyan]Location '{location.value}': "
                f"Consolidated {len(group)} burns -> Depth: {depth_val}, "
                f"Laterality: {lat_val}, "
                f"Circumferential: {consolidated_injury.circumferencial}[/dim cyan]"
            )

        self.console.print(f"[cyan]Consolidated {len(injuries)} initial burn entries into {len(consolidated_injuries)} unique location entries.[/cyan]")
        return consolidated_injuries


    def _save_json(self, data: BurnsModel, input_file_path: Path):
        """
        Saves the extracted and validated BurnsModel data to a JSON file.
        The patient ID is derived from the input file stem and added to the data.

        Args:
            data: The BurnsModel object containing the extracted data.
            input_file_path: The Path object of the original input markdown file.
        """
        output_filename = input_file_path.stem + ".json"
        output_path = self.output_dir / output_filename
        file_id = input_file_path.stem  # Get ID from filename

        # Ensure the data object is not None before proceeding
        if data is None:
            self.console.print(f"[red]Error: Cannot save None data for input file '{input_file_path.name}'.[/red]")
            return

        try:
            # Convert the BurnsModel to a dictionary, excluding None values for cleaner output
            data_dict = data.model_dump(mode='json', exclude_none=True)

            # Add the ID field to the dictionary (not to the model itself before dumping)
            data_dict["ID"] = file_id

            # Write the dictionary to a JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=4, ensure_ascii=False)
            # self.console.print(f"[green]Successfully saved extracted data to '{output_path}'[/green]") # Can be noisy

        except IOError as e:
            self.console.print(f"[red]Error saving JSON file '{output_path}': {e}[/red]")
        except Exception as e:
            # Catch potential errors during model_dump or file writing
            self.console.print(f"[red]Unexpected error saving JSON for file ID {file_id} to '{output_path}': {e}[/red]")


    def process_files(self,
                limit: Optional[int] = None,
                file_id_range: Optional[Tuple[int, int]] = None,
                year_range: Optional[Tuple[int, int]] = None):
        """
        Processes markdown files based on specified filters: extracts burn info,
        consolidates injuries, and saves results as JSON files.

        Args:
            limit: Maximum number of files to process.
            file_id_range: A tuple (start_id, end_id) to filter files by numeric stem ID.
            year_range: A tuple (start_year, end_year) to filter files by year derived
                        from the first two digits of the stem.
        """
        markdown_files = self._get_markdown_files(limit=limit, file_id_range=file_id_range, year_range=year_range)
        if not markdown_files:
            self.console.print("[yellow]No markdown files found matching the specified criteria. Exiting.[/yellow]")
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
                extracted_data = self._extract_burns(medical_text, file_id)

                if extracted_data is None:
                    self.console.print(f"[yellow]Extraction failed for '{file_path.name}'. Skipping saving.[/yellow]")
                    fail_count += 1
                    # Apply rate limiting delay after API call attempt (success or fail)
                    if self.gemini_sleep_duration > 0 and i < len(markdown_files) - 1:
                        time.sleep(self.gemini_sleep_duration)
                    progress.advance(task_id)
                    continue # Skip to next file

                # --- Consolidate Injuries ---
                # Check if 'burn_injuries' exists and is a non-empty list
                if hasattr(extracted_data, 'burns') and extracted_data.burns:
                    extracted_data.burns = self._consolidate_burn_injuries(extracted_data.burns)
                else:
                    self.console.print(f"[cyan]No burn injuries found/extracted for '{file_path.name}'. Skipping consolidation.[/cyan]")

                # --- Save Data ---
                self._save_json(extracted_data, file_path)
                success_count += 1

                # --- Gemini Rate Limiting Delay ---
                # Apply delay *after* processing each file (API call + saving)
                # except for the very last file.
                if self.gemini_sleep_duration > 0 and i < len(markdown_files) - 1:
                    # self.console.print(f"[dim]Waiting {self.gemini_sleep_duration:.2f}s before next API call...[/dim]") # Optional verbose log
                    time.sleep(self.gemini_sleep_duration)
                # ---------------------------------
                progress.advance(task_id) # Advance progress after all steps for the file

        # --- Final Summary ---
        summary_table = Table(title="Processing Summary", show_header=True, header_style="bold magenta")
        summary_table.add_column("Status", style="dim", width=15)
        summary_table.add_column("Count", justify="right")
        summary_table.add_row("Files Found", str(len(markdown_files)))
        summary_table.add_row("[green]Successfully Processed", str(success_count))
        summary_table.add_row("[red]Failed/Skipped", str(fail_count))

        self.console.print(summary_table)
        self.console.print("[bold green]Processing complete.[/bold green]")


if __name__ == "__main__": 
    console = Console() 
    console.print("\n[bold blue]🔥 Burn Injury Extractor Service 🔥[/bold blue]\n")
    # Determine project root relative to this script file
    try:
        # Assumes script is in 'pydantic_extracter' subdir relative to project root
        PROJECT_ROOT = Path(__file__).resolve().parent.parent
    except Exception as e:
        console.print(f"[bold red]Error determining project root: {e}. Please check script location.[/bold red]")
        exit(1) # Exit if project structure is unexpected

    # Define standard input/output directories relative to project root
    INPUT_DIR = PROJECT_ROOT / "data" / "output" / "markdown" / "clean"
    OUTPUT_DIR = PROJECT_ROOT / "data" / "output" / "json" / "burns" # Specific output for burns
    GLOSSARY_PATH = PROJECT_ROOT / "documentation" / "PT-glossario.md"

    # --- User Interaction for Filtering ---
    console.print("[bold yellow]Select File Processing Mode:[/bold yellow]")
    console.print("  1. Process All Files")
    console.print("  2. Process by File ID Range (e.g., 2301 to 2315)")
    console.print("  3. Process by Year Range (e.g., 2023 to 2024)")
    console.print("  4. Process First N Files (Limit)")

    mode = IntPrompt.ask("Enter choice", choices=["1", "2", "3", "4"], default=1)

    limit: Optional[int] = None
    file_id_range: Optional[Tuple[int, int]] = None
    year_range: Optional[Tuple[int, int]] = None

    if mode == 2:
        while True:
            start_id = IntPrompt.ask("[cyan]Enter start File ID[/cyan]")
            end_id = IntPrompt.ask("[cyan]Enter end File ID[/cyan]")
            if start_id <= end_id:
                file_id_range = (start_id, end_id)
                break
            else:
                console.print("[red]Error: Start ID must be less than or equal to End ID.[/red]")
    elif mode == 3:
        while True:
            start_year = IntPrompt.ask("[cyan]Enter start Year (YYYY)[/cyan]", default=2023)
            end_year = IntPrompt.ask("[cyan]Enter end Year (YYYY)[/cyan]", default=time.localtime().tm_year) # Default to current year
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
        limit = IntPrompt.ask("[cyan]Enter the maximum number of files to process[/cyan]", default=5)
        if limit <= 0:
            console.print("[yellow]Limit must be positive. Processing all files instead.[/yellow]")
            limit = None # Reset to process all if invalid limit given

    # --- Initialize and Run Service ---
    try:
        console.print("\n[bold yellow]Initializing Burns Extractor Service...[/bold yellow]")
        # Check if input directory exists before initializing service fully
        if not INPUT_DIR.is_dir():
            console.print(f"[bold red]Error: Input directory not found at '{INPUT_DIR}'. Please check the path.[/bold red]")
            exit(1)

        extractor_service = BurnsExtractorService(
            input_dir=str(INPUT_DIR),
            output_dir=str(OUTPUT_DIR),
            glossary_path=str(GLOSSARY_PATH),
            gemini_rate_limit_rpm=DEFAULT_GEMINI_RATE_LIMIT_RPM # Use the constant
        )

        console.print("\n[bold green]Starting Processing Run...[/bold green]")
        extractor_service.process_files(
            limit=limit,
            file_id_range=file_id_range,
            year_range=year_range
        )

    except ValueError as e:
        # Catch initialization errors (e.g., missing API key from GenAIClientManager)
        console.print(f"[bold red]Initialization failed: {e}[/bold red]")
    except Exception as e:
        # Catch any other unexpected errors during setup or execution
        console.print(f"[bold red]An unexpected error occurred during execution: {e}[/bold red]")
        import traceback
        console.print(f"[grey50]{traceback.format_exc()}[/grey50]") # Log traceback for debugging