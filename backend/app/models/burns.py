"""
Burns Model

This module defines the Pydantic models for burns data in the application.
"""

from enum import Enum
from typing import List, Optional
from pydantic import Field

from backend.app.models.base import InfoBurnBaseModel


class BurnMechanism(str, Enum):
    """Possible mechanisms of burn injuries"""
    HEAT = "Heat"
    ELECTRICAL = "Electrical discharge"
    FRICTION = "Friction"
    CHEMICALS = "Chemicals"
    RADIATION = "Radiation"
    UNKNOWN = "unknown or unspecified"


class AccidentType(str, Enum):
    """Types of accidents causing the burns"""
    DOMESTIC = "domestic"
    WORKPLACE = "workplace"
    OTHER = "other"


class BurnLocation(str, Enum):
    """Possible locations of burn injuries on body"""
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
    """Classification of burn depths"""
    FIRST_DEGREE = "1st_degree"
    SECOND_DEGREE_PARTIAL = "2nd_degree_partial"
    SECOND_DEGREE_FULL = "2nd_degree_full"
    THIRD_DEGREE = "3rd_degree"
    FOURTH_DEGREE = "4th_degree"
    UNSPECIFIED = "unspecified"


class Laterality(str, Enum):
    """Directional specification for burns"""
    LEFT = "left"
    RIGHT = "right"
    BILATERAL = "bilateral"
    UNSPECIFIED = "unspecified"


class BurnInjury(InfoBurnBaseModel):
    """Model for individual burn injuries"""
    location: BurnLocation
    laterality: Laterality
    depth: BurnDepth
    circumferencial: bool = False


class BurnsPatientData(InfoBurnBaseModel):
    """Model for burns patient data"""
    ID: str = Field(description="Unique identifier for the patient")
    tbsa: Optional[float] = Field(None, description="Total Body Surface Area affected by burns in percentage")
    mechanism: Optional[BurnMechanism] = Field(None, description="Mechanism of burn injuries")
    type_of_accident: Optional[AccidentType] = Field(None, description="Type of accident")
    agent: Optional[str] = Field(None, description="The specific agent causing the burn")
    wildfire: bool = Field(False, description="Indicates if burn was caused by a wildfire")
    bonfire: bool = Field(False, description="Indicates if burn injuries are related to a bonfire")
    fireplace: bool = Field(False, description="Indicates if burn injuries are related to a domestic fireplace")
    violence: bool = Field(False, description="Indicates if burn was inflicted in a violence context")
    suicide_attempt: bool = Field(False, description="Indicates if burn was result of a suicide attempt")
    escharotomy: bool = Field(False, description="Indicates if escharotomy was performed")
    associated_trauma: Optional[List[str]] = Field(None, description="List of associated traumas")
    burns: Optional[List[BurnInjury]] = Field(None, description="List of individual burn injuries")