"""
AI Response Models

Structured output models for all AI-generated content including clinical summaries,
change reports, disease predictions, and generic medicine results.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.clinical import Severity, TrendDirection


class ReasoningStep(BaseModel):
    """A single step in AI reasoning chain."""
    step_number: int = Field(..., description="Step number in reasoning chain")
    description: str = Field(..., description="Description of reasoning step")
    evidence: Optional[str] = Field(None, description="Supporting evidence")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class Finding(BaseModel):
    """A clinical finding detected by AI."""
    finding_id: str = Field(..., description="Unique finding identifier")
    category: str = Field(..., description="Finding category (CONDITION, SYMPTOM, LAB_ABNORMALITY, etc.)")
    description: str = Field(..., description="Description of finding")
    severity: Severity = Field(default=Severity.MINOR)
    supporting_data: List[str] = Field(default_factory=list)
    reasoning: str = Field(default="")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class ClinicalSummary(BaseModel):
    """AI-generated clinical summary."""
    summary_id: str = Field(..., description="Unique summary identifier")
    patient_id: str = Field(..., description="Anonymized patient identifier")
    visit_id: str = Field(..., description="Visit identifier")
    summary_text: str = Field(..., description="Generated clinical summary")
    key_findings: List[Finding] = Field(default_factory=list)
    reasoning_steps: List[ReasoningStep] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    model_version: str = Field(default="claude-3-sonnet")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class Change(BaseModel):
    """A detected change between clinical visits."""
    change_id: str = Field(...)
    category: str = Field(..., description="VITALS, LABS, MEDICATIONS, SYMPTOMS, CONDITIONS")
    description: str = Field(...)
    severity: Severity = Field(default=Severity.MINOR)
    previous_value: Optional[str] = Field(None)
    current_value: str = Field(default="")
    trend_direction: TrendDirection = Field(default=TrendDirection.STABLE)
    reasoning: str = Field(default="")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class ChangeReport(BaseModel):
    """AI-generated change report between visits."""
    report_id: str = Field(...)
    patient_id: str = Field(...)
    current_visit_id: str = Field(...)
    comparison_visit_id: str = Field(...)
    significant_changes: List[Change] = Field(default_factory=list)
    stable_conditions: List[str] = Field(default_factory=list)
    new_findings: List[Finding] = Field(default_factory=list)
    resolved_issues: List[str] = Field(default_factory=list)
    overall_assessment: str = Field(default="")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class DiseasePrediction(BaseModel):
    """AI-generated disease prediction."""
    prediction_id: str = Field(...)
    patient_id: Optional[str] = Field(None)
    symptoms: List[str] = Field(default_factory=list)
    predicted_diseases: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of {disease, probability, confidence}",
    )
    recommended_tests: List[str] = Field(default_factory=list)
    reasoning_steps: List[ReasoningStep] = Field(default_factory=list)
    ai_explanation: str = Field(default="")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    model_version: str = Field(default="medicure-v1")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class DrugAlternative(BaseModel):
    """A generic medicine alternative."""
    generic_name: str = Field(...)
    composition: str = Field(...)
    strength: str = Field(default="")
    jan_aushadhi_price: float = Field(default=0.0)
    branded_price: float = Field(default=0.0)
    savings_amount: float = Field(default=0.0)
    savings_percentage: float = Field(default=0.0)
    manufacturer: str = Field(default="")
    is_jan_aushadhi: bool = Field(default=False)


class GenericMedicineResult(BaseModel):
    """Complete generic medicine analysis result."""
    result_id: str = Field(...)
    brand_name: str = Field(...)
    composition: str = Field(default="")
    alternatives: List[DrugAlternative] = Field(default_factory=list)
    total_savings: float = Field(default=0.0)
    ai_explanation: str = Field(default="")
    safety_note: str = Field(
        default="Always consult your doctor before switching medications."
    )
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
