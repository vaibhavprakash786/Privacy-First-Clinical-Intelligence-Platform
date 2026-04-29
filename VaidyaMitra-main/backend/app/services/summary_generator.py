"""
Clinical Summary Generator

AI-powered clinical summarization using Bedrock for reasoning.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.bedrock_client import BedrockClient, get_bedrock_client, AIError
from app.models.clinical import ClinicalVisit, Severity
from app.models.ai_models import ClinicalSummary, Finding, ReasoningStep

logger = logging.getLogger(__name__)


class SummaryGenerator:
    """Clinical summary generator using AI reasoning."""

    SYSTEM_PROMPT = """You are a clinical intelligence assistant providing decision-support to doctors.
You analyze anonymized clinical data and generate comprehensive summaries.
You MUST respond with valid JSON only. You do NOT diagnose or prescribe treatment."""

    SUMMARY_PROMPT_TEMPLATE = """Analyze the following anonymized clinical data and generate a comprehensive summary.

Clinical Data:
{clinical_data}

Generate a JSON response with this exact structure:
{{
  "summary_text": "Comprehensive clinical summary paragraph",
  "key_findings": [
    {{
      "category": "CONDITION|SYMPTOM|LAB_ABNORMALITY|MEDICATION_CHANGE",
      "description": "Description of finding",
      "severity": "critical|important|minor",
      "supporting_data": ["data point 1"],
      "reasoning": "Why this is significant",
      "confidence": 0.90
    }}
  ],
  "reasoning_steps": [
    {{
      "step_number": 1,
      "description": "What was analyzed",
      "evidence": "Supporting evidence",
      "confidence": 0.90
    }}
  ],
  "confidence": 0.85
}}

Respond ONLY with valid JSON."""

    def __init__(self, ai_client: Optional[BedrockClient] = None):
        self.ai_client = ai_client or get_bedrock_client()
        logger.info("SummaryGenerator initialized")

    def generate_summary(self, clinical_visit: ClinicalVisit) -> ClinicalSummary:
        """Generate AI-powered clinical summary for a patient visit."""
        try:
            clinical_data = self._build_clinical_data_string(clinical_visit)
            prompt = self.SUMMARY_PROMPT_TEMPLATE.format(clinical_data=clinical_data)

            response_json = self.ai_client.invoke_json(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
                max_tokens=3000,
            )

            return self._parse_response(response_json, clinical_visit)

        except Exception as e:
            logger.error(f"Summary generation error: {e}")
            raise

    def _build_clinical_data_string(self, visit: ClinicalVisit) -> str:
        parts = []
        parts.append(f"Visit Date: {visit.visit_date.strftime('%Y-%m-%d')}")
        parts.append(f"Visit Type: {visit.visit_type}")

        if visit.chief_complaint:
            parts.append(f"\nChief Complaint: {visit.chief_complaint}")
        if visit.history_of_present_illness:
            parts.append(f"\nHPI: {visit.history_of_present_illness}")
        if visit.past_medical_history:
            parts.append(f"\nPMH: {visit.past_medical_history}")

        if visit.vitals:
            v = visit.vitals
            vitals_parts = []
            if v.blood_pressure_systolic and v.blood_pressure_diastolic:
                vitals_parts.append(f"BP: {v.blood_pressure_systolic}/{v.blood_pressure_diastolic}")
            if v.heart_rate:
                vitals_parts.append(f"HR: {v.heart_rate}")
            if v.temperature:
                vitals_parts.append(f"Temp: {v.temperature}°C")
            if v.oxygen_saturation:
                vitals_parts.append(f"SpO2: {v.oxygen_saturation}%")
            if v.weight:
                vitals_parts.append(f"Weight: {v.weight}kg")
            if vitals_parts:
                parts.append(f"\nVitals: {', '.join(vitals_parts)}")

        if visit.lab_results:
            parts.append("\nLab Results:")
            for lab in visit.lab_results:
                flag = " (ABNORMAL)" if lab.abnormal_flag else ""
                parts.append(f"  - {lab.test_name}: {lab.value} {lab.unit}{flag}")

        if visit.medications:
            parts.append("\nMedications:")
            for med in visit.medications:
                parts.append(f"  - {med.name} {med.dosage} {med.frequency}")

        if visit.assessment:
            parts.append(f"\nAssessment: {visit.assessment}")
        if visit.plan:
            parts.append(f"\nPlan: {visit.plan}")

        return "\n".join(parts)

    def _parse_response(self, response_json: Dict[str, Any], visit: ClinicalVisit) -> ClinicalSummary:
        findings = []
        for f in response_json.get("key_findings", []):
            severity_str = f.get("severity", "minor").lower()
            if severity_str not in ["critical", "important", "minor"]:
                severity_str = "minor"
            findings.append(Finding(
                finding_id=str(uuid.uuid4()),
                category=f.get("category", "CONDITION"),
                description=f.get("description", ""),
                severity=Severity(severity_str),
                supporting_data=f.get("supporting_data", []),
                reasoning=f.get("reasoning", ""),
                confidence=float(f.get("confidence", 0.5)),
            ))

        reasoning_steps = []
        for r in response_json.get("reasoning_steps", []):
            reasoning_steps.append(ReasoningStep(
                step_number=r.get("step_number", 0),
                description=r.get("description", ""),
                evidence=r.get("evidence"),
                confidence=float(r.get("confidence", 0.5)),
            ))

        return ClinicalSummary(
            summary_id=str(uuid.uuid4()),
            patient_id=visit.patient_id,
            visit_id=visit.visit_id,
            summary_text=response_json.get("summary_text", ""),
            key_findings=findings,
            reasoning_steps=reasoning_steps,
            confidence_score=float(response_json.get("confidence", 0.0)),
        )
