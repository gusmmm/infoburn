from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum
from datetime import date

# This module defines models for representing a patient's medical history,
# including conditions, medications, and surgeries.
class SnomedConcept(BaseModel):
    """
    Represents a SNOMED-CT concept for standardized terminology.
    """
    sctid: str = Field(description="The unique SNOMED CT Identifier (SCTID).")
    term: str = Field(description="The preferred human-readable term for the SCTID.")


# class DieaseaseCategory(str, Enum)
# This enum classifies various disease categories based on the ICD-11 classification.
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
# This class represents a disease or condition with its name and category.
# It is used to classify diseases based on the ICD-11 classification.
class Disease(BaseModel):
    name: str = Field(description="The name of the disease or condition as extracted.")
    category: DiseaseCategory = Field(
        default=DiseaseCategory.UNKNOWN, # Default if Gemini doesn't provide it
        description="The category of the disease based on standard classifications."
    )
    snomed_classification: Optional[SnomedConcept] = Field( # Added field
        None, description="SNOMED-CT classification for the disease name."
    )
    provenance: str = Field(description="The original pieces of text you used to extract the disease and any additional notes or comments about the disease.")


class PreviousMedicalHistory(BaseModel):
    ID: Optional[str] = Field(None, description="Patient identifier, derived from the source filename.") # Keep optional here, set in _save_json
    previous_diseases: List[Disease] = Field(description="A list of diseases or conditions the patient had prior to the current admission.")

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


class Medication(BaseModel):
    """
    Model for representing a medication the patient was taking before admission,
    including SNOMED-CT classification for interoperability.
    """
    name: str = Field(
        description="Name of the medication (e.g., 'Metformin', 'Lisinopril'). "
                    "This is typically the generic or brand name found in the text.",
        examples=["Lisinopril"]
    )
    dosage: str = Field(
        description="Dosage amount and unit (e.g., '500mg', '10mg', '2 puffs').",
        examples=["10mg"]
    )
    frequency: MedicationFrequency = Field(
        description="How often the medication is taken, using predefined codes."
    )
    # Made frequency_other, assuming it's only relevant if frequency is OTHER
    frequency_other: str = Field(
        description="Description of frequency if 'Other' is selected in the frequency field."
    )
    # Made notes , as they might not always be present
    notes: str = Field(
        description="Additional details or context about the medication extracted "
                    "from the medical text (e.g., 'for hypertension', 'patient stopped 2 weeks ago')."
    )
    # --- NEW FIELD for SNOMED-CT Classification ---
    snomed_classification: SnomedConcept = Field(
        description="SNOMED-CT classification representing the primary therapeutic or "
                    "pharmacological class of the medication (e.g., ACE inhibitor, Biguanide). "
                    "This field links the specific medication name to a standardized clinical concept "
                    "for categorization and interoperability. Use concepts representing classes, "
                    "not the specific medication product itself unless necessary."
    )

class Surgery(BaseModel):
    """
    Model for representing a previous surgery from a patient's medical history.
    """
    name: str = Field(
        description="Name or type of surgery (e.g., 'Appendectomy', 'Knee Replacement')"
    )
    year: int = Field(
        description="Year when the surgery was performed, if known"
    )
    location: str = Field(
        description="Hospital or facility where surgery was performed, if specified"
    )
    notes: str = Field(
        description="Additional details about the surgery from the medical text"
    )
    
    @field_validator('year')
    def validate_year(cls, v):
        """Validate that surgery year is reasonable"""
        if v is not None and (v < 1900 or v > date.today().year):
            raise ValueError(f"Surgery year {v} is outside reasonable range")
        return v

class MedicalHistory(BaseModel):
    """
    Comprehensive model for a patient's medical history including conditions,
    medications, and surgeries.
    """
    diseases: List[Disease] = Field(
        default_factory=list,
        description="List of previous pathologic conditions or diseases"
    )
    medications: List[Medication] = Field(
        default_factory=list,
        description="List of medications taken before admission"
    )
    surgeries: List[Surgery] = Field(
        default_factory=list,
        description="List of previous surgeries"
    )
    has_allergies: bool = Field(
        description="Whether the patient has any noted allergies"
    )
    allergies: List[str] = Field(
        description="List of patient's allergies, if specified"
    )
    notable_family_history: str = Field(
        description="Notable family medical history if mentioned"
    )
    notes: str = Field(
        description="Additional relevant medical history details not captured elsewhere"
    )

