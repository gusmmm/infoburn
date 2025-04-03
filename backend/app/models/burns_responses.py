"""
Burns Response Models

This module defines Pydantic models specifically for API responses related to burns data.
These models define how burn data is presented in API responses, ensuring consistent
and well-structured outputs across the application.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import Field

from backend.app.models.burns import BurnMechanism, AccidentType, BurnInjury
from backend.app.models.base import InfoBurnBaseModel


class BurnsPatientResponse(InfoBurnBaseModel):
    """
    Response model for burns patient data.
    
    This model extends the base BurnsPatientData model to include additional
    fields that are needed for API responses, such as document ID and timestamps.
    It's designed specifically for returning burn records through the API.
    """
    # MongoDB ObjectId (converted to string) - using 'id' not '_id' to comply with Pydantic rules
    id: str = Field(description="MongoDB document ID")
    
    # Core fields from BurnsPatientData
    ID: str = Field(description="Patient identifier")
    tbsa: Optional[float] = Field(None, description="Total Body Surface Area affected by burns (%)")
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
    
    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Record creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Record last update timestamp")
    
    # Reference to admission data (if linked)
    admission_id: Optional[str] = Field(None, description="Reference to related admission record")
    
    class Config:
        """Configuration for the BurnsPatientResponse model"""
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "ID": "12345",
                "tbsa": 15.5,
                "mechanism": "Heat",
                "type_of_accident": "domestic",
                "agent": "hot water",
                "wildfire": False,
                "bonfire": False,
                "fireplace": False,
                "violence": False,
                "suicide_attempt": False,
                "escharotomy": False,
                "associated_trauma": ["head injury"],
                "burns": [
                    {
                        "location": "trunk",
                        "laterality": "bilateral",
                        "depth": "2nd_degree_partial",
                        "circumferencial": False
                    }
                ],
                "created_at": "2023-01-01T12:00:00",
                "updated_at": "2023-01-01T12:00:00",
                "admission_id": "507f1f77bcf86cd799439012"
            }
        }


class BurnsStatisticsResponse(InfoBurnBaseModel):
    """
    Response model for burns statistics data.
    
    This model is designed to provide structured statistical information
    about burn records in the database, including counts, distributions,
    and averages.
    """
    total_count: int = Field(description="Total number of burn records")
    mechanism_distribution: Dict[str, int] = Field(description="Distribution of burn mechanisms")
    accident_type_distribution: Dict[str, int] = Field(description="Distribution of accident types")
    average_tbsa: Optional[float] = Field(None, description="Average TBSA percentage across all records")
    domestic_accident_percentage: Optional[float] = Field(None, description="Percentage of domestic accidents")
    violence_count: int = Field(0, description="Number of burns related to violence")
    
    class Config:
        """Configuration for the BurnsStatisticsResponse model"""
        json_schema_extra = {
            "example": {
                "total_count": 150,
                "mechanism_distribution": {
                    "Heat": 120,
                    "Chemicals": 15,
                    "Electrical discharge": 10,
                    "Friction": 5
                },
                "accident_type_distribution": {
                    "domestic": 100,
                    "workplace": 40,
                    "other": 10
                },
                "average_tbsa": 17.3,
                "domestic_accident_percentage": 66.7,
                "violence_count": 5
            }
        }


# Test the models if this file is run directly
if __name__ == "__main__":
    import json
    from pydantic import TypeAdapter
    
    # Create a sample burn injury
    burn_injury = BurnInjury(
        location="trunk",
        laterality="bilateral",
        depth="2nd_degree_partial",
        circumferencial=False
    )
    
    # Create a sample burns patient response
    response = BurnsPatientResponse(
        id="507f1f77bcf86cd799439011",
        ID="12345",
        tbsa=15.5,
        mechanism="Heat",
        type_of_accident="domestic",
        agent="hot water",
        associated_trauma=["head injury"],
        burns=[burn_injury],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Print the response as JSON
    print("Burns Patient Response:")
    print(response.model_dump_json(indent=2))
    
    # Create a sample statistics response
    stats = BurnsStatisticsResponse(
        total_count=150,
        mechanism_distribution={
            "Heat": 120,
            "Chemicals": 15,
            "Electrical discharge": 10,
            "Friction": 5
        },
        accident_type_distribution={
            "domestic": 100,
            "workplace": 40,
            "other": 10
        },
        average_tbsa=17.3,
        domestic_accident_percentage=66.7,
        violence_count=5
    )
    
    # Print the statistics as JSON
    print("\nBurns Statistics Response:")
    print(stats.model_dump_json(indent=2))
    
    # Test deserialization from JSON
    json_data = response.model_dump_json()
    deserialized = BurnsPatientResponse.model_validate_json(json_data)
    print("\nDeserialization successful:", deserialized.ID == "12345")