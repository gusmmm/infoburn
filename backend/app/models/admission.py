from datetime import date, datetime
from typing import Optional, List
from pydantic import Field, field_validator, model_validator, ConfigDict
from enum import Enum
import re
import json
from .base import InfoBurnBaseModel, PyObjectId

class Gender(str, Enum):
    """Enumeration for patient gender"""
    MALE = "M"
    FEMALE = "F"

class AdmissionBase(InfoBurnBaseModel):
    """Base model for admissions with common fields"""
    ID: str = Field(description="Patient admission identifier (4-5 digits)", pattern=r"^\d{4,5}$")
    processo: Optional[int] = Field(None, description="Patient file number")
    nome: Optional[str] = Field(None, description="Full name of the patient")
    data_ent: Optional[date] = Field(None, description="Date of admission")
    data_alta: Optional[date] = Field(None, description="Release date")
    sexo: Optional[Gender] = Field(None, description="Patient gender (M or F)")
    data_nasc: Optional[date] = Field(None, description="Patient's birth date")
    destino: Optional[str] = Field(None, description="Discharge destination")
    origem: Optional[str] = Field(None, description="Origin facility/location")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    @field_validator('ID')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Ensure ID is a 4-5 digit string and properly formatted"""
        if not v or not re.match(r'^\d{4,5}$', v):
            raise ValueError('ID must be a 4-5 digit string')
        return v
    
    @model_validator(mode='after')
    def validate_dates(self) -> 'AdmissionBase':
        """Validate that admission date is before release date if both are present"""
        if self.data_ent and self.data_alta and self.data_ent > self.data_alta:
            raise ValueError("Admission date must be before release date")
        return self
    
    @model_validator(mode='after')
    def validate_age(self) -> 'AdmissionBase':
        """Validate that birth date is before admission date if both are present"""
        if self.data_nasc and self.data_ent and self.data_nasc > self.data_ent:
            raise ValueError("Birth date must be before admission date")
        return self

    def model_dump_json(self, **kwargs) -> str:
        """Custom JSON serialization"""
        data = self.model_dump()
        # Convert dates to ISO format
        for field in ['data_ent', 'data_alta', 'data_nasc']:
            if value := data.get(field):
                data[field] = value.isoformat()
        return json.dumps(data, **kwargs)

class AdmissionCreate(AdmissionBase):
    """Schema for creating new admissions"""
    pass

class AdmissionUpdate(InfoBurnBaseModel):
    """
    Model for updating an existing admission record.
    
    This model defines fields that can be updated in an existing admission record.
    All fields are optional since an update may only modify specific fields.
    """
    processo: Optional[int] = Field(None, description="Patient file number")
    nome: Optional[str] = Field(None, description="Full name of the patient")
    data_ent: Optional[date] = Field(None, description="Date of admission")
    data_alta: Optional[date] = Field(None, description="Release date")
    sexo: Optional[Gender] = Field(None, description="Patient gender (M or F)")
    data_nasc: Optional[date] = Field(None, description="Patient's birth date")
    destino: Optional[str] = Field(None, description="Discharge destination")
    origem: Optional[str] = Field(None, description="Origin facility/location")
    
    # Reference to related records
    burns: Optional[str] = Field(None, description="Reference to related burns record")
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        json_schema_extra = {
            "example": {
                "data_alta": "2023-05-15",
                "destino": "Home",
                "burns": "507f1f77bcf86cd799439011"
            }
        }
    )

class AdmissionResponse(AdmissionBase):
    """Schema for responses including the MongoDB ID"""
    id: PyObjectId = Field(alias='_id')
    burns: Optional[str] = Field(None, description="Reference to related burns record")