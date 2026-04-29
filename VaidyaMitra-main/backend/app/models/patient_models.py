"""
Patient Data Models

Models for patient registration, visits, and medical records.
Includes hospital-grade fields: Aadhaar, email, emergency contact, occupation, marital status, address.
All PII fields are scrubbed via DataGuard before AI processing.
"""

import re
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator


class Gender(str, Enum):
    MALE = "M"
    FEMALE = "F"
    OTHER = "O"


class BloodGroup(str, Enum):
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS = "O+"
    O_NEG = "O-"
    UNKNOWN = "Unknown"


class MaritalStatus(str, Enum):
    SINGLE = "Single"
    MARRIED = "Married"
    WIDOWED = "Widowed"
    DIVORCED = "Divorced"
    SEPARATED = "Separated"
    OTHER = "Other"


class Patient(BaseModel):
    """Core patient profile — hospital admission grade."""
    patient_id: str = ""
    name: str
    age: int
    gender: Gender
    date_of_birth: Optional[str] = None
    blood_group: BloodGroup = BloodGroup.UNKNOWN
    marital_status: MaritalStatus = MaritalStatus.SINGLE

    # Contact info
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None

    # Indian identity
    aadhaar_no: Optional[str] = None  # 12-digit Aadhaar number
    abha_no: Optional[str] = None     # 14-digit ABHA (Ayushman Bharat Health Account) ID
    pan_no: Optional[str] = None      # 10-char PAN (optional)

    # Emergency
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None

    # Demographics
    occupation: Optional[str] = None
    religion: Optional[str] = None
    nationality: str = "Indian"

    # Medical
    allergies: List[str] = Field(default_factory=list)
    chronic_conditions: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)
    family_history: List[str] = Field(default_factory=list)
    past_surgeries: List[str] = Field(default_factory=list)

    # System
    language_preference: str = "en"
    registered_at: str = ""
    updated_at: str = ""

    @field_validator("age")
    @classmethod
    def validate_age(cls, v: int) -> int:
        if v < 0 or v > 150:
            raise ValueError("Age must be between 0 and 150")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r"^[6-9]\d{9}$", v):
            raise ValueError("Phone must be a valid 10-digit Indian mobile number (starting 6-9)")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", v):
            raise ValueError("Invalid email format")
        return v

    @field_validator("aadhaar_no")
    @classmethod
    def validate_aadhaar(cls, v: Optional[str]) -> Optional[str]:
        if v:
            cleaned = v.replace(" ", "").replace("-", "")
            if not re.match(r"^\d{12}$", cleaned):
                raise ValueError("Aadhaar must be exactly 12 digits")
            return cleaned
        return v

    @field_validator("abha_no")
    @classmethod
    def validate_abha(cls, v: Optional[str]) -> Optional[str]:
        """Validate ABHA (Ayushman Bharat Health Account) — 14 digit health ID."""
        if v:
            cleaned = v.replace(" ", "").replace("-", "")
            if not re.match(r"^\d{14}$", cleaned):
                raise ValueError("ABHA number must be exactly 14 digits")
            return cleaned
        return v

    @field_validator("pan_no")
    @classmethod
    def validate_pan(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", v.upper()):
            raise ValueError("PAN must be in format ABCDE1234F")
        return v.upper() if v else v

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r"^\d{6}$", v):
            raise ValueError("Pincode must be exactly 6 digits")
        return v


# ========== Vital Sign Boundaries (Indian clinical standards) ==========
VITAL_RANGES = {
    "blood_pressure_systolic": {"min": 60, "max": 250, "unit": "mmHg"},
    "blood_pressure_diastolic": {"min": 30, "max": 160, "unit": "mmHg"},
    "heart_rate": {"min": 30, "max": 220, "unit": "bpm"},
    "respiratory_rate": {"min": 6, "max": 60, "unit": "breaths/min"},
    "temperature": {"min": 34.0, "max": 43.0, "unit": "°C"},
    "oxygen_saturation": {"min": 50, "max": 100, "unit": "%"},
    "weight": {"min": 0.5, "max": 300, "unit": "kg"},
    "height": {"min": 30, "max": 250, "unit": "cm"},
    "bmi": {"min": 8, "max": 70, "unit": "kg/m²"},
    "blood_glucose": {"min": 20, "max": 700, "unit": "mg/dL"},
}


def validate_vitals(vitals: Dict[str, float]) -> Dict[str, str]:
    """Validate vital signs against clinically possible ranges. Returns dict of errors."""
    errors = {}
    for key, value in vitals.items():
        if key in VITAL_RANGES:
            r = VITAL_RANGES[key]
            if value < r["min"] or value > r["max"]:
                errors[key] = f"{key} ({value}) is out of clinical range ({r['min']}-{r['max']} {r['unit']})"
    return errors


class PatientVisit(BaseModel):
    """Single patient visit record — comprehensive clinical intake."""
    visit_id: str = ""
    patient_id: str
    visit_type: str = "ROUTINE"  # ROUTINE, FOLLOW_UP, EMERGENCY, REFERRAL, SURGERY_PRE, SURGERY_POST
    visit_date: str = ""
    doctor_name: Optional[str] = None
    department: Optional[str] = None

    # SOAP note structure
    chief_complaint: str = ""
    history_of_present_illness: str = ""  # HPI
    past_medical_history: str = ""
    family_history: str = ""
    social_history: str = ""  # smoking, alcohol, occupation hazards
    review_of_systems: str = ""  # ROS

    # Exam
    physical_examination: str = ""
    assessment: str = ""
    plan: str = ""
    notes: str = ""

    # Vitals
    vitals: Dict[str, float] = Field(default_factory=dict)

    # Lab & Rx
    lab_results: List[Dict[str, str]] = Field(default_factory=list)
    medications_prescribed: List[Dict[str, str]] = Field(default_factory=list)
    diagnosis: List[str] = Field(default_factory=list)
    icd_codes: List[str] = Field(default_factory=list)

    # Follow-up
    follow_up_date: Optional[str] = None
    follow_up_instructions: str = ""
    referral_to: Optional[str] = None

    # Attachments — OCR-extracted document IDs
    attachments: List[str] = Field(default_factory=list)
    ocr_extracted: bool = False


class PatientRecord(BaseModel):
    """Privacy-masked medical record for display."""
    record_id: str
    patient_id: str
    visit_date: str
    visit_type: str
    department: Optional[str] = None
    doctor_name: Optional[str] = None
    masked_complaint: str
    masked_assessment: str
    masked_plan: str
    masked_hpi: str = ""
    vitals: Dict[str, float]
    diagnosis: List[str]
    icd_codes: List[str] = Field(default_factory=list)
    lab_results: List[Dict[str, str]] = Field(default_factory=list)
    medications_prescribed: List[Dict[str, str]] = Field(default_factory=list)
    follow_up_date: Optional[str] = None
    privacy_applied: bool = True
    entities_masked: int = 0
    severity: str = "normal"  # normal, elevated, critical


class HealthTrend(BaseModel):
    """Health metric trend over time."""
    metric_name: str
    unit: str
    data_points: List[Dict[str, Any]]  # [{date, value}]
    trend: str = "stable"  # improving, worsening, stable
    normal_range: Optional[Dict[str, float]] = None


class PatientSummary(BaseModel):
    """Aggregated patient summary."""
    patient_id: str
    patient_name: str
    total_visits: int
    last_visit_date: Optional[str] = None
    active_conditions: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    health_trends: List[HealthTrend] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
