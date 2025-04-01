from datetime import datetime, date
from typing import Optional
from .base import InfoBurnBaseModel, PyObjectId
from pydantic import Field, field_validator, model_validator, ConfigDict
from enum import Enum
import re

class Gender(str, Enum):
    """Enumeration for patient gender"""
    MALE = "M"
    FEMALE = "F"

class AdmissionCreate(InfoBurnBaseModel):
    """Schema for creating new admissions"""
    ID: str = Field(
        description="Patient admission identifier (4-5 digits)",
        pattern=r"^\d{4,5}$"
    )
    processo: Optional[int] = Field(None, description="Patient file number")
    nome: Optional[str] = Field(None, description="Full name of the patient")
    data_ent: Optional[date] = Field(None, description="Date of admission")
    data_alta: Optional[date] = Field(None, description="Release date")
    sexo: Optional[Gender] = Field(None, description="Patient gender (M or F)")
    data_nasc: Optional[date] = Field(None, description="Patient's birth date")
    destino: Optional[str] = Field(None, description="Discharge destination")
    origem: Optional[str] = Field(None, description="Origin facility/location")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ID": "3108",
                "processo": 12345,
                "nome": "João Silva",
                "data_ent": "2025-04-01",
                "data_alta": "2025-04-01",
                "sexo": "M",
                "data_nasc": "1980-01-01",
                "destino": "Home",
                "origem": "Emergency"
            }
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
    def validate_dates(self) -> 'AdmissionCreate':
        """Validate that admission date is before release date if both are present"""
        if self.data_ent and self.data_alta and self.data_ent > self.data_alta:
            raise ValueError("Admission date must be before release date")
        return self
    
    @model_validator(mode='after')
    def validate_age(self) -> 'AdmissionCreate':
        """Validate that birth date is before admission date if both are present"""
        if self.data_nasc and self.data_ent and self.data_nasc > self.data_ent:
            raise ValueError("Birth date must be before admission date")
        return self

# Schema for responses (includes _id)
class AdmissionResponse(AdmissionCreate):
    """Schema for admission responses, includes MongoDB id"""
    id: PyObjectId = Field(alias="_id")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={
            date: lambda d: d.isoformat() if d else None
        }
    )