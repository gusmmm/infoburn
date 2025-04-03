"""
Database models for admission data.

This module contains the MongoDB data models for admission data,
matching the Pydantic models used for validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from enum import Enum


class Gender(str, Enum):
    """Enumeration for patient gender"""
    MALE = "M"
    FEMALE = "F"


class AdmissionDataModel(BaseModel):
    """
    Database model for Burns Critical Care Unit patient admission data.
    Corresponds to the 'admission_data' collection in MongoDB.
    """
    ID: str = Field(description="Patient admission identifier (4-5 digits)")
    processo: Optional[int] = Field(None, description="Patient file number")
    nome: Optional[str] = Field(None, description="Full name of the patient")
    data_ent: Optional[date] = Field(None, description="Date of admission to the Burns Critical Care Unit")
    data_alta: Optional[date] = Field(None, description="Release date from the Burns Critical Care Unit")
    sexo: Optional[Gender] = Field(None, description="Patient gender (M or F)")
    data_nasc: Optional[date] = Field(None, description="Patient's birth date")
    destino: Optional[str] = Field(None, description="Discharge destination after release from the unit")
    origem: Optional[str] = Field(None, description="Origin facility/location before admission to the unit")

    class Config:
        """Configuration for the AdmissionDataModel"""
        collection = "admission_data"
        schema_extra = {
            "example": {
                "ID": "12345",
                "processo": 987654,
                "nome": "João Silva",
                "data_ent": "2023-06-15",
                "data_alta": "2023-06-30",
                "sexo": "M",
                "data_nasc": "1980-01-01",
                "destino": "Home",
                "origem": "Emergency Department"
            }
        }