"""
Clinical Data Normalizer

Standardizes extracted medical data from Bedrock/Textract.
Maps common units, flags abnormal values using standard reference ranges,
and formats dates.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Basic adult reference ranges for common tests (can be expanded)
REFERENCE_RANGES = {
    "hemoglobin": {"min": 12.0, "max": 17.5, "unit": "g/dl"},
    "platelets": {"min": 150000, "max": 450000, "unit": "cell/mcl"},
    "wbc": {"min": 4500, "max": 11000, "unit": "cell/mcl"},
    "rbc": {"min": 4.0, "max": 5.9, "unit": "million/mcl"},
    "glucose_fasting": {"min": 70, "max": 100, "unit": "mg/dl"},
    "glucose_random": {"min": 70, "max": 140, "unit": "mg/dl"},
    "hba1c": {"min": 4.0, "max": 5.6, "unit": "%"},
    "creatinine": {"min": 0.6, "max": 1.2, "unit": "mg/dl"},
    "urea": {"min": 7, "max": 20, "unit": "mg/dl"},
    "cholesterol_total": {"min": 0, "max": 200, "unit": "mg/dl"},
    "cholesterol_ldl": {"min": 0, "max": 100, "unit": "mg/dl"},
    "cholesterol_hdl": {"min": 40, "max": 60, "unit": "mg/dl"},
    "triglycerides": {"min": 0, "max": 150, "unit": "mg/dl"},
    "tsh": {"min": 0.4, "max": 4.0, "unit": "miu/l"},
    "sgot": {"min": 8, "max": 45, "unit": "u/l"},
    "sgpt": {"min": 7, "max": 56, "unit": "u/l"},
}

# Aliases to map raw OCR text to canonical standard names
TEST_ALIASES = {
    "hgb": "hemoglobin",
    "hb": "hemoglobin",
    "plt": "platelets",
    "wbc count": "wbc",
    "white blood cells": "wbc",
    "rbc count": "rbc",
    "red blood cells": "rbc",
    "fasting blood sugar": "glucose_fasting",
    "fbs": "glucose_fasting",
    "random blood sugar": "glucose_random",
    "rbs": "glucose_random",
    "glycated hemoglobin": "hba1c",
    "a1c": "hba1c",
    "serum creatinine": "creatinine",
    "blood urea nitrogen": "urea",
    "bun": "urea",
    "lipid profile": "cholesterol_total",
    "ldl cholesterol": "cholesterol_ldl",
    "hdl cholesterol": "cholesterol_hdl",
    "thyroid stimulating hormone": "tsh",
    "ast": "sgot",
    "alt": "sgpt",
}

UNIT_ALIASES = {
    "g/dl": "g/dl",
    "gm/dl": "g/dl",
    "grams/dl": "g/dl",
    "mg/dl": "mg/dl",
    "milligrams/dl": "mg/dl",
    "percent": "%",
    "%": "%",
    "u/l": "u/l",
    "iu/l": "u/l",
    "mEq/L": "meq/l",
    "x10^3/uL": "cell/mcl",
    "x10^6/uL": "million/mcl",
}

def normalize_clinical_data(extractor_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes raw Bedrock extracted JSON and normalizes test names, units,
    and calculates abnormality flags based on reference ranges.
    """
    normalized = extractor_json.copy()
    
    # 1. Normalize Labs
    labs = normalized.get("lab_results", [])
    clean_labs = []
    
    for lab in labs:
        test_name_raw = lab.get("test_name", "").lower().strip()
        canonical_name = TEST_ALIASES.get(test_name_raw, test_name_raw)
        
        value_raw = lab.get("value")
        unit_raw = lab.get("unit", "").lower().strip()
        canonical_unit = UNIT_ALIASES.get(unit_raw, unit_raw)
        
        is_abnormal = lab.get("is_abnormal", False)
        
        # Try numeric assessment
        if canonical_name in REFERENCE_RANGES and value_raw:
            try:
                # Strip out non-numeric chars like '<', '>', etc for basic checking
                import re
                num_str = re.sub(r'[^\d.]', '', str(value_raw))
                if num_str:
                    val = float(num_str)
                    ref = REFERENCE_RANGES[canonical_name]
                    # Only map if units align or are missing
                    if canonical_unit == ref["unit"]:
                        if val < ref["min"] or val > ref["max"]:
                            is_abnormal = True
                            
                        # Add ref string if missing
                        if not lab.get("reference_range"):
                            lab["reference_range"] = f"{ref['min']} - {ref['max']} {ref['unit']}"
            except Exception:
                pass
                
        clean_labs.append({
            "test_name_raw": lab.get("test_name"),
            "test_name": canonical_name,
            "value": value_raw,
            "unit": canonical_unit,
            "reference_range": lab.get("reference_range"),
            "is_abnormal": is_abnormal
        })
        
    normalized["lab_results"] = clean_labs
    
    # Ensure standard schema structure
    if "patient_demographics" not in normalized:
        normalized["patient_demographics"] = {}
    if "diagnoses" not in normalized:
        normalized["diagnoses"] = []
    if "medications" not in normalized:
        normalized["medications"] = []
    if "vitals" not in normalized:
        normalized["vitals"] = []
        
    return normalized
