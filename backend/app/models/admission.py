from datetime import datetime, date
from typing import Optional
from .base import InfoBurnBaseModel, PyObjectId
from pydantic import Field, field_validator, model_validator
from enum import Enum
import re

class Gender(str, Enum):
    """Enumeration for patient gender"""
    MALE = "M"
    FEMALE = "F"

class AdmissionModel(InfoBurnBaseModel):
    """
    Represents a patient admission in the burns unit.
    
    Attributes:
        ID: Unique identifier for the admission (MongoDB ObjectId with alias _id)
        processo: Patient file number
        nome: Full name of the patient
        data_ent: Date of admission to the Burns Critical Care Unit
        data_alta: Release date from the Burns Critical Care Unit
        sexo: Patient gender (M or F)
        data_nasc: Patient's birth date
        destino: Discharge destination after release from the unit
        origem: Origin facility/location before admission to the unit
    """
    ID: PyObjectId = Field(
        alias='_id',
        description="Unique identifier for the admission"
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

# Rebuild model to resolve forward references
AdmissionModel.model_rebuild()