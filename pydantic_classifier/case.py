from pydantic import BaseModel, Field, ValidationError
from typing import List
from enum import Enum

# --- Enums (Example - can be expanded based on common findings) ---

class OrganSystem(str, Enum):
    """Enumeration for major organ systems relevant to critical care."""
    RESPIRATORY = "Respiratory"
    CARDIOVASCULAR = "Cardiovascular"
    RENAL = "Renal"
    HEMATOLOGIC = "Hematologic"
    NEUROLOGIC = "Neurologic"
    GASTROINTESTINAL = "Gastrointestinal"
    HEPATIC = "Hepatic"
    OTHER = "Other"
    UNKNOWN = "Unknown" # Added for cases where system isn't specified

# --- Nested Models ---

class OrganicDysfunction(BaseModel):
    """
    Represents an identified organ dysfunction and the support provided.
    All fields are required.
    """
    system: OrganSystem = Field(
        description="The organ system affected by the dysfunction. Must be provided.",
    )
    dysfunction_description: str = Field(
        description="Specific description of the dysfunction (e.g., 'Acute Respiratory Failure', 'Septic Shock', 'AKI Stage 3'). Must be provided.",
    )
    support_provided: List[str] = Field(
        description="List of supports provided for this dysfunction (e.g., ['Mechanical Ventilation', 'Norepinephrine infusion', 'CRRT']). Must be provided, can be an empty list.",
    )
    provenance: str = Field(
        description="The sentences or expressions in the original text where the information was obtained. Must be provided.",
    )


class AdmissionStatus(BaseModel):
    """
    Captures the patient's state regarding organ dysfunction and ventilation at admission.
    All fields are required.
    """
    organic_dysfunctions: List[OrganicDysfunction] = Field(
        description="List of organ dysfunctions present at admission. Must be provided, can be an empty list.",
    )
    mechanical_ventilation: bool = Field(
        description="Indicates if the patient was under invasive mechanical ventilation at the time of admission. Must be provided.",
    )
    provenance: str = Field(
        description="The sentences or expressions in the original text where the information was obtained. Must be provided.",
    )


class Procedure(BaseModel):
    """
    Represents a medical or surgical procedure performed during the hospital stay.
    All fields are required.
    """
    name: str = Field(
        description="Name of the procedure (e.g., 'Escharotomy', 'Central Line Insertion', 'Skin Grafting', 'Debridement'). Must be provided.",
    )
    details: str = Field(
        description="Relevant details about the procedure (e.g., location, type, device used). Must be provided.",
    )
    provenance: str = Field(
        description="The sentences or expressions in the original text where the information was obtained. Must be provided.",
    )


class Infection(BaseModel):
    """
    Represents an infection identified during the hospital stay.
    All fields are required.
    """
    site: str = Field(
        description="Site of the infection (e.g., 'Bloodstream', 'Lungs (VAP)', 'Wound', 'Urinary Tract'). Must be provided.",
    )
    pathogen: str = Field(
        description="Identified pathogen(s), if known (e.g., 'Pseudomonas aeruginosa', 'MRSA', 'Candida albicans'). Must be provided.",
    )
    details: str = Field(
        description="Additional details like date/day of identification, resistance patterns, or treatment. Must be provided.",
    )
    provenance: str = Field(
        description="The sentences or expressions in the original text where the information was obtained. Must be provided.",
    )

# --- Main Clinical Case Model ---

class ClinicalCaseExtract(BaseModel):
    """
    Structured representation of key clinical information extracted from a burn patient's case notes.
    All fields are explicitly required. The extraction process must ensure all fields are populated.
    """
    admission_status: AdmissionStatus = Field(
        description="Patient's status regarding organ dysfunction and ventilation upon admission. Must be provided."
    )
    procedures: List[Procedure] = Field(
        description="List of significant procedures performed during the hospital stay. Must be provided, can be an empty list.",
    )
    infections: List[Infection] = Field(
        description="List of infections identified during the hospital stay. Must be provided, can be an empty list.",
    )
    other_relevant_features: List[str] = Field(
        description="List of other notable clinical features, events, or complications mentioned. Must be provided, can be an empty list.",
    )
    provenance: str = Field(
        description="The sentences or expressions in the original text where the overall case information was obtained or summarized. Must be provided.",
    )

# --- Example Usage & Basic Tests ---

if __name__ == "__main__":
    from rich.console import Console
    console = Console()

    console.print("[bold cyan]--- Testing Pydantic Model Definitions (Strict: No Defaults) ---[/bold cyan]")

    # Test Case 1: Minimum Required Data (Empty lists/strings where applicable)
    # Since defaults are removed, we MUST provide all fields.
    console.print("\n[yellow]Test Case 1: Minimum Required Data[/yellow]")
    try:
        case1_data = {
            "admission_status": {
                "organic_dysfunctions": [], # Must provide empty list
                "mechanical_ventilation": False, # Must provide boolean
                "provenance": "Admission status not detailed." # Must provide string
            },
            "procedures": [], # Must provide empty list
            "infections": [], # Must provide empty list
            "other_relevant_features": [], # Must provide empty list
            "provenance": "Minimal case summary." # Must provide string
        }
        case1 = ClinicalCaseExtract(**case1_data)
        console.print("[green]Case 1 Validation Successful:[/green]")
        console.print(case1.model_dump_json(indent=2))
        assert case1.admission_status.mechanical_ventilation is False
        assert case1.admission_status.organic_dysfunctions == []
        assert case1.procedures == []
        assert case1.infections == []
        assert case1.other_relevant_features == []
        console.print("[bold green]Assertions Passed![/bold green]")
    except ValidationError as e:
        console.print(f"[bold red]Case 1 Validation Failed:[/bold red]")
        console.print(e) # Show Pydantic validation error details
    except Exception as e:
        console.print(f"[bold red]Case 1 Unexpected Error:[/bold red]\n{e}")


    # Test Case 2: More complete data (Should still work)
    console.print("\n[yellow]Test Case 2: More Complete Data[/yellow]")
    try:
        case2_data = {
            "admission_status": {
                "organic_dysfunctions": [
                    {
                        "system": OrganSystem.RESPIRATORY, # Use Enum member
                        "dysfunction_description": "ARDS",
                        "support_provided": ["Mechanical Ventilation", "PEEP 12"],
                        "provenance": "Admitted with severe ARDS requiring intubation."
                    },
                    {
                        "system": OrganSystem.CARDIOVASCULAR, # Use Enum member
                        "dysfunction_description": "Septic Shock",
                        "support_provided": ["Norepinephrine 0.2 mcg/kg/min"],
                        "provenance": "BP was 70/40, started on norepinephrine."
                    }
                ],
                "mechanical_ventilation": True,
                "provenance": "Patient intubated in ER prior to admission."
            },
            "procedures": [
                {"name": "Central Line Insertion", "details": "Right IJ", "provenance": "Central line placed on admission."},
                {"name": "Escharotomy", "details": "Bilateral lower extremities", "provenance": "Circumferential burns noted, escharotomies performed."}
            ],
            "infections": [
                {"site": "Bloodstream", "pathogen": "Pseudomonas aeruginosa", "details": "Day 5, sensitive to Meropenem", "provenance": "Blood cultures from day 5 grew Pseudomonas."}
            ],
            "other_relevant_features": [
                "History of Diabetes Mellitus Type 2",
                "Developed Acute Kidney Injury on Day 7"
            ],
            "provenance": "Summary of hospital course."
        }
        case2 = ClinicalCaseExtract(**case2_data)
        console.print("[green]Case 2 Validation Successful:[/green]")
        console.print(case2.model_dump_json(indent=2))
        assert case2.admission_status.mechanical_ventilation is True
        assert len(case2.admission_status.organic_dysfunctions) == 2
        assert len(case2.procedures) == 2
        assert len(case2.infections) == 1
        assert len(case2.other_relevant_features) == 2
        console.print("[bold green]Assertions Passed![/bold green]")
    except ValidationError as e:
        console.print(f"[bold red]Case 2 Validation Failed:[/bold red]")
        console.print(e)
    except Exception as e:
        console.print(f"[bold red]Case 2 Unexpected Error:[/bold red]\n{e}")

    # Test Case 3: Intentionally Missing Field (Should Fail Validation)
    console.print("\n[yellow]Test Case 3: Intentionally Missing Field (Expect Validation Error)[/yellow]")
    try:
        case3_data = {
            "admission_status": {
                "organic_dysfunctions": [],
                "mechanical_ventilation": False,
                "provenance": "Admission status."
                # Missing 'provenance' inside admission_status
            },
            "procedures": [],
            "infections": [],
            "other_relevant_features": [],
            # Missing top-level 'provenance'
            "provenance": "Test case 3 provenance." # Let's make this one pass, but miss one inside admission_status
        }
        # We expect this to fail because admission_status.provenance is missing
        case3_missing_admission_provenance = {
             "admission_status": {
                "organic_dysfunctions": [],
                "mechanical_ventilation": False,
                # "provenance": "Admission status." # Intentionally missing
            },
            "procedures": [],
            "infections": [],
            "other_relevant_features": [],
            "provenance": "Test case 3 provenance."
        }
        case3 = ClinicalCaseExtract(**case3_missing_admission_provenance)
        # If it reaches here, the validation unexpectedly passed
        console.print("[bold red]Case 3 Validation Unexpectedly Succeeded:[/bold red]")
        console.print(case3.model_dump_json(indent=2))
    except ValidationError as e:
        console.print(f"[bold green]Case 3 Validation Failed as Expected:[/bold green]")
        # Print specific missing fields for clarity
        missing_fields = [err['loc'] for err in e.errors()]
        console.print(f"Missing fields detected: {missing_fields}")
        # console.print(e) # Optionally print full error details
    except Exception as e:
        console.print(f"[bold red]Case 3 Unexpected Error:[/bold red]\n{e}")


    console.print("\n[bold cyan]--- Model Testing Complete ---[/bold cyan]")
