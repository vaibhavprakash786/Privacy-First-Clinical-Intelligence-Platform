"""
API Request/Response Models

Pydantic models for all REST API endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# --- Request Models ---

class ClinicalDataInput(BaseModel):
    """Request body for submitting clinical data."""
    patient_id: Optional[str] = Field(None, description="Patient identifier (will be anonymized)")
    visit_date: Optional[str] = Field(None, description="Visit date in ISO format")
    visit_type: str = Field(default="ROUTINE", description="ROUTINE, FOLLOW_UP, or EMERGENCY")
    input_format: str = Field(default="manual", description="manual, json, hl7")
    chief_complaint: Optional[str] = None
    history_of_present_illness: Optional[str] = None
    past_medical_history: Optional[str] = None
    vitals: Optional[Dict[str, Any]] = None
    lab_results: Optional[List[Dict[str, Any]]] = None
    medications: Optional[List[Dict[str, Any]]] = None
    allergies: Optional[List[str]] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    notes: Optional[str] = None


class QueryRequest(BaseModel):
    """Request body for natural language query."""
    query: str = Field(..., min_length=1, description="Natural language query")
    patient_id: Optional[str] = Field(None, description="Patient context")


class DiseasePredictionRequest(BaseModel):
    """Request body for disease prediction."""
    symptoms: List[str] = Field(..., min_items=1, description="List of symptoms")
    patient_id: Optional[str] = Field(None)
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[str] = Field(None)


class GenericMedicineRequest(BaseModel):
    """Request body for finding generic alternatives."""
    medicine_name: str = Field(..., min_length=1, description="Branded medicine name")
    quantity: Optional[int] = Field(None, ge=1, description="Quantity for savings calculation")


# --- Response Models ---

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "operational"
    version: str = "1.0.0"
    services: Dict[str, bool] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ErrorDetail(BaseModel):
    """Error detail."""
    code: str
    message: str
    user_message: Optional[str] = None
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standardized error response."""
    error: ErrorDetail


class ClinicalDataResponse(BaseModel):
    """Response after submitting clinical data."""
    success: bool = True
    visit_id: str = ""
    patient_id: str = ""
    privacy_applied: bool = True
    entities_masked: int = 0
    message: str = "Clinical data processed and stored successfully"


class UploadReportResponse(BaseModel):
    """Response after uploading PDF report."""
    success: bool = True
    visit_id: str = ""
    patient_id: str = ""
    pages_extracted: int = 0
    text_length: int = 0
    privacy_applied: bool = True
    entities_masked: int = 0
    s3_key: Optional[str] = None
