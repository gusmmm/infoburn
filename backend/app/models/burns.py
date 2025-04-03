"""
Database models for burns data.

This module contains the MongoDB data models for burns data,
matching the Pydantic models used for validation.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum


class BurnMechanism(str, Enum):
    """Enumeration of burn mechanisms"""
    HEAT = "Heat"
    ELECTRICAL = "Electrical discharge"
    FRICTION = "Friction"
    CHEMICALS = "Chemicals"
    RADIATION = "Radiation"
    UNKNOWN = "unknown or unspecified"


class AccidentType(str, Enum):
    """Enumeration of accident types"""
    DOMESTIC = "domestic"
    WORKPLACE = "workplace"
    OTHER = "other"


class BurnLocation(str, Enum):
    """Enumeration of burn locations on the body"""
    HEAD = "head"
    NECK = "neck"
    FACE = "face"
    UPPER_EXTREMITY = "upper extremity"
    HAND = "hand"
    TRUNK = "trunk"
    THORAX = "thorax"
    ABDOMEN = "abdomen"
    BACK = "back of trunk"
    PERINEUM = "perineum"
    LOWER_EXTREMITY = "lower extremity"
    FOOT = "foot"


class BurnDepth(str, Enum):
    """Enumeration of burn depth classifications"""
    FIRST_DEGREE = "1st_degree"
    SECOND_DEGREE_PARTIAL = "2nd_degree_partial"
    SECOND_DEGREE_FULL = "2nd_degree_full"
    THIRD_DEGREE = "3rd_degree"
    FOURTH_DEGREE = "4th_degree"
    UNSPECIFIED = "unspecified"


class Laterality(str, Enum):
    """Enumeration of body laterality"""
    LEFT = "left"
    RIGHT = "right"
    BILATERAL = "bilateral"
    UNSPECIFIED = "unspecified"


class BurnInjury(BaseModel):
    """
    Model for individual burn injuries with location, laterality, depth and circumferential status.
    """
    location: BurnLocation = Field(description="Anatomical location of the burn")
    laterality: Laterality = Field(description="Side of the body affected by the burn")
    depth: BurnDepth = Field(description="Depth of the burn injury")
    circumferencial: bool = Field(description="Indicates if the burn encircles the body part completely")


class BurnsModel(BaseModel):
    """
    Database model for burns data.
    Corresponds to the 'burns' collection in MongoDB.
    """
    patient_id: str = Field(description="ID of the patient this burns data belongs to.")
    tbsa: float = Field(description="Total Body Surface Area affected by burns in percentage.")
    mechanism: BurnMechanism = Field(description="Mechanism of burn injuries.")
    type_of_accident: AccidentType = Field(description="Type of accident: domestic, workplace, or other.")
    agent: str = Field(description="The specific agent that caused the burn injury (e.g., fire, gas, petrol, chemical name).")
    wildfire: bool = Field(description="Indicates if the burn was caused by a wildfire (e.g., forest fire, bushfire, grass fire, hill fire, prairie fire).")
    bonfire: bool = Field(description="Indicates if the burn injuries are related to a bonfire or a camp fire.")
    fireplace: bool = Field(description="Indicates if the burn injuries are related to a domestic fireplace.")
    violence: bool = Field(description="Indicates if the burn was inflicted in a violence context.")
    suicide_attempt: bool = Field(description="Indicates if the burn was specifically described as a suicide attempt.")
    escharotomy: bool = Field(description="Indicates if the patient underwent emergency escharotomy.")
    associated_trauma: List[str] = Field(description="List of trauma lesions associated with the burn injuries.")
    burns: List[BurnInjury] = Field(description="Detailed information about individual burn injuries.")

    @field_validator("tbsa")
    def validate_tbsa(cls, value):
        """
        Validate the tbsa field to ensure it is between 0 and 100.
        """
        if value is not None and not (0 <= value <= 100):
            raise ValueError("TBSA must be between 0 and 100.")
        return value

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "patient_id": "12345",
                    "tbsa": 15.5,
                    "mechanism": "Heat",
                    "type_of_accident": "domestic",
                    "agent": "boiling water",
                    "wildfire": False,
                    "bonfire": False,
                    "fireplace": True,
                    "violence": False,
                    "suicide_attempt": False,
                    "escharotomy": False,
                    "associated_trauma": [],
                    "burns": [
                        {
                            "location": "hand",
                            "laterality": "right",
                            "depth": "2nd_degree_partial",
                            "circumferencial": False
                        }
                    ]
                }
            ]
        }
    }