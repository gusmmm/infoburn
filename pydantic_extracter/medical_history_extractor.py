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

# Import the SNOMED CT diagnosis lookup function
from core_tools.diagnosis import find_diagnosis_snomed_code

from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

# --- Configuration ---
load_dotenv()
GEMINI_MODEL_NAME = "gemini-2.0-flash" # Use a more descriptive constant

# --- Pydantic Models ---

class SnomedConcept(BaseModel):
    """
    Represents a SNOMED-CT concept for standardized terminology.
    """
    sctid: str = Field(description="The unique SNOMED CT Identifier (SCTID).")
    term: str = Field(description="The preferred human-readable term for the SCTID.")

class DiseaseCategory(str, Enum):
    INFECTIOUS = "Certain infectious or parasitic diseases"
    NEOPLASMS = "Neoplasms"
    BLOOD_DISORDERS = "Diseases of the blood or blood-forming organs"
    IMMUNE_SYSTEM = "Diseases of the immune system"
    ENDOCRINE_METABOLIC = "Endocrine, nutritional or metabolic diseases"
    MENTAL_BEHAVIORAL = "Mental, behavioural or neurodevelopmental disorders"
    SLEEP_DISORDERS = "Sleep-wake disorders"
    NERVOUS_SYSTEM = "Diseases of the nervous system"
    VISUAL_SYSTEM = "Diseases of the visual system"
    EAR_DISORDERS = "Diseases of the ear or mastoid process"
    CIRCULATORY_SYSTEM = "Diseases of the circulatory system"
    RESPIRATORY_SYSTEM = "Diseases of the respiratory system"
    DIGESTIVE_SYSTEM = "Diseases of the digestive system"
    SKIN_DISORDERS = "Diseases of the skin"
    MUSCULOSKELETAL = "Diseases of the musculoskeletal system or connective tissue"
    GENITOURINARY = "Diseases of the genitourinary system"
    SEXUAL_HEALTH = "Conditions related to sexual health"
    PREGNANCY = "Pregnancy, childbirth or the puerperium"
    PERINATAL = "Certain conditions originating in the perinatal period"
    DEVELOPMENTAL = "Developmental anomalies"
    SYMPTOMS_SIGNS = "Symptoms, signs or clinical findings, not elsewhere classified"
    INJURY_POISONING = "Injury, poisoning or certain other consequences of external causes"
    EXTERNAL_CAUSES = "External causes of morbidity or mortality"
    HEALTH_FACTORS = "Factors influencing health status or contact with health services"
    TRADITIONAL_MEDICINE = "Supplementary Chapter Traditional Medicine Conditions - Module I"
    UNKNOWN = "Unknown or Unspecified"

class Disease(BaseModel):
    name: str = Field(description="The name of the disease or condition as extracted.")
    category: DiseaseCategory = Field(
        default=DiseaseCategory.UNKNOWN, # Default if Gemini doesn't provide it
        description="The category of the disease based on standard classifications."
    )
    snomed_classification: Optional[SnomedConcept] = Field( # Added field
        None, description="SNOMED-CT classification for the disease name."
    )

class PreviousMedicalHistory(BaseModel):
    ID: Optional[str] = Field(None, description="Patient identifier, derived from the source filename.") # Keep optional here, set in _save_json
    previous_diseases: List[Disease] = Field(description="A list of diseases or conditions the patient had prior to the current admission.")

# --- Service Class ---
class MedicalHistoryExtractorService:
    """
    Extracts previous medical history from markdown files using Google Gemini API.
    """
    def __init__(self, input_dir: str, output_dir: str, glossary_path: str, rate_limit_rpm: int = 15): # Add rate_limit_rpm parameter
        self.console = Console()
        try:
            self.api_key = self._load_api_key()
            self.client = self._initialize_client()
        except ValueError as e:
            self.console.print(f"[bold red]Error initializing service: {e}[/bold red]")
            raise  # Re-raise after logging

        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.glossary_path = Path(glossary_path)
        self.glossary_content: Optional[str] = None # Cache for glossary content

        # Rate Limiting Setup
        if rate_limit_rpm <= 0:
            self.console.print("[yellow]Warning: Rate limit must be positive. Disabling rate limiting.[/yellow]")
            self.sleep_duration = 0
        else:
            self.sleep_duration = 60.0 / rate_limit_rpm
            self.console.print(f"[blue]Rate limiting enabled: {rate_limit_rpm} RPM (delay: {self.sleep_duration:.2f} seconds between calls).[/blue]")


        self._ensure_output_dir()
        self.console.print(f"Input directory: '{self.input_dir}'")
        self.console.print(f"Output directory: '{self.output_dir}'")
        self.console.print(f"Glossary path: '{self.glossary_path}'")

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
            # Optional: Test connection or list models if needed
            # client.models.list()
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

    def _get_markdown_files(self, limit: Optional[int] = None) -> List[Path]:
        """Gets a list of markdown files from the input directory, optionally limited."""
        if not self.input_dir.is_dir():
            self.console.print(f"[bold red]Error: Input directory '{self.input_dir}' not found or is not a directory.[/bold red]")
            return []
        
        files = sorted(list(self.input_dir.glob("*.md"))) # Get sorted list
        
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

    def _extract_history(self, medical_text: str) -> Optional[PreviousMedicalHistory]:
        """Extracts medical history using the Gemini API."""
        glossary = self._load_glossary()
        prompt = f"""This is a clinical case text:
        --- START TEXT ---
        {medical_text}
        --- END TEXT ---

        The text is a critical care burn patient clinical case, potentially containing admission, release, and death notes. It is written in European Portuguese.

        Your task is to extract the patient's previous medical history (diseases or conditions they had *before* the current burn incident).

        Use the following glossary for potentially ambiguous Portuguese terms if needed:
        --- START GLOSSARY ---
        {glossary if glossary else "No glossary provided."}
        --- END GLOSSARY ---

        Return *only* the previous medical history structured according to the provided JSON schema. The output must be in English.
        """

        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction="You are a meticulous data scientist specializing in extracting structured medical information from clinical texts.",
                    temperature=0.1, # Slightly increased for potentially better extraction nuance
                    response_mime_type='application/json',
                    response_schema=PreviousMedicalHistory.model_json_schema(),
                ),
                # Add safety settings if needed, e.g., to block harmful content
                # safety_settings={...}
            )

            # Attempt to parse the JSON response using the Pydantic model
            # The SDK should ideally return validated data if response_schema is used,
            # but explicit validation adds robustness.
            if response.text:
                try:
                    # Parse the JSON string from the response text
                    response_data = json.loads(response.text)
                    # Validate the parsed data against the Pydantic model
                    validated_data = PreviousMedicalHistory.model_validate(response_data)
                    return validated_data
                except json.JSONDecodeError as json_err:
                    self.console.print(f"[red]Error decoding JSON response: {json_err}[/red]")
                    self.console.print(f"Raw response text: {response.text[:500]}...") # Log part of the raw response
                    return None
                except ValidationError as val_err:
                    self.console.print(f"[red]Validation Error: Extracted data does not match schema: {val_err}[/red]")
                    self.console.print(f"Raw response data: {response_data}")
                    return None
            else:
                 self.console.print("[yellow]Warning: Received empty response from API.[/yellow]")
                 return None

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

        Args:
            diseases: A list of Disease objects extracted initially.

        Returns:
            The same list of Disease objects, potentially updated with snomed_classification.
        """
        if not diseases:
            return []

        self.console.print(f"[cyan]Enriching {len(diseases)} diseases with SNOMED CT codes...[/cyan]")
        enriched_diseases = []
        for disease in diseases:
            disease_name = disease.name
            if not disease_name:
                self.console.print("[yellow]Skipping disease with missing name during SNOMED enrichment.[/yellow]")
                enriched_diseases.append(disease) # Keep the original disease object
                continue

            # self.console.print(f"  Looking up SNOMED code for: '{disease_name}'") # Verbose logging
            snomed_result = None
            try:
                # Call the imported function
                snomed_result = find_diagnosis_snomed_code(disease_name)
            except Exception as e:
                # Log errors from the lookup function itself
                self.console.print(f"[red]Error during SNOMED lookup for '{disease_name}': {e}[/red]")

            if snomed_result:
                try:
                    # Validate and create SnomedConcept
                    snomed_concept = SnomedConcept.model_validate(snomed_result)
                    disease.snomed_classification = snomed_concept # Assign to the disease object
                    # self.console.print(f"    Found: {snomed_concept.term} ({snomed_concept.sctid})") # Verbose
                except ValidationError as val_err:
                    self.console.print(f"[yellow]Warning: SNOMED result for '{disease_name}' failed validation: {val_err}. Result: {snomed_result}[/yellow]")
                    disease.snomed_classification = None # Ensure it's None if validation fails
            else:
                # self.console.print(f"    No valid SNOMED code found for '{disease_name}'") # Verbose
                disease.snomed_classification = None # Ensure it's None if not found

            enriched_diseases.append(disease)
            # Add a small delay *within* the enrichment loop if calling an external API frequently
            # time.sleep(0.5) # Example: Adjust delay as needed for the diagnosis lookup service

        return enriched_diseases

    def _save_json(self, data: PreviousMedicalHistory, input_file_path: Path):
        """Saves the extracted data, including the file-derived ID, to a JSON file."""
        output_filename = input_file_path.stem + ".json"
        output_path = self.output_dir / output_filename
        
        # Extract ID from filename
        file_id = input_file_path.stem
        
        try:
            # Convert Pydantic model to dict and add/update the ID
            # Use model_dump for Pydantic v2
            data_dict = data.model_dump(exclude_none=True) # Exclude None fields if desired
            data_dict['ID'] = file_id # Ensure ID is set correctly

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=4, ensure_ascii=False) # Use json.dump for dict

            # self.console.print(f"[green]Successfully saved: '{output_path}'[/green]") # Reduce verbosity inside loop
        except IOError as e:
            self.console.print(f"[red]Error saving JSON file '{output_path}': {e}[/red]")
        except Exception as e:
            self.console.print(f"[red]Unexpected error saving JSON '{output_path}': {e}[/red]")

    def process_files(self, limit: Optional[int] = None):
        """Processes markdown files in the input directory to extract medical history."""
        markdown_files = self._get_markdown_files(limit=limit)
        if not markdown_files:
            self.console.print("[yellow]No markdown files found to process.[/yellow]")
            return

        self.console.print(f"Found {len(markdown_files)} markdown files to process.")

        # Setup progress bar
        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeRemainingColumn(),
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
                extracted_data = self._extract_history(medical_text)
                if extracted_data is None:
                    self.console.print(f"[yellow]Failed initial extraction for '{file_path.name}'. Skipping.[/yellow]")
                    fail_count += 1; progress.advance(task); continue

                # Step 2: Enrichment
                if extracted_data.previous_diseases:
                    # Enrich the extracted diseases list in place
                    extracted_data.previous_diseases = self._enrich_diseases_with_snomed(extracted_data.previous_diseases)
                else:
                     self.console.print(f"[cyan]No previous diseases found/extracted for '{file_path.name}'. Skipping enrichment.[/cyan]")

                # Step 3: Save (includes ID addition)
                self._save_json(extracted_data, file_path)
                success_count += 1
                progress.advance(task)

                # Rate Limiting Delay (for Gemini API calls)
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
    console.print("[bold blue]Medical History Extractor[/bold blue]")

    # Define paths relative to the project root (assuming script is run from project root or similar)
    # Adjust these paths if the script location or project structure differs.
    PROJECT_ROOT = Path(__file__).resolve().parents[1] # Assumes script is in pydantic_extracter
    INPUT_DIR = PROJECT_ROOT / "data" / "output" / "markdown" / "clean"
    OUTPUT_DIR = PROJECT_ROOT / "data" / "output" / "json" / "medical_history"
    GLOSSARY_PATH = PROJECT_ROOT / "documentation" / "PT-glossario.md"

    try:
        # --- Test Run ---
        console.print("\n[bold yellow]Starting Test Run (limit=10 files)...[/bold yellow]")
        extractor_service = MedicalHistoryExtractorService(
            input_dir=str(INPUT_DIR),
            output_dir=str(OUTPUT_DIR),
            glossary_path=str(GLOSSARY_PATH),
            rate_limit_rpm=15 # Explicitly set or rely on default
        )
        extractor_service.process_files(limit=10) # Process only 10 files for testing

        # --- Optional: Full Run (Uncomment to run on all files) ---
        # console.print("\n[bold green]Starting Full Run...[/bold green]")
        # full_run_service = MedicalHistoryExtractorService(
        #     input_dir=str(INPUT_DIR),
        #     output_dir=str(OUTPUT_DIR),
        #     glossary_path=str(GLOSSARY_PATH),
        #     rate_limit_rpm=15 # Adjust if needed for full run
        # )
        # full_run_service.process_files()

    except ValueError as e:
        # Catch initialization errors (like missing API key)
        console.print(f"[bold red]Initialization failed: {e}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred during execution: {e}[/bold red]")
