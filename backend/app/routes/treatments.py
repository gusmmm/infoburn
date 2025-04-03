"""
Treatment routes for InfoBurn API.

This module handles all API endpoints related to treatments and procedures
for patients in the burns critical care unit, including wound care,
surgeries, medication administration, and therapy plans.
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, date
from enum import Enum

# Create router
treatment_router = APIRouter(
    prefix="/treatments",
    tags=["treatments"]
)

# Enums for standardized options
class ProcedureType(str, Enum):
    """Types of procedures performed in burn care"""
    DRESSING_CHANGE = "dressing_change"
    DEBRIDEMENT = "debridement"
    SKIN_GRAFT = "skin_graft"
    ESCHAROTOMY = "escharotomy"
    FASCIOTOMY = "fasciotomy"
    FLUID_RESUSCITATION = "fluid_resuscitation"
    PAIN_MANAGEMENT = "pain_management"
    PHYSICAL_THERAPY = "physical_therapy"
    OTHER = "other"

class MedicationType(str, Enum):
    """Types of medications commonly used in burn care"""
    ANALGESIC = "analgesic"
    ANTIBIOTIC = "antibiotic"
    SEDATIVE = "sedative"
    VASOPRESSOR = "vasopressor"
    ANTICOAGULANT = "anticoagulant"
    FLUID = "fluid"
    OTHER = "other"

# Models
class MedicationBase(BaseModel):
    """Model for medication administration"""
    name: str = Field(..., description="Name of medication")
    dosage: str = Field(..., description="Dosage and unit")
    route: str = Field(..., description="Administration route (IV, oral, etc.)")
    frequency: str = Field(..., description="Administration frequency")
    type: MedicationType = Field(..., description="Type of medication")
    start_date: date = Field(..., description="Start date of medication")
    end_date: Optional[date] = Field(None, description="End date of medication")
    notes: Optional[str] = Field(None, description="Additional notes")

class ProcedureBase(BaseModel):
    """Model for medical procedures"""
    type: ProcedureType = Field(..., description="Type of procedure")
    description: str = Field(..., description="Detailed description of procedure")
    location: Optional[str] = Field(None, description="Anatomical location")
    timestamp: datetime = Field(default_factory=datetime.now, description="Time of procedure")
    performed_by: str = Field(..., description="Healthcare provider who performed the procedure")
    outcome: Optional[str] = Field(None, description="Outcome or result of procedure")
    complications: Optional[str] = Field(None, description="Any complications encountered")
    notes: Optional[str] = Field(None, description="Additional notes")

class TreatmentPlanBase(BaseModel):
    """Model for treatment plans"""
    title: str = Field(..., description="Title of the treatment plan")
    description: str = Field(..., description="Detailed description of the plan")
    start_date: date = Field(..., description="Start date of treatment plan")
    end_date: Optional[date] = Field(None, description="Expected end date of treatment plan")
    goals: List[str] = Field(..., description="Treatment goals")
    created_by: str = Field(..., description="Healthcare provider who created the plan")
    
class TreatmentCreate(BaseModel):
    """Model for creating a treatment record"""
    patient_id: str = Field(..., description="ID of the patient")
    medication: Optional[MedicationBase] = None
    procedure: Optional[ProcedureBase] = None
    treatment_plan: Optional[TreatmentPlanBase] = None
    
class Treatment(TreatmentCreate):
    """Full treatment model with database ID"""
    id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True

# Routes
@treatment_router.get("/", response_model=List[Treatment])
async def get_treatments(
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    treatment_type: Optional[str] = Query(None, description="Filter by treatment type (medication, procedure, plan)"),
    start_date: Optional[date] = Query(None, description="Filter by start date (from)"),
    end_date: Optional[date] = Query(None, description="Filter by end date (to)"),
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return")
):
    """
    Get a list of treatments.
    
    Returns a paginated list of treatments, optionally filtered by patient,
    type, and date range.
    """
    # Implementation placeholder
    return []

@treatment_router.post("/", response_model=Treatment)
async def create_treatment(treatment: TreatmentCreate):
    """
    Record a new treatment.
    
    Takes treatment data and creates a new record in the database.
    """
    # Implementation placeholder
    now = datetime.now()
    return {
        "id": "placeholder", 
        "created_at": now,
        "updated_at": now,
        **treatment.model_dump()
    }

@treatment_router.get("/{treatment_id}", response_model=Treatment)
async def get_treatment(
    treatment_id: str = Path(..., description="The ID of the treatment to retrieve")
):
    """
    Get a specific treatment by ID.
    
    Retrieves detailed information about a treatment.
    """
    # Implementation placeholder
    now = datetime.now()
    return {
        "id": treatment_id, 
        "patient_id": "patient123",
        "procedure": {
            "type": ProcedureType.DRESSING_CHANGE,
            "description": "Change of silver sulfadiazine dressing on left arm",
            "location": "left arm",
            "timestamp": now,
            "performed_by": "nurse_jones",
            "outcome": "Wound appears clean with good granulation tissue",
            "complications": None,
            "notes": "Patient tolerated procedure well with minimal discomfort"
        },
        "medication": None,
        "treatment_plan": None,
        "created_at": now,
        "updated_at": now
    }

@treatment_router.put("/{treatment_id}", response_model=Treatment)
async def update_treatment(
    treatment: TreatmentCreate,
    treatment_id: str = Path(..., description="The ID of the treatment to update")
):
    """
    Update a treatment record.
    
    Updates an existing treatment with new information.
    """
    # Implementation placeholder
    now = datetime.now()
    return {
        "id": treatment_id, 
        "created_at": datetime(2023, 1, 1),
        "updated_at": now,
        **treatment.model_dump()
    }

@treatment_router.delete("/{treatment_id}")
async def delete_treatment(
    treatment_id: str = Path(..., description="The ID of the treatment to delete")
):
    """
    Remove a treatment from the system.
    
    Deletes a treatment record from the database.
    """
    # Implementation placeholder
    return {"message": f"Treatment {treatment_id} deleted successfully"}