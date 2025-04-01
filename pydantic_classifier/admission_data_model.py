# let's create a pydantic model for the Google Sheets extraction
# the goal is to extract the data from the Google Sheets and convert it into a pydantic model
# so that it can be saved as a typed json file

from typing import Optional, List
from datetime import datetime, date
import logfire
from core_tools.key_manager import KeyManager
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
import re

key_manager = KeyManager()
PYDANTIC_API_KEY = key_manager.get_key("PYDANTIC_API_KEY")

logfire.configure(token=PYDANTIC_API_KEY)
logfire.info('Hello from {place}! Timestamp: {timestamp}',
              place='Porto',
              timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
logfire.instrument_pydantic()  

class Gender(str, Enum):
    """Enumeration for patient gender"""
    MALE = "M"
    FEMALE = "F"

class AdmissionDataPatient(BaseModel):
    """
    Pydantic model for Burns Critical Care Unit patient data.
    Validates data extracted from CSV files.
    """
    ID: str = Field(
        description="Patient admission identifier (4-5 digits)",
        pattern=r"^\d{4,5}$"
    )
    
    processo: Optional[int] = Field(
        None,
        description="Patient file number"
    )
    
    nome: Optional[str] = Field(
        None,
        description="Full name of the patient"
    )
    
    data_ent: Optional[date] = Field(
        None,
        description="Date of admission to the Burns Critical Care Unit"
    )
    
    data_alta: Optional[date] = Field(
        None,
        description="Release date from the Burns Critical Care Unit"
    )
    
    sexo: Optional[Gender] = Field(
        None,
        description="Patient gender (M or F)"
    )
    
    data_nasc: Optional[date] = Field(
        None,
        description="Patient's birth date"
    )
    
    destino: Optional[str] = Field(
        None,
        description="Discharge destination after release from the unit"
    )
    
    origem: Optional[str] = Field(
        None,
        description="Origin facility/location before admission to the unit"
    )
    
    @field_validator('ID')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Ensure ID is a 4-5 digit string and properly formatted"""
        if not v or not re.match(r'^\d{4,5}$', v):
            raise ValueError('ID must be a 4-5 digit string')
        return v
    
    @model_validator(mode='after')
    def validate_dates(self) -> 'AdmissionDataPatient':
        """Validate that admission date is before release date if both are present"""
        if self.data_ent and self.data_alta and self.data_ent > self.data_alta:
            raise ValueError("Admission date must be before release date")
        return self
    
    @model_validator(mode='after')
    def validate_age(self) -> 'AdmissionDataPatient':
        """Validate that birth date is before admission date if both are present"""
        if self.data_nasc and self.data_ent and self.data_nasc > self.data_ent:
            raise ValueError("Birth date must be before admission date")
        return self

    class Config:
        """Configuration for the BurnsPatient model"""
        from_attributes = True
        validate_assignment = True
        json_schema_extra = {
            "examples": [
                {
                    "ID": "12345",
                    "processo": 987654,
                    "nome": "João Silva",
                    "data_ent": "15-06-2023",
                    "data_alta": "30-06-2023",
                    "sexo": "M",
                    "data_nasc": "01-01-1980",
                    "destino": "Home",
                    "origem": "Emergency Department"
                }
            ]
        }