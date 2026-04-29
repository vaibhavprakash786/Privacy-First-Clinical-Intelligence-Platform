"""
Clinical Data Models

Core data structures for clinical information including
vital signs, lab results, medications, and clinical visits.
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator


class InputFormat(str, Enum):
    """Supported input formats for clinical data."""
    MANUAL = "manual"
    PDF = "pdf"
    JSON = "json"
    HL7 = "hl7"


class Severity(str, Enum):
    """Severity levels for clinical findings and changes."""
    CRITICAL = "critical"
    IMPORTANT = "important"
    MINOR = "minor"


class TrendDirection(str, Enum):
    """Direction of clinical trends over time."""
    IMPROVING = "improving"
    WORSENING = "worsening"
    STABLE = "stable"


class VitalSigns(BaseModel):
    """Patient vital signs with validation."""

    blood_pressure_systolic: Optional[int] = Field(
        None, ge=50, le=300, description="Systolic blood pressure in mmHg"
    )
    blood_pressure_diastolic: Optional[int] = Field(
        None, ge=30, le=200, description="Diastolic blood pressure in mmHg"
    )
    heart_rate: Optional[int] = Field(
        None, ge=20, le=300, description="Heart rate in beats per minute"
    )
    temperature: Optional[float] = Field(
        None, ge=35.0, le=43.0, description="Body temperature in Celsius"
    )
    respiratory_rate: Optional[int] = Field(
        None, ge=5, le=60, description="Respiratory rate per minute"
    )
    oxygen_saturation: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Oxygen saturation percentage"
    )
    weight: Optional[float] = Field(
        None, gt=0.0, le=500.0, description="Weight in kilograms"
    )
    height: Optional[float] = Field(
        None, gt=0.0, le=300.0, description="Height in centimeters"
    )
    bmi: Optional[float] = Field(None, ge=5.0, le=100.0, description="Body Mass Index")

    @model_validator(mode="after")
    def validate_blood_pressure(self):
        if (
            self.blood_pressure_systolic is not None
            and self.blood_pressure_diastolic is not None
        ):
            if self.blood_pressure_systolic <= self.blood_pressure_diastolic:
                raise ValueError(
                    "Systolic blood pressure must be greater than diastolic"
                )
        return self


class LabResult(BaseModel):
    """Laboratory test result."""

    test_name: str = Field(..., min_length=1, description="Name of the test")
    value: float | str = Field(..., description="Test result value")
    unit: str = Field(..., min_length=1, description="Unit of measurement")
    reference_range: Optional[str] = Field(None, description="Normal reference range")
    abnormal_flag: Optional[bool] = Field(None, description="Whether result is abnormal")
    test_date: datetime = Field(..., description="Date when the test was performed")

    @field_validator("test_date")
    @classmethod
    def validate_test_date(cls, v: datetime) -> datetime:
        if v > datetime.utcnow():
            raise ValueError("Test date cannot be in the future")
        return v


class Medication(BaseModel):
    """Medication information."""

    name: str = Field(..., min_length=1, description="Medication name")
    dosage: str = Field(..., min_length=1, description="Dosage amount and form")
    frequency: str = Field(..., min_length=1, description="Frequency of administration")
    route: str = Field(..., min_length=1, description="Route of administration")
    start_date: Optional[datetime] = Field(None, description="Date medication was started")
    end_date: Optional[datetime] = Field(None, description="Date medication was discontinued")
    indication: Optional[str] = Field(None, description="Reason for medication")

    @model_validator(mode="after")
    def validate_dates(self):
        now = datetime.utcnow()
        if self.start_date and self.start_date > now:
            raise ValueError("Medication start date cannot be in the future")
        if self.end_date and self.end_date > now:
            raise ValueError("Medication end date cannot be in the future")
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("Medication start date must be before end date")
        return self


class ClinicalVisit(BaseModel):
    """Complete clinical visit record."""

    visit_id: str = Field(..., min_length=1, description="Unique visit identifier")
    patient_id: str = Field(..., min_length=1, description="Anonymized patient identifier")
    visit_date: datetime = Field(..., description="Date and time of visit")
    visit_type: str = Field(..., description="Type of visit (ROUTINE, FOLLOW_UP, EMERGENCY)")
    chief_complaint: Optional[str] = Field(None, description="Patient's primary complaint")
    history_of_present_illness: Optional[str] = Field(None, description="History of current illness")
    past_medical_history: Optional[str] = Field(None, description="Past medical history")
    medications: List[Medication] = Field(default_factory=list, description="Current medications")
    allergies: List[str] = Field(default_factory=list, description="Known allergies")
    vitals: Optional[VitalSigns] = Field(None, description="Vital signs recorded during visit")
    lab_results: List[LabResult] = Field(default_factory=list, description="Laboratory test results")
    assessment: Optional[str] = Field(None, description="Clinical assessment")
    plan: Optional[str] = Field(None, description="Treatment plan")
    notes: Optional[str] = Field(None, description="Additional clinical notes")
    input_format: InputFormat = Field(default=InputFormat.MANUAL, description="Data input format")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("visit_date")
    @classmethod
    def validate_visit_date(cls, v: datetime) -> datetime:
        if v > datetime.utcnow():
            raise ValueError("Visit date cannot be in the future")
        return v

    @field_validator("visit_type")
    @classmethod
    def validate_visit_type(cls, v: str) -> str:
        allowed = {"ROUTINE", "FOLLOW_UP", "EMERGENCY"}
        if v.upper() not in allowed:
            raise ValueError(f"Visit type must be one of: {', '.join(allowed)}")
        return v.upper()
