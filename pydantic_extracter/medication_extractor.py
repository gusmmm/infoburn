import os
import json
import time
from pathlib import Path
from typing import List, Optional, Dict
from enum import Enum

from pydantic import BaseModel, Field, ValidationError
from google import genai
from google.genai import types
from google.api_core import exceptions as google_exceptions

# Assuming the tool is correctly placed and importable
from core_tools.snomedct import find_snomed_code_fhir_expand

from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

# --- Configuration ---
load_dotenv()
GEMINI_MODEL_NAME = "gemini-2.5-flash-preview-04-17" # As per user's file
DEFAULT_GEMINI_RATE_LIMIT_RPM = 10 # Requests per minute for Gemini API


# --- Pydantic Models ---

class MedicationFrequency(str, Enum):
    """Standard medication frequencies."""
    QD = "Once daily"
    BID = "Twice daily"
    TID = "Three times daily"
    QID = "Four times daily"
    QHS = "At bedtime"
    QOD = "Every other day"
    QWK = "Once weekly"
    PRN = "As needed"
    OTHER = "Other (specify in frequency_other)"
    UNKNOWN = "Unknown" # Added for robustness

class SnomedConcept(BaseModel):
    """
    Represents a SNOMED-CT concept, including its unique identifier and
    human-readable term. Essential for semantic interoperability.
    """
    sctid: str = Field(
        description="The unique SNOMED CT Identifier (SCTID) for the concept. "
                    "This is the primary key for interoperability."
    )
    term: str = Field(
        description="The preferred human-readable description (term) associated "
                    "with the SCTID."
    )

class Medication(BaseModel):
    """
    Model for representing a medication the patient was taking before admission,
    including SNOMED-CT classification for interoperability.
    """
    name: str = Field(
        description="Name of the medication (e.g., 'Metformin', 'Lisinopril'). "
                    "This is typically the generic or brand name found in the text."
    )
    dosage: Optional[str] = Field( # Made optional
        None, description="Dosage amount and unit (e.g., '500mg', '10mg', '2 puffs')."
    )
    # Allow frequency to be string initially, validate later if needed or handle conversion
    frequency: Optional[str] = Field( # Made optional, store as string initially
         None, description="How often the medication is taken (e.g., 'BID', 'Once daily', 'As needed')."
    )
    frequency_other: Optional[str] = Field( # Made optional
        None, description="Description of frequency if not a standard code."
    )
    notes: Optional[str] = Field( # Made optional
        None, description="Additional details or context about the medication extracted "
                    "from the medical text (e.g., 'for hypertension', 'patient stopped 2 weeks ago')."
    )
    snomed_classification: Optional[SnomedConcept] = Field( # Made optional
        None, description="SNOMED-CT classification representing the primary therapeutic or "
                    "pharmacological class of the medication. May be null if not found."
    )

class MedicationList(BaseModel):
    """
    Model for representing a list of medications the patient was taking before admission.
    This is the structure for the final JSON output.
    """
    ID: str = Field(description="Patient identifier, derived from the source filename.")
    medications: List[Medication] = Field(
        description="List of medications the patient was taking before admission."
    )

# --- Temporary Models for Initial Extraction ---
class SimpleMedication(BaseModel):
    """Temporary model for initial Gemini extraction."""
    name: str
    dosage: Optional[str] = None # Allow missing fields
    frequency: Optional[str] = None
    notes: Optional[str] = None

class SimpleMedicationList(BaseModel):
    """Temporary root model for initial Gemini extraction."""
    medications: List[SimpleMedication]

# --- Service Class ---
class MedicationExtractorService:
    """
    Extracts and enriches medication information from markdown files.
    """
    def __init__(self, input_dir: str, output_dir: str, rate_limit_rpm: int = DEFAULT_RATE_LIMIT_RPM):
        self.console = Console()
        try:
            self.api_key = self._load_api_key()
            self.client = self._initialize_client()
        except ValueError as e:
            self.console.print(f"[bold red]Error initializing service: {e}[/bold red]")
            raise

        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)

        # Rate Limiting Setup
        self.rate_limit_rpm = rate_limit_rpm
        if self.rate_limit_rpm <= 0:
            self.console.print("[yellow]Warning: Rate limit must be positive. Disabling rate limiting.[/yellow]")
            self.sleep_duration = 0
        else:
            self.sleep_duration = 60.0 / self.rate_limit_rpm
            self.console.print(f"[blue]Rate limiting enabled: {self.rate_limit_rpm} RPM (delay: {self.sleep_duration:.2f} seconds between calls).[/blue]")

        self._ensure_output_dir()
        self.console.print(f"Input directory: '{self.input_dir}'")
        self.console.print(f"Output directory: '{self.output_dir}'")

    def _load_api_key(self) -> str:
        """Loads the Gemini API key from environment variables."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not found.")
        return api_key

    def _initialize_client(self) -> genai.Client:
        """Initializes the Google Gemini API client."""
        try:
            client = genai.Client(api_key=self.api_key)
            self.console.print("[green]Gemini client initialized successfully.[/green]")
            return client
        except Exception as e:
            raise ValueError(f"Failed to initialize Gemini client: {e}")

    def _ensure_output_dir(self):
        """Ensures the output directory exists, creating it if necessary."""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self.console.print(f"[bold red]Error creating output directory '{self.output_dir}': {e}[/bold red]")
            raise

    def _get_markdown_files(self, limit: Optional[int] = None) -> List[Path]:
        """Gets a list of markdown files from the input directory, optionally limited."""
        if not self.input_dir.is_dir():
            self.console.print(f"[bold red]Error: Input directory '{self.input_dir}' not found or is not a directory.[/bold red]")
            return []
        files = sorted(list(self.input_dir.glob("*.md")))
        if limit is not None and limit > 0:
            self.console.print(f"[yellow]Limiting processing to the first {limit} files.[/yellow]")
            return files[:limit]
        return files

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

    def _extract_simple_medications(self, medical_text: str) -> Optional[List[Dict]]:
        """Extracts basic medication details using the Gemini API."""
        prompt = f"""This is a clinical case text:
        --- START TEXT ---
        {medical_text}
        --- END TEXT ---

        The text is a critical care burn patient clinical case written in European Portuguese.

        Your task is to extract the patient's previous medications (medications they were taking *before* the current burn incident). For each medication, extract its name, dosage (if available), frequency (if available), and any relevant notes.

        Return *only* the list of medications structured according to the provided JSON schema. The output must be in English. Focus on accuracy and completeness based *only* on the provided text.
        """
        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction="You are an AI assistant specialized in extracting medication information from clinical texts. Extract only the name, dosage, frequency, and notes for each medication mentioned in the patient's history.",
                    temperature=0.1,
                    response_mime_type='application/json',
                    response_schema=SimpleMedicationList.model_json_schema(),
                    thinking_config=genai.types.ThinkingConfig(
                        thinking_budget=4096
                    ),
                ),
            )
            if response.text:
                try:
                    response_data = json.loads(response.text)
                    # Validate with the simple schema
                    validated_simple_data = SimpleMedicationList.model_validate(response_data)
                    # Return the list of medication dicts
                    return [med.model_dump() for med in validated_simple_data.medications]
                except json.JSONDecodeError as json_err:
                    self.console.print(f"[red]Error decoding JSON response: {json_err}[/red]")
                    self.console.print(f"Raw response text: {response.text[:500]}...")
                    return None
                except ValidationError as val_err:
                    self.console.print(f"[red]Validation Error (Initial Extraction): {val_err}[/red]")
                    self.console.print(f"Raw response data: {response_data}")
                    return None
            else:
                 self.console.print("[yellow]Warning: Received empty response from API during initial extraction.[/yellow]")
                 return None
        except google_exceptions.GoogleAPIError as api_err:
            self.console.print(f"[bold red]Google API Error during initial extraction: {api_err}[/bold red]")
            if isinstance(api_err, google_exceptions.ResourceExhausted):
                 self.console.print("[bold yellow]Quota possibly exceeded.[/bold yellow]")
            return None
        except Exception as e:
            self.console.print(f"[bold red]An unexpected error occurred during initial extraction: {e}[/bold red]")
            return None

    def _enrich_with_snomed(self, simple_medications: List[Dict]) -> List[Dict]:
        """Enriches medication data with SNOMED CT codes."""
        enriched_medications = []
        if not simple_medications:
            return []

        self.console.print(f"[cyan]Enriching {len(simple_medications)} medications with SNOMED CT codes...[/cyan]")
        for med_dict in simple_medications:
            med_name = med_dict.get("name")
            if not med_name:
                self.console.print("[yellow]Skipping medication with missing name.[/yellow]")
                continue

            # self.console.print(f"  Looking up SNOMED code for: {med_name}") # Verbose logging
            snomed_result = None
            try:
                # Directly call the SNOMED lookup function
                snomed_result = find_snomed_code_fhir_expand(medication_name=med_name)
            except Exception as e:
                self.console.print(f"[red]Error during SNOMED lookup for '{med_name}': {e}[/red]")

            enriched_med = med_dict.copy() # Start with the simple extracted data

            if snomed_result and isinstance(snomed_result, dict) and "sctid" in snomed_result and "term" in snomed_result:
                 # Validate against SnomedConcept model
                 try:
                     snomed_concept = SnomedConcept.model_validate(snomed_result)
                     enriched_med["snomed_classification"] = snomed_concept.model_dump()
                     # self.console.print(f"    Found: {snomed_concept.term} ({snomed_concept.sctid})") # Verbose
                 except ValidationError as val_err:
                     self.console.print(f"[yellow]Warning: SNOMED result for '{med_name}' failed validation: {val_err}. Result: {snomed_result}[/yellow]")
                     enriched_med["snomed_classification"] = None # Set to None if validation fails
            else:
                # self.console.print(f"    No valid SNOMED code found for {med_name}") # Verbose
                enriched_med["snomed_classification"] = None # Explicitly set to None if not found or invalid

            # Add frequency_other if needed (or ensure it exists if required by final model)
            if "frequency" not in enriched_med or enriched_med["frequency"] is None:
                 enriched_med["frequency"] = MedicationFrequency.UNKNOWN.value # Default if missing
            # Ensure frequency_other exists, even if empty, if Medication model requires it
            enriched_med.setdefault("frequency_other", None)

            enriched_medications.append(enriched_med)

        return enriched_medications

    def _save_json(self, medication_list_data: List[Dict], input_file_path: Path):
        """Saves the final enriched medication data to a JSON file."""
        output_filename = input_file_path.stem + ".json"
        output_path = self.output_dir / output_filename
        file_id = input_file_path.stem

        # Prepare the final structure matching MedicationList
        final_data = {
            "ID": file_id,
            "medications": medication_list_data # Already enriched list of dicts
        }

        try:
            # Validate the final structure before saving (optional but recommended)
            try:
                MedicationList.model_validate(final_data)
            except ValidationError as val_err:
                 self.console.print(f"[bold red]Final Validation Error for '{output_filename}': {val_err}[/bold red]")
                 # Decide whether to save anyway or skip
                 # For now, we'll save but log the error prominently
                 self.console.print(f"[yellow]Saving file '{output_path}' despite validation error.[/yellow]")


            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=4, ensure_ascii=False)
            # self.console.print(f"[green]Successfully saved: '{output_path}'[/green]")
        except IOError as e:
            self.console.print(f"[red]Error saving JSON file '{output_path}': {e}[/red]")
        except Exception as e:
            self.console.print(f"[red]Unexpected error saving JSON '{output_path}': {e}[/red]")

    def process_files(self, limit: Optional[int] = None):
        """Processes markdown files to extract and enrich medication information."""
        markdown_files = self._get_markdown_files(limit=limit)
        if not markdown_files:
            self.console.print("[yellow]No markdown files found to process.[/yellow]")
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

            for i, file_path in enumerate(markdown_files):
                progress.update(task, description=f"[cyan]Processing: {file_path.name}")

                medical_text = self._read_file(file_path)
                if medical_text is None:
                    fail_count += 1; progress.advance(task); continue

                # Step 1: Initial Extraction
                simple_meds = self._extract_simple_medications(medical_text)
                if simple_meds is None:
                    self.console.print(f"[yellow]Failed initial extraction for '{file_path.name}'. Skipping.[/yellow]")
                    fail_count += 1; progress.advance(task); continue # Skip if initial extraction fails

                if not simple_meds:
                     self.console.print(f"[cyan]No medications found/extracted for '{file_path.name}'. Saving empty list.[/cyan]")
                     # Proceed to save empty list

                # Step 2: Enrichment
                enriched_meds = self._enrich_with_snomed(simple_meds)

                # Step 3: Save
                self._save_json(enriched_meds, file_path)
                success_count += 1
                progress.advance(task)

                # Rate Limiting Delay (applied after each file's Gemini call)
                if self.sleep_duration > 0 and i < len(markdown_files) - 1:
                    time.sleep(self.sleep_duration)

        self.console.print("-" * 30)
        self.console.print(f"[bold green]Processing complete.[/bold green]")
        self.console.print(f"Successfully processed and saved: {success_count}")
        self.console.print(f"Failed/Skipped: {fail_count}")
        self.console.print("-" * 30)


# --- Main Execution & Test ---
if __name__ == "__main__":
    console = Console()
    console.print("[bold blue]Medication Extractor[/bold blue]")

    PROJECT_ROOT = Path(__file__).resolve().parent.parent # Adjust if script moves
    INPUT_DIR = PROJECT_ROOT / "data" / "output" / "markdown" / "clean"
    OUTPUT_DIR = PROJECT_ROOT / "data" / "output" / "json" / "medication" # Corrected output dir

    try:
        console.print("\n[bold yellow]Starting Test Run (limit=10 files)...[/bold yellow]")
        extractor_service = MedicationExtractorService(
            input_dir=str(INPUT_DIR),
            output_dir=str(OUTPUT_DIR),
            rate_limit_rpm=DEFAULT_GEMINI_RATE_LIMIT_RPM
        )
        extractor_service.process_files(limit=10)

        # --- Optional: Full Run ---
        # console.print("\n[bold green]Starting Full Run...[/bold green]")
        # full_run_service = MedicationExtractorService(
        #     input_dir=str(INPUT_DIR),
        #     output_dir=str(OUTPUT_DIR),
        #     rate_limit_rpm=DEFAULT_RATE_LIMIT_RPM
        # )
        # full_run_service.process_files()

    except ValueError as e:
        console.print(f"[bold red]Initialization failed: {e}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred during execution: {e}[/bold red]")