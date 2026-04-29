"""
Medicine Identifier Service

Identify medicines, get detailed info, and compare branded vs Jan Aushadhi.
Expanded knowledge base with 50+ Indian market medicines.
Integrated with AWS DynamoDB caching for fast repeated lookups.
"""

import logging
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional

from app.services.bedrock_client import get_bedrock_client
from app.core.cache_client import CacheClient, get_cache_client
from app.core.config import settings

logger = logging.getLogger(__name__)

IDENTIFY_PROMPT_TEMPLATE = """You are an expert clinical pharmacologist for the Indian healthcare system (VaidyaMitra).
The user is asking to identify a medicine based on the following input:

"{query}"

{ocr_context}

Analyze the input. It might be a brand name, generic name, layman term, side effect description, or raw OCR text from an image.
CRITICAL: If the user input contains a typo (e.g., "comblifam" or "croseen"), intelligently autocorrect it to the intended standard medicine name (e.g., "Combiflam" or "Crocin").
Identify the primary medicine the user is looking for and provide a robust generic alternative. 
Then, provide a structured JSON response with exactly this format. Do NOT include markdown blocks around the JSON.

{{
  "brand_name": "Standardized Brand Name (if applicable, else Generic)",
  "generic_name": "Generic/Chemical Name",
  "category": "Therapeutic Category (e.g., Antibiotic, Analgesic)",
  "composition": "Full composition with strengths",
  "usage": "Primary uses / Indications",
  "dosage": "Typical adult dosage",
  "schedule_class": "Drug Schedule (e.g., OTC, Schedule H, Schedule H1, Schedule G, Schedule X)",
  "when_to_take": "Timing rules (e.g., After meals, empty stomach, morning only)",
  "contraindications": ["Condition 1", "Condition 2"],
  "detailed_info": "More information about interactions, how it works, or special warnings",
  "side_effects": ["side effect 1", "side effect 2"],
  "variants": ["Variant 1", "Variant 2"],
  "similar_medicines": ["Alternative Brand 1", "Alternative Brand 2"],
  "generic_equivalent": {{
      "name": "Exact Generic/Chemical Name of the best cost-effective alternative",
      "composition": "Active ingredients and strengths",
      "usage": "Brief usage info specifically for this generic",
      "dosage": "Typical adult dosage for this generic"
  }}
}}

Respond ONLY with valid JSON.
"""

def identify_medicine_ai(query: str, extracted_text: Optional[str] = None) -> Dict:
    """Identify a medicine using Gen AI (handles text queries and OCR text).
    
    Results are cached in DynamoDB with a 7-day TTL. Identical queries 
    return cached results instantly without invoking Bedrock.
    """
    cache = get_cache_client()
    
    # ── Check Cache ──────────────────────────────────────────────
    cache_key = CacheClient.generate_cache_key("medicine_id", query.lower().strip(), extracted_text or "")
    cached = cache.get(cache_key)
    if cached is not None:
        logger.info(f"Medicine identify CACHE HIT for: {query}")
        cached["from_cache"] = True
        return cached

    # ── AI Invocation ────────────────────────────────────────────
    ocr_context = f"\nExtra context extracted from image OCR (may contain noise): {extracted_text}\n" if extracted_text else ""
    prompt = IDENTIFY_PROMPT_TEMPLATE.format(query=query, ocr_context=ocr_context)
    
    ai_client = get_bedrock_client()
    try:
        response_json = ai_client.invoke_json(
            prompt=prompt,
            system_prompt="You are a JSON-only API. Only output valid JSON.",
            max_tokens=2000,
            temperature=0.2
        )
        
        medicine_data = {
            "brand": response_json.get("brand_name", query),
            "generic": response_json.get("generic_name", "Unknown Generic"),
            "category": response_json.get("category", "Unknown Category"),
            "composition": response_json.get("composition", "Unknown Composition"),
            "usage": response_json.get("usage", ""),
            "dosage": response_json.get("dosage", ""),
            "schedule_class": response_json.get("schedule_class", "OTC / Unclassified"),
            "when_to_take": response_json.get("when_to_take", "Consult physician for timing"),
            "contraindications": response_json.get("contraindications", []),
            "detailed_info": response_json.get("detailed_info", "No further details available."),
            "side_effects": response_json.get("side_effects", []),
            "variants": response_json.get("variants", []),
            "similar_medicines": response_json.get("similar_medicines", []),
            "generic_equivalent": response_json.get("generic_equivalent", None)
        }
        
        result = {
            "result_id": str(uuid.uuid4()),
            "identified": True,
            "medicine": medicine_data,
            "generated_at": datetime.utcnow().isoformat(),
            "from_cache": False,
        }

        # ── Store in Cache ───────────────────────────────────────
        cache.put(
            cache_key, result,
            ttl_hours=settings.CACHE_TTL_MEDICINE_HOURS,
            service="medicine_id",
            query_text=query,
        )
        
        return result
        
    except Exception as e:
        logger.error(f"AI Medicine Identification failed: {e}")
        return {
            "result_id": str(uuid.uuid4()),
            "identified": False,
            "query": query,
            "suggestion": "Failed to identify medicine using AI. Please try again with a clearer name.",
            "error": str(e),
            "generated_at": datetime.utcnow().isoformat(),
            "from_cache": False,
        }

# Legacy stubs to prevent import breaking in routes.py until we update it.
def identify_medicine(query: str):
    return identify_medicine_ai(query)

def get_medicine_info(medicine_name: str):
    return identify_medicine_ai(medicine_name)

def compare_medicines(brand_name: str, generic_name: Optional[str] = None):
    # Dummy to prevent breaking frontend if still called. The new UI won't need it.
    return {"error": "Price comparison is deprecated."}

def list_all_medicines():
    return []

def search_medicines(q: str):
    return []
