from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum
from datetime import date

class Condition(BaseModel):
    """
    Model for representing a pathologic condition or disease from a patient's medical history.
    """
    name: str = Field(
        description="Name of the condition or disease (e.g., 'Diabetes Mellitus', 'Hypertension')"
    )
    onset_year: int = Field(
        description="Year when the condition was first diagnosed or began, if known"
    )
    duration_years: float = Field(
        description="Duration of the condition in years, if specified instead of onset year"
    )
    notes: str = Field(
        None,
        description="Additional details about the condition from the medical text"
    )
    
    @field_validator('onset_year')
    def validate_onset_year(cls, v):
        """Validate that onset year is reasonable"""
        if v is not None and (v < 1900 or v > date.today().year):
            raise ValueError(f"Onset year {v} is outside reasonable range")
        return v

class MedicationFrequency(str, Enum):
    """Enumeration of common medication frequencies"""
    ONCE_DAILY = "once_daily"
    TWICE_DAILY = "twice_daily" 
    THREE_TIMES_DAILY = "three_times_daily"
    FOUR_TIMES_DAILY = "four_times_daily"
    WEEKLY = "weekly"
    AS_NEEDED = "as_needed"
    OTHER = "other"

class Medication(BaseModel):
    """
    Model for representing a medication the patient was taking before admission.
    """
    name: str = Field(
        description="Name of the medication (e.g., 'Metformin', 'Lisinopril')"
    )
    dosage: str = Field(
        description="Dosage amount (e.g., '500mg', '10mg')"
    )
    frequency: MedicationFrequency = Field(
        description="How often the medication is taken"
    )
    frequency_other: str = Field(
        description="Description of frequency if not one of the standard options"
    )
    notes: str = Field(
        description="Additional details about the medication from the medical text"
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
    conditions: List[Condition] = Field(
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

