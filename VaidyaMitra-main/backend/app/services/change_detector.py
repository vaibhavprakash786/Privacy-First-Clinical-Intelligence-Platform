"""
Change Detector

AI-powered change detection between clinical visits using Bedrock.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.bedrock_client import BedrockClient, get_bedrock_client, AIError
from app.models.clinical import ClinicalVisit, Severity, TrendDirection
from app.models.ai_models import ChangeReport, Change, Finding

logger = logging.getLogger(__name__)


class ChangeDetector:
    """Clinical change detector using AI reasoning."""

    SYSTEM_PROMPT = """You are a clinical intelligence assistant that provides decision-support to doctors.
You analyze anonymized clinical data and identify significant changes between visits.
You MUST respond with valid JSON only. You do NOT diagnose or prescribe treatment."""

    CHANGE_PROMPT = """Identify significant changes between these two visits:

Previous Visit:
{previous_visit_data}

Current Visit:
{current_visit_data}

Return JSON:
{{
  "significant_changes": [
    {{
      "category": "VITALS|LABS|MEDICATIONS|SYMPTOMS|CONDITIONS",
      "description": "What changed",
      "severity": "critical|important|minor",
      "previous_value": "Previous value",
      "current_value": "Current value",
      "trend_direction": "improving|worsening|stable",
      "reasoning": "Why significant",
      "confidence": 0.95
    }}
  ],
  "stable_conditions": ["Stable condition 1"],
  "new_findings": [
    {{
      "category": "CONDITION|SYMPTOM|LAB_ABNORMALITY",
      "description": "New finding",
      "severity": "critical|important|minor",
      "supporting_data": ["data"],
      "reasoning": "Why significant",
      "confidence": 0.90
    }}
  ],
  "resolved_issues": ["Resolved issue 1"],
  "overall_assessment": "Overall trajectory summary"
}}

Respond ONLY with valid JSON."""

    FIRST_VISIT_PROMPT = """Analyze this first visit and identify key findings:

Visit Data:
{current_visit_data}

Return JSON with same structure but significant_changes and resolved_issues as empty arrays.
Respond ONLY with valid JSON."""

    def __init__(self, ai_client: Optional[BedrockClient] = None):
        self.ai_client = ai_client or get_bedrock_client()
        logger.info("ChangeDetector initialized")

    def detect_changes(
        self,
        current_visit: ClinicalVisit,
        previous_visit: Optional[ClinicalVisit] = None,
    ) -> ChangeReport:
        """Detect changes between current and previous visits."""
        try:
            current_data = self._build_visit_string(current_visit)

            if previous_visit:
                previous_data = self._build_visit_string(previous_visit)
                prompt = self.CHANGE_PROMPT.format(
                    previous_visit_data=previous_data,
                    current_visit_data=current_data,
                )
                comparison_id = previous_visit.visit_id
            else:
                prompt = self.FIRST_VISIT_PROMPT.format(current_visit_data=current_data)
                comparison_id = "FIRST_VISIT"

            response = self.ai_client.invoke_json(prompt=prompt, system_prompt=self.SYSTEM_PROMPT)

            changes = []
            for c in response.get("significant_changes", []):
                sev = c.get("severity", "minor").lower()
                if sev not in ["critical", "important", "minor"]:
                    sev = "minor"
                trend = c.get("trend_direction", "stable").lower()
                if trend not in ["improving", "worsening", "stable"]:
                    trend = "stable"
                changes.append(Change(
                    change_id=str(uuid.uuid4()),
                    category=c.get("category", "CONDITIONS"),
                    description=c.get("description", ""),
                    severity=Severity(sev),
                    previous_value=c.get("previous_value"),
                    current_value=c.get("current_value", ""),
                    trend_direction=TrendDirection(trend),
                    reasoning=c.get("reasoning", ""),
                    confidence=float(c.get("confidence", 0.5)),
                ))

            findings = []
            for f in response.get("new_findings", []):
                sev = f.get("severity", "minor").lower()
                if sev not in ["critical", "important", "minor"]:
                    sev = "minor"
                findings.append(Finding(
                    finding_id=str(uuid.uuid4()),
                    category=f.get("category", "CONDITION"),
                    description=f.get("description", ""),
                    severity=Severity(sev),
                    supporting_data=f.get("supporting_data", []),
                    reasoning=f.get("reasoning", ""),
                    confidence=float(f.get("confidence", 0.5)),
                ))

            return ChangeReport(
                report_id=str(uuid.uuid4()),
                patient_id=current_visit.patient_id,
                current_visit_id=current_visit.visit_id,
                comparison_visit_id=comparison_id,
                significant_changes=changes,
                stable_conditions=response.get("stable_conditions", []),
                new_findings=findings,
                resolved_issues=response.get("resolved_issues", []),
                overall_assessment=response.get("overall_assessment", ""),
            )

        except Exception as e:
            logger.error(f"Change detection error: {e}")
            raise

    def _build_visit_string(self, visit: ClinicalVisit) -> str:
        parts = [f"Date: {visit.visit_date.strftime('%Y-%m-%d')}", f"Type: {visit.visit_type}"]
        if visit.chief_complaint:
            parts.append(f"Complaint: {visit.chief_complaint}")
        if visit.vitals:
            v = visit.vitals
            vp = []
            if v.blood_pressure_systolic:
                vp.append(f"BP:{v.blood_pressure_systolic}/{v.blood_pressure_diastolic}")
            if v.heart_rate:
                vp.append(f"HR:{v.heart_rate}")
            if v.temperature:
                vp.append(f"T:{v.temperature}")
            if v.oxygen_saturation:
                vp.append(f"SpO2:{v.oxygen_saturation}%")
            if vp:
                parts.append(f"Vitals: {', '.join(vp)}")
        if visit.lab_results:
            for lab in visit.lab_results:
                parts.append(f"Lab: {lab.test_name}={lab.value}{lab.unit}")
        if visit.medications:
            for med in visit.medications:
                parts.append(f"Med: {med.name} {med.dosage} {med.frequency}")
        if visit.assessment:
            parts.append(f"Assessment: {visit.assessment}")
        return "\n".join(parts)
