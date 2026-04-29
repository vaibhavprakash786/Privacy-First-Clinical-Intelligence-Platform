"""
Generic Medicine Engine (Jan Aushadhi)

Core USP of VaidyaMitra — finds affordable Jan Aushadhi generic alternatives
for branded medicines and calculates patient savings.
Integrated with AWS DynamoDB caching for fast repeated lookups.
"""

import logging
import uuid
import json
from typing import Any, Dict, List, Optional

from app.services.bedrock_client import BedrockClient, get_bedrock_client
from app.models.ai_models import DrugAlternative, GenericMedicineResult
from app.services.pmbjp_catalog import get_catalog
from app.core.cache_client import CacheClient, get_cache_client
from app.core.config import settings

logger = logging.getLogger(__name__)

class GenericMedicineEngine:
    """
    Jan Aushadhi Generic Medicine Engine powered by Gen AI and the Official PMBJP Catalog.
    """

    COMPOSITION_EXTRACTION_PROMPT = """You are a clinical pharmacist.
The user is searching for affordable generic alternatives for the following medicine:

"{query}"

{ocr_context}

Identify the exact branded medicine being asked about and its active generic composition.
CRITICAL INSTRUCTION: Use standard Indian PMBJP spelling for generics. For example, use "Amoxycillin" instead of "Amoxicillin", "Paracetamol" instead of "Acetaminophen", and include full salt names like "Potassium Clavulanate".

Respond ONLY with valid JSON in this exact format:
{{
  "identified_brand_name": "Standardized Brand Name",
  "composition": "Full active generic ingredients (e.g., Amoxycillin + Potassium Clavulanate)",
  "estimated_branded_mrp": 150.0  // Give a realistic estimated price in INR for the branded version
}}
"""

    CLINICAL_DETAILS_PROMPT = """You are VaidyaMitra's expert pharmacist creating a patient-friendly clinical dashboard.
CRITICAL INSTRUCTION: You MUST ONLY provide medical and healthcare-related information. If the user's initial query or the extracted context contains completely unrelated topics (like sports, politics, coding, etc.), IGNORE them entirely and focus ONLY on the medicine requested.

Compare the Branded Medicine "{brand_name}" to its EXACT official Jan Aushadhi generic equivalent: "{pmbjp_generic_name}" (PMBJP Code: {pmbjp_code}, MRP: ₹{pmbjp_mrp}).

Both contain the composition: "{composition}".

Generate a comprehensive clinical profile for the dashboard.
Respond ONLY with valid JSON in exactly this format. Do NOT include markdown blocks.
{{
  "comprehensive_comparison": "A 3-sentence comparison explaining the price difference, confirming they belong to the same therapeutic group ({group_name}), and guaranteeing exact bioequivalence.",
  "uses": ["List of 3 primary medical uses / indications"],
  "side_effects": ["List of 3 common side effects to watch out for"],
  "precautions": {{
    "pregnancy": "Safe / Consult Doctor / Unsafe with brief reason",
    "driving": "Safe / May cause dizziness",
    "alcohol": "Safe / Unsafe interaction warning"
  }},
  "dosage_guidelines": "General advice on when and how to take it (e.g., Take after meals)."
}}
"""

    def __init__(self, ai_client: Optional[BedrockClient] = None):
        self.ai_client = ai_client or get_bedrock_client()
        self.catalog = get_catalog()
        self.cache = get_cache_client()
        logger.info("GenericMedicineEngine initialized with AI backend, Official Catalog, and Cache")

    def search(self, query: str) -> List[Dict[str, Any]]:
        return []

    def find_alternatives(self, medicine_name: str, extracted_text: Optional[str] = None) -> GenericMedicineResult:
        # ── Check Cache ──────────────────────────────────────────
        cache_key = CacheClient.generate_cache_key(
            "janaushadhi", medicine_name.lower().strip(), extracted_text or ""
        )
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.info(f"Jan Aushadhi CACHE HIT for: {medicine_name}")
            cached["from_cache"] = True
            return GenericMedicineResult(**cached)

        ocr_context = f"\nExtra context extracted from image OCR (may contain noise): {extracted_text}\n" if extracted_text else ""
        
        # Step 1: Extract Composition & Brand details
        comp_prompt = self.COMPOSITION_EXTRACTION_PROMPT.format(query=medicine_name, ocr_context=ocr_context)
        
        try:
            comp_response = self.ai_client.invoke_json(
                prompt=comp_prompt,
                system_prompt="You are a JSON-only API.",
                max_tokens=1000,
                temperature=0.1
            )
            
            brand_name = comp_response.get("identified_brand_name", medicine_name)
            composition = comp_response.get("composition", "")
            branded_price = float(comp_response.get("estimated_branded_mrp", 100.0))
            
            # Step 2: Match against Official PMBJP Catalog
            pmbjp_match = self.catalog.find_best_match(composition)
            
            if not pmbjp_match:
                # Fallback if no exact match is found
                return self._create_fallback_response(brand_name, composition)
                
            # Step 3: Generate Detailed Clinical Profile
            clinical_prompt = self.CLINICAL_DETAILS_PROMPT.format(
                brand_name=brand_name,
                pmbjp_generic_name=pmbjp_match.generic_name,
                pmbjp_code=pmbjp_match.drug_code,
                pmbjp_mrp=pmbjp_match.mrp,
                composition=composition,
                group_name=pmbjp_match.group_name
            )
            
            clinical_response = self.ai_client.invoke_json(
                prompt=clinical_prompt,
                system_prompt="You are a JSON-only API. Respond only with valid JSON.",
                max_tokens=1500,
                temperature=0.2
            )
            
            # Step 4: Construct the final enriched payload
            jan_price = float(pmbjp_match.mrp)
            savings_amount = max(0.0, branded_price - jan_price)
            savings_pct = (savings_amount / branded_price * 100) if branded_price > 0 else 0.0

            # Pack official PMBJP data into the strength/manufacturer fields for standard rendering
            enhanced_strength = f"Unit: {pmbjp_match.unit_size} | {pmbjp_match.group_name}"
            
            alt = DrugAlternative(
                generic_name=pmbjp_match.generic_name,
                composition=composition,
                strength=enhanced_strength,
                jan_aushadhi_price=jan_price,
                branded_price=branded_price,
                savings_amount=round(savings_amount, 2),
                savings_percentage=round(savings_pct, 1),
                manufacturer=pmbjp_match.drug_code, 
                is_jan_aushadhi=True,
            )
            
            # We pack the comprehensive JSON into safety_note to pass it cleanly to the frontend
            # The frontend will parse this JSON to build the dashboard
            safety_payload = json.dumps({
                "uses": clinical_response.get("uses", []),
                "side_effects": clinical_response.get("side_effects", []),
                "precautions": clinical_response.get("precautions", {}),
                "dosage_guidelines": clinical_response.get("dosage_guidelines", "")
            })

            result = GenericMedicineResult(
                result_id=str(uuid.uuid4()),
                brand_name=brand_name,
                composition=composition,
                alternatives=[alt],
                total_savings=round(savings_amount, 2),
                ai_explanation=clinical_response.get("comprehensive_comparison", ""),
                safety_note=safety_payload,  # Repurposed to hold the JSON clinical details
                confidence_score=0.98
            )

            # ── Store in Cache ───────────────────────────────────
            self.cache.put(
                cache_key, result.model_dump(),
                ttl_hours=settings.CACHE_TTL_JANAUSHADHI_HOURS,
                service="janaushadhi",
                query_text=medicine_name,
            )

            return result

        except Exception as e:
            logger.error(f"AI Jan Aushadhi Search Pipeline failed: {e}")
            return self._create_fallback_response(medicine_name, "")
            
    def _create_fallback_response(self, brand_name: str, composition: str) -> GenericMedicineResult:
        return GenericMedicineResult(
            result_id=str(uuid.uuid4()),
            brand_name=brand_name,
            composition=composition,
            alternatives=[],
            total_savings=0.0,
            ai_explanation="We could not find an exact official PMBJP match for this medicine in the current catalog. Please verify the composition or consult a Jan Aushadhi Kendra.",
            safety_note=json.dumps({"error": "No match found"}),
            confidence_score=0.0,
        )
