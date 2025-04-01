from datetime import datetime, date
from typing import Optional
from .base import InfoBurnBaseModel, PyObjectId
from pydantic import Field, field_validator, model_validator, ConfigDict
from enum import Enum
import re

class AdmissionModel(InfoBurnBaseModel):
    """
    Represents a patient admission in the burns unit.
    """
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
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
    sexo: Optional[str] = Field(
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
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={
            date: lambda d: d.isoformat() if d else None
        }
    )
    
    @field_validator('ID')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Ensure ID is a 4-5 digit string and properly formatted"""
        if not v or not re.match(r'^\d{4,5}$', v):
            raise ValueError('ID must be a 4-5 digit string')
        return v
    
    @model_validator(mode='after')
    def validate_dates(self) -> 'AdmissionModel':
        """Validate that admission date is before release date if both are present"""
        if self.data_ent and self.data_alta and self.data_ent > self.data_alta:
            raise ValueError("Admission date must be before release date")
        return self
    
    @model_validator(mode='after')
    def validate_age(self) -> 'AdmissionModel':
        """Validate that birth date is before admission date if both are present"""
        if self.data_nasc and self.data_ent and self.data_nasc > self.data_ent:
            raise ValueError("Birth date must be before admission date")
        return self

    def model_dump(self, *args, **kwargs):
        """Override model_dump to convert dates to ISO format strings"""
        dump = super().model_dump(*args, **kwargs)
        # Convert dates to ISO format strings for MongoDB storage
        for field in ['data_ent', 'data_alta', 'data_nasc']:
            if dump.get(field):
                dump[field] = dump[field].isoformat()
        return dump
    
    @classmethod
    def from_mongo(cls, data):
        """Convert MongoDB data back to model instance"""
        if not data:
            return None
        
        # Convert ISO format strings back to dates
        for field in ['data_ent', 'data_alta', 'data_nasc']:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field]).date()
        
        return cls(**data)

# Rebuild model to resolve forward references
AdmissionModel.model_rebuild()