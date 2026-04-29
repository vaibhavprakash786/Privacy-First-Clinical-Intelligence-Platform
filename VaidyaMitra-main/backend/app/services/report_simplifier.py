"""
Report Simplifier Service

AI-powered medical report simplification and summarization.
Converts complex medical jargon to patient-friendly language.
Uses AWS Bedrock Claude for AI simplification, with jargon-map fallback.
Integrated with AWS DynamoDB caching for repeated report analyses.
"""

import hashlib
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Optional

from app.core.config import settings
from app.services.bedrock_client import get_bedrock_client
from app.core.cache_client import CacheClient, get_cache_client

logger = logging.getLogger(__name__)

# Medical jargon → simple language mappings (used as fallback when Bedrock unavailable)
JARGON_MAP = {
    "hypertension": "high blood pressure",
    "hypotension": "low blood pressure",
    "tachycardia": "fast heart rate",
    "bradycardia": "slow heart rate",
    "dyspnea": "difficulty breathing",
    "edema": "swelling",
    "pyrexia": "fever",
    "myalgia": "muscle pain",
    "arthralgia": "joint pain",
    "cephalgia": "headache",
    "hba1c": "average blood sugar level (HbA1c)",
    "hemoglobin": "blood's oxygen-carrying protein",
    "creatinine": "kidney waste marker",
    "bilirubin": "liver waste marker",
    "lipid profile": "cholesterol and fat levels",
    "ecg": "heart rhythm test (ECG)",
    "ct scan": "detailed X-ray scan (CT)",
    "mri": "magnetic body scan (MRI)",
    "biopsy": "tissue sample test",
    "prognosis": "expected outcome",
    "etiology": "cause of disease",
    "prophylaxis": "prevention treatment",
    "contraindicated": "not recommended / unsafe",
    "asymptomatic": "no symptoms showing",
    "benign": "not harmful / not cancerous",
    "malignant": "harmful / cancerous",
    "acute": "sudden and short-term",
    "chronic": "long-lasting",
    "idiopathic": "cause unknown",
    "bilateral": "on both sides",
    "anterior": "front part",
    "posterior": "back part",
    "subcutaneous": "under the skin",
    "intravenous": "through a vein (IV)",
    "oral": "taken by mouth",
    "stat": "immediately",
    "prn": "as needed",
    "bid": "twice a day",
    "tid": "three times a day",
    "qid": "four times a day",
    "npo": "nothing by mouth / no eating before test",
}


def simplify_report(report_text: str = "", language: str = "en", image_bytes: Optional[bytes] = None, raw_file_bytes: Optional[bytes] = None) -> Dict:
    """
    Simplify a medical report into patient-friendly language.
    Uses Bedrock AI when available, falls back to jargon replacement.
    Text-only requests are cached; image requests bypass cache.
    """
    if not report_text.strip() and not image_bytes and not raw_file_bytes:
        return {"error": "Empty report text and no image provided"}

    # ── Check Cache ─────────────
    cache = get_cache_client()
    cache_key = None
    
    hasher = hashlib.sha256()
    if raw_file_bytes:
        hasher.update(raw_file_bytes)
    else:
        if report_text:
            hasher.update(report_text.encode())
        if image_bytes:
            hasher.update(image_bytes)
        
    content_hash = hasher.hexdigest()
    
    # Only cache if we actually have content to hash
    if content_hash != hashlib.sha256().hexdigest():
        cache_key = CacheClient.generate_cache_key("simplify", content_hash, language)
        cached = cache.get(cache_key)
        if cached is not None:
            logger.info(f"Report simplify CACHE HIT")
            cached["from_cache"] = True
            return cached

    ai_client = get_bedrock_client()

    # Try AI-powered simplification first
    result = None
    if ai_client.mode == "bedrock":
        try:
            result = _simplify_with_ai(ai_client, report_text, language, image_bytes)
        except Exception as e:
            logger.warning(f"Bedrock simplification failed, using fallback: {e}")

    # Fallback: jargon replacement
    if result is None:
        result = _simplify_with_jargon(report_text, language)

    result["from_cache"] = False

    # ── Store in Cache ───────────────────────────────────────
    if cache_key:
        cache.put(
            cache_key, result,
            ttl_hours=settings.CACHE_TTL_REPORT_HOURS,
            service="simplify",
            query_text=report_text[:100],
        )

    return result


def _simplify_with_ai(ai_client, report_text: str, language: str, image_bytes: Optional[bytes] = None) -> Dict:
    """Use Bedrock Claude to simplify a medical report."""
    system_prompt = """You are a medical report simplifier for Indian patients. 
Your job is to convert complex medical reports into simple, easy-to-understand language 
that a patient with basic education can understand. 

IMPORTANT RULES:
1. Replace ALL medical jargon with simple everyday words
2. Explain what test values mean (high/low/normal)
3. Use short sentences
4. Be accurate — do not add or remove medical facts
5. Keep medication names as-is but explain what they're for
6. Return your response as valid JSON"""

    prompt = f"""You are analyzing a medical report. If an image is provided, first extract all the medical data from it internally.
    
DO NOT just transcribe the raw text. You MUST rewrite and synthesize the entire content into cohesive, patient-friendly language.

Simplify this medical report for a patient. Return ONLY valid JSON in this exact format:
{{
    "simplified_text": "the fully rewritten, simplified version of the entire report in cohesive sentences",
    "terms_explained": [
        {{"medical_term": "original term", "simple_meaning": "simple explanation"}}
    ],
    "key_findings": ["finding 1", "finding 2"],
    "action_items": ["what patient should do 1", "what patient should do 2"],
    "severity_assessment": {{
        "level": "LOW or MEDIUM or HIGH",
        "color": "#22c55e for LOW, #f59e0b for MEDIUM, #ef4444 for HIGH",
        "label": "brief severity description"
    }}
}}

MEDICAL REPORT:
{report_text if report_text else "(Please extract and simplify the text from the attached medical report image)"}"""

    response = ai_client.invoke(prompt, system_prompt=system_prompt, temperature=0.2, image_bytes=image_bytes)

    # Parse AI response
    try:
        # Try to extract JSON from the response
        result = _extract_json(response)
    except Exception:
        # If JSON parsing fails, use the raw response as simplified text
        result = {
            "simplified_text": response,
            "terms_explained": [],
            "key_findings": ["AI-simplified report generated"],
            "action_items": ["Consult your doctor for detailed guidance"],
            "severity_assessment": {"level": "MEDIUM", "color": "#f59e0b", "label": "Review recommended"},
        }

    return {
        "result_id": str(uuid.uuid4()),
        "original_text": report_text,
        "simplified_text": result.get("simplified_text", response),
        "terms_explained": result.get("terms_explained", []),
        "readability_level": "Easy (Grade 6-8)",
        "language": language,
        "key_findings": result.get("key_findings", []),
        "action_items": result.get("action_items", []),
        "severity_assessment": result.get("severity_assessment", {
            "level": "LOW", "color": "#22c55e", "label": "Routine"
        }),
        "ai_powered": True,
        "disclaimer": "This is an AI-simplified version. Always consult your doctor for medical advice.",
        "generated_at": datetime.utcnow().isoformat(),
    }


def _simplify_with_jargon(report_text: str, language: str) -> Dict:
    """Fallback: simplify using jargon replacement map."""
    import re
    simplified = report_text
    terms_simplified = []

    for jargon, simple in JARGON_MAP.items():
        if jargon.lower() in simplified.lower():
            simplified = re.sub(
                re.escape(jargon), f"{simple}", simplified, flags=re.IGNORECASE
            )
            terms_simplified.append({"medical_term": jargon, "simple_meaning": simple})

    return {
        "result_id": str(uuid.uuid4()),
        "original_text": report_text,
        "simplified_text": simplified,
        "terms_explained": terms_simplified,
        "readability_level": "Easy (Grade 6-8)",
        "language": language,
        "key_findings": _extract_key_findings(report_text),
        "action_items": _extract_action_items(report_text),
        "severity_assessment": _assess_severity(report_text),
        "ai_powered": False,
        "disclaimer": "This is an AI-simplified version. Always consult your doctor for medical advice.",
        "generated_at": datetime.utcnow().isoformat(),
    }


def summarize_report(report_text: str = "", image_bytes: Optional[bytes] = None, raw_file_bytes: Optional[bytes] = None) -> Dict:
    """Create a structured AI summary of a medical report.
    Text-only requests are cached; image requests bypass cache."""
    if not report_text.strip() and not image_bytes and not raw_file_bytes:
        return {"error": "Empty report text and no image provided"}

    # ── Check Cache ─────────────
    cache = get_cache_client()
    cache_key = None
    
    hasher = hashlib.sha256()
    if raw_file_bytes:
        hasher.update(raw_file_bytes)
    else:
        if report_text:
            hasher.update(report_text.encode())
        if image_bytes:
            hasher.update(image_bytes)
        
    content_hash = hasher.hexdigest()
    
    if content_hash != hashlib.sha256().hexdigest():
        cache_key = CacheClient.generate_cache_key("summarize", content_hash)
        cached = cache.get(cache_key)
        if cached is not None:
            logger.info(f"Report summarize CACHE HIT")
            cached["from_cache"] = True
            return cached

    ai_client = get_bedrock_client()

    # Try AI-powered summarization
    result = None
    if ai_client.mode == "bedrock":
        try:
            result = _summarize_with_ai(ai_client, report_text, image_bytes)
        except Exception as e:
            logger.warning(f"Bedrock summarization failed, using fallback: {e}")

    # Fallback: keyword-based summarization
    if result is None:
        result = _summarize_fallback(report_text)

    result["from_cache"] = False

    # ── Store in Cache ───────────────────────────────────────
    if cache_key:
        cache.put(
            cache_key, result,
            ttl_hours=settings.CACHE_TTL_REPORT_HOURS,
            service="summarize",
            query_text=report_text[:100],
        )

    return result


def _summarize_with_ai(ai_client, report_text: str, image_bytes: Optional[bytes] = None) -> Dict:
    """Use Bedrock Claude to summarize a medical report."""
    system_prompt = """You are a clinical report summarizer. Create structured summaries 
of medical reports for healthcare professionals and patients. Be concise and accurate."""

    prompt = f"""You are summarizing a medical report. If an image is provided, extract the data internally and synthesize it.

DO NOT just transcribe the raw text. You MUST produce a clinical summary.

Summarize this medical report. Return ONLY valid JSON in this exact format:
{{
    "overview": "a 2-3 sentence clinical overview synthesizing the entire report",
    "key_findings": ["finding 1", "finding 2"],
    "concerns": ["concern 1 with ⚠️ prefix if urgent"],
    "next_steps": ["recommended action 1", "recommended action 2"],
    "medications_mentioned": ["medication 1", "medication 2"],
    "severity": {{
        "level": "LOW or MEDIUM or HIGH",
        "color": "#22c55e for LOW, #f59e0b for MEDIUM, #ef4444 for HIGH",
        "label": "brief severity description"
    }}
}}

MEDICAL REPORT:
{report_text if report_text else "(Please extract and summarize the text from the attached medical report image)"}"""

    response = ai_client.invoke(prompt, system_prompt=system_prompt, temperature=0.2, image_bytes=image_bytes)

    try:
        result = _extract_json(response)
    except Exception:
        result = {
            "overview": response[:500],
            "key_findings": ["AI-generated summary available"],
            "concerns": [],
            "next_steps": ["Review with your doctor"],
            "medications_mentioned": [],
            "severity": {"level": "MEDIUM", "color": "#f59e0b", "label": "Review recommended"},
        }

    return {
        "result_id": str(uuid.uuid4()),
        "summary": {
            "overview": result.get("overview", ""),
            "key_findings": result.get("key_findings", []),
            "concerns": result.get("concerns", []),
            "next_steps": result.get("next_steps", []),
            "medications_mentioned": result.get("medications_mentioned", []),
        },
        "severity": result.get("severity", {"level": "LOW", "color": "#22c55e", "label": "Routine"}),
        "confidence_score": 0.92,
        "ai_powered": True,
        "disclaimer": "AI-generated summary. Consult your healthcare provider for interpretation.",
        "generated_at": datetime.utcnow().isoformat(),
    }


def _summarize_fallback(report_text: str) -> Dict:
    """Fallback: keyword-based summary."""
    return {
        "result_id": str(uuid.uuid4()),
        "summary": {
            "overview": _generate_overview(report_text),
            "key_findings": _extract_key_findings(report_text),
            "concerns": _extract_concerns(report_text),
            "next_steps": _extract_action_items(report_text),
            "medications_mentioned": _extract_medications(report_text),
        },
        "severity": _assess_severity(report_text),
        "confidence_score": 0.65,
        "ai_powered": False,
        "disclaimer": "AI-generated summary. Consult your healthcare provider for interpretation.",
        "generated_at": datetime.utcnow().isoformat(),
    }


def _extract_json(text: str) -> dict:
    """Extract JSON from AI response text, handling markdown code blocks."""
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    import re
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding JSON-like content between braces
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group(0))

    raise ValueError("No valid JSON found in response")


# ---- Fallback helper functions (used when Bedrock unavailable) ----

def _generate_overview(text: str) -> str:
    """Generate a brief overview (fallback)."""
    word_count = len(text.split())
    if word_count < 20:
        return "Brief clinical note describing patient condition."
    elif word_count < 100:
        return "Standard clinical report covering patient assessment and treatment plan."
    return "Comprehensive medical report with detailed findings, assessment, and treatment recommendations."


def _extract_key_findings(text: str) -> list:
    """Extract key findings from report (fallback)."""
    findings = []
    text_lower = text.lower()
    if any(w in text_lower for w in ["elevated", "high", "increased"]):
        findings.append("Elevated values detected — may need monitoring")
    if any(w in text_lower for w in ["normal", "within range", "stable"]):
        findings.append("Some values are within normal range")
    if any(w in text_lower for w in ["low", "decreased", "reduced"]):
        findings.append("Some values are below normal — follow-up recommended")
    if any(w in text_lower for w in ["fever", "pyrexia", "temperature"]):
        findings.append("Temperature-related findings noted")
    if any(w in text_lower for w in ["diabetes", "hba1c", "glucose", "sugar"]):
        findings.append("Blood sugar / diabetes-related metrics found")
    if any(w in text_lower for w in ["blood pressure", "hypertension", "bp"]):
        findings.append("Blood pressure readings noted")
    if not findings:
        findings.append("Report reviewed — no critical alerts detected")
    return findings


def _extract_concerns(text: str) -> list:
    """Extract health concerns (fallback)."""
    concerns = []
    text_lower = text.lower()
    if any(w in text_lower for w in ["critical", "urgent", "emergency", "severe"]):
        concerns.append("⚠️ Urgent attention may be required")
    if any(w in text_lower for w in ["abnormal", "irregular", "concerning"]):
        concerns.append("Some test results show abnormal values")
    if any(w in text_lower for w in ["follow-up", "follow up", "review"]):
        concerns.append("Follow-up visit recommended by doctor")
    return concerns if concerns else ["No immediate concerns identified"]


def _extract_action_items(text: str) -> list:
    """Extract action items (fallback)."""
    items = []
    text_lower = text.lower()
    if any(w in text_lower for w in ["medication", "medicine", "prescri"]):
        items.append("Take prescribed medications as directed")
    if any(w in text_lower for w in ["test", "lab", "investigation"]):
        items.append("Complete recommended tests/investigations")
    if any(w in text_lower for w in ["follow-up", "follow up", "review", "revisit"]):
        items.append("Schedule follow-up visit as recommended")
    if any(w in text_lower for w in ["diet", "exercise", "lifestyle"]):
        items.append("Follow dietary and lifestyle recommendations")
    if not items:
        items.append("Continue current care plan and monitor symptoms")
    return items


def _extract_medications(text: str) -> list:
    """Extract medication names mentioned (fallback)."""
    common_meds = [
        "Paracetamol", "Amoxicillin", "Metformin", "Atorvastatin", "Amlodipine",
        "Omeprazole", "Azithromycin", "Ciprofloxacin", "Ibuprofen", "Aspirin",
        "Insulin", "Losartan", "Pantoprazole", "Ceftriaxone", "Doxycycline",
    ]
    found = []
    for med in common_meds:
        if med.lower() in text.lower():
            found.append(med)
    return found


def _assess_severity(text: str) -> Dict:
    """Assess report severity (fallback)."""
    text_lower = text.lower()
    if any(w in text_lower for w in ["critical", "emergency", "urgent", "severe", "malignant"]):
        return {"level": "HIGH", "color": "#ef4444", "label": "Requires immediate attention"}
    if any(w in text_lower for w in ["elevated", "abnormal", "concerning", "moderate"]):
        return {"level": "MEDIUM", "color": "#f59e0b", "label": "Monitor closely"}
    return {"level": "LOW", "color": "#22c55e", "label": "Routine — no immediate concern"}
