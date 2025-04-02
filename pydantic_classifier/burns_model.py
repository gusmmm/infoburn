from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum

class BurnMechanism(str, Enum):
    HEAT = "Heat"
    ELECTRICAL = "Electrical discharge"
    FRICTION = "Friction"
    CHEMICALS = "Chemicals"
    RADIATION = "Radiation"
    UNKNOWN = "unknown or unspecified"

class AccidentType(str, Enum):
    DOMESTIC = "domestic"
    WORKPLACE = "workplace"
    OTHER = "other"

class BurnLocation(str, Enum):
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
    FIRST_DEGREE = "1st_degree"
    SECOND_DEGREE_PARTIAL = "2nd_degree_partial" 
    SECOND_DEGREE_FULL = "2nd_degree_full"
    THIRD_DEGREE = "3rd_degree"
    FOURTH_DEGREE = "4th_degree"
    UNSPECIFIED = "unspecified"

class BurnInjury(BaseModel):
    """
    Model for individual burn injuries with location, laterality, depth and circumferential status.
    """
    location: BurnLocation
    laterality: Optional[str] = Field(description="Side of the body affected by the burn.")
    depth: BurnDepth = Field(description="Depth of the burn injury.")
    circumferencial: Optional[bool] = Field(description="Indicates if the burn encircles the body part completely.")

    @field_validator("laterality")
    def validate_laterality(cls, value):
        if value is None:
            return value
        allowed_values = ["left", "right", "bilateral", "unspecified"]
        if value not in allowed_values:
            raise ValueError(f"Laterality must be one of: {', '.join(allowed_values)}")
        return value

class BurnsModel(BaseModel):
    """
    Base model for burns data.
    """
    tbsa: Optional[float] = Field(description="Total Body Surface Area affected by burns in percentage.")
    mechanism: Optional[BurnMechanism] = Field(description="Mechanism of burn injuries.")
    type_of_accident: Optional[AccidentType] = Field(description="Type of accident: domestic, workplace, or other.")
    agent: Optional[str] = Field(description="The specific agent that caused the burn injury (e.g., fire, gas, petrol, chemical name).")
    wildfire: Optional[bool] = Field(description="Indicates if the burn was caused by a wildfire (e.g., forest fire, bushfire, grass fire, hill fire, prairie fire).")
    bonfire: Optional[bool] = Field(description="Indicates if the burn injuries are related to a bonfire or a camp fire.")
    fireplace: Optional[bool] = Field(description="Indicates if the burn injuries are related to a domestic fireplace.")
    violence: Optional[bool] = Field(description="Indicates if the burn was inflicted in a violence context.")
    suicide_attempt: Optional[bool] = Field(description="Indicates if the burn was specifically described as a suicide attempt.")
    escharotomy: Optional[bool] = Field(description="Indicates if the patient underwent emergency escharotomy.")
    associated_trauma: Optional[List[str]] = Field(description="List of trauma lesions associated with the burn injuries.")
    burns: Optional[List[BurnInjury]] = Field(description="Detailed information about individual burn injuries.")

    @field_validator("tbsa")
    def validate_tbsa(cls, value):
        """
        Validate the tbsa field to ensure it is between 0 and 100.
        """
        if value is not None and not (0 <= value <= 100):
            raise ValueError("TBSA must be between 0 and 100.")
        return value

