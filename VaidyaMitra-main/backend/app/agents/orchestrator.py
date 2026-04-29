"""
Master Orchestrator Agent

Agentic AI orchestration layer that determines intent and routes
requests to the appropriate sub-agent.
Integrated with AWS DynamoDB caching for AI query results.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from app.services.bedrock_client import BedrockClient, get_bedrock_client
from app.services.summary_generator import SummaryGenerator
from app.services.change_detector import ChangeDetector
from app.services.disease_predictor import DiseasePredictor
from app.services.generic_medicine_engine import GenericMedicineEngine
from app.services.rag_service import RAGService, get_rag_service
from app.services.privacy_layer import PrivacyLayer
from app.models.clinical import ClinicalVisit
from app.core.cache_client import CacheClient, get_cache_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class AgentIntent:
    """Enum-like class for agent intents."""
    CLINICAL_SUMMARY = "clinical_summary"
    CHANGE_DETECTION = "change_detection"
    DISEASE_PREDICTION = "disease_prediction"
    GENERIC_MEDICINE = "generic_medicine"
    CLINICAL_QUERY = "clinical_query"
    RISK_MONITORING = "risk_monitoring"
    UNKNOWN = "unknown"


class OrchestratorAgent:
    """
    Master Orchestrator Agent for VAIDYAMITRA.

    Determines user intent and routes to the correct sub-agent:
    - Clinical Summary Agent
    - Change Detection Agent
    - Disease Prediction Agent
    - Generic Medicine Agent
    - Query Response Agent
    - Risk Monitoring Agent
    """

    INTENT_PROMPT = """Classify the following user request into one of these categories:
- clinical_summary: Wants a clinical summary of a patient visit
- change_detection: Wants to compare visits or detect changes
- disease_prediction: Has symptoms and wants disease prediction
- generic_medicine: Wants generic/Jan Aushadhi alternative for a medicine
- clinical_query: General clinical question about a patient
- risk_monitoring: Wants risk assessment or monitoring alerts

User request: "{query}"

Return JSON:
{{
  "intent": "one_of_the_categories_above",
  "confidence": 0.95,
  "entities": {{}}
}}

Respond ONLY with valid JSON."""

    def __init__(self):
        self.ai_client = get_bedrock_client()
        self.privacy_layer = PrivacyLayer()
        self.summary_generator = SummaryGenerator(self.ai_client)
        self.change_detector = ChangeDetector(self.ai_client)
        self.disease_predictor = DiseasePredictor(self.ai_client)
        self.medicine_engine = GenericMedicineEngine(self.ai_client)
        self.rag_service = get_rag_service()
        self.cache = get_cache_client()
        logger.info("Orchestrator Agent initialized with all sub-agents and cache")

    def classify_intent(self, query: str) -> Dict[str, Any]:
        """Classify user intent from natural language query."""
        # Quick keyword-based classification (fast path)
        query_lower = query.lower()

        if any(w in query_lower for w in ["summary", "summarize", "summarise", "overview"]):
            return {"intent": AgentIntent.CLINICAL_SUMMARY, "confidence": 0.90}

        if any(w in query_lower for w in ["change", "differ", "compare", "trend"]):
            return {"intent": AgentIntent.CHANGE_DETECTION, "confidence": 0.90}

        if any(w in query_lower for w in ["symptom", "predict", "disease", "diagnos"]):
            return {"intent": AgentIntent.DISEASE_PREDICTION, "confidence": 0.90}

        if any(w in query_lower for w in ["generic", "jan aushadhi", "alternative", "cheaper", "medicine price", "affordable", "substitute"]):
            return {"intent": AgentIntent.GENERIC_MEDICINE, "confidence": 0.90}

        if any(w in query_lower for w in ["risk", "monitor", "alert", "warning"]):
            return {"intent": AgentIntent.RISK_MONITORING, "confidence": 0.85}

        # Fall back to AI classification for ambiguous queries
        try:
            prompt = self.INTENT_PROMPT.format(query=query)
            result = self.ai_client.invoke_json(prompt=prompt)
            return result
        except Exception as e:
            logger.warning(f"AI intent classification failed: {e}")
            return {"intent": AgentIntent.CLINICAL_QUERY, "confidence": 0.50}

    def process_request(
        self,
        query: str,
        patient_id: Optional[str] = None,
        clinical_visit: Optional[ClinicalVisit] = None,
        previous_visit: Optional[ClinicalVisit] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a request through the agent pipeline.
        
        1. Apply privacy masking
        2. Check cache for identical masked query
        3. Classify intent
        4. Route to sub-agent
        5. Cache and return structured response
        """
        # Step 1: Privacy masking on the query
        masked_data = self.privacy_layer.detect_and_mask(query)
        masked_query = masked_data.masked_text

        # Step 2: Check cache (only for text-only queries, skip when clinical visit data provided)
        cache_key = None
        if not clinical_visit and not previous_visit:
            cache_key = CacheClient.generate_cache_key("query", masked_query.lower().strip())
            cached = self.cache.get(cache_key)
            if cached is not None:
                logger.info(f"Orchestrator CACHE HIT for query: {masked_query[:50]}")
                cached["from_cache"] = True
                return cached

        # Step 3: Classify intent
        intent_result = self.classify_intent(masked_query)
        intent = intent_result.get("intent", AgentIntent.UNKNOWN)
        confidence = intent_result.get("confidence", 0.0)

        logger.info(f"Intent: {intent} (confidence: {confidence})")

        # Step 3: Route to sub-agent
        try:
            if intent == AgentIntent.CLINICAL_SUMMARY and clinical_visit:
                summary = self.summary_generator.generate_summary(clinical_visit)
                result = {
                    "agent": "clinical_summary",
                    "intent": intent,
                    "intent_confidence": confidence,
                    "result": summary.model_dump(),
                    "pii_masked": masked_data.entities_detected_count > 0,
                }

            elif intent == AgentIntent.CHANGE_DETECTION and clinical_visit:
                report = self.change_detector.detect_changes(clinical_visit, previous_visit)
                result = {
                    "agent": "change_detection",
                    "intent": intent,
                    "intent_confidence": confidence,
                    "result": report.model_dump(),
                    "pii_masked": masked_data.entities_detected_count > 0,
                }

            elif intent == AgentIntent.DISEASE_PREDICTION:
                # Extract symptoms from query
                symptoms = self._extract_symptoms(masked_query)
                prediction = self.disease_predictor.predict(symptoms, patient_id)
                result = {
                    "agent": "disease_prediction",
                    "intent": intent,
                    "intent_confidence": confidence,
                    "result": prediction.model_dump(),
                    "pii_masked": masked_data.entities_detected_count > 0,
                }

            elif intent == AgentIntent.GENERIC_MEDICINE:
                medicine_name = self._extract_medicine_name(masked_query)
                med_result = self.medicine_engine.find_alternatives(medicine_name)
                result = {
                    "agent": "generic_medicine",
                    "intent": intent,
                    "intent_confidence": confidence,
                    "result": med_result.model_dump(),
                    "pii_masked": masked_data.entities_detected_count > 0,
                }

            else:
                # General clinical query — use RAG with Strict Persona
                grounded_prompt = self.rag_service.build_grounded_prompt(
                    base_prompt=f"User Query: {masked_query}",
                    query=masked_query,
                    doc_type="clinical",
                )
                
                strict_system_prompt = (
                    "You are VaidyaMitra's elite clinical AI assistant. "
                    "CRITICAL INSTRUCTION: You MUST ONLY answer questions related to medicine, healthcare, diseases, clinical data, or the VaidyaMitra platform. "
                    "If the user asks an unrelated question (e.g., 'who won the world cup', 'how to code in python', 'what is the capital of France'), "
                    "you MUST completely ignore the direct answer, gracefully state that you specialize in healthcare, and creatively pivot the conversation back to health, wellness, or medicine. "
                    "Respond with valid JSON containing exactly three keys: 'response' (your text), 'sources' (empty list if none), and 'confidence' (float 0.0-1.0)."
                )
                
                response = self.ai_client.invoke_json(
                    prompt=grounded_prompt,
                    system_prompt=strict_system_prompt,
                )
                result = {
                    "agent": "query_response",
                    "intent": intent,
                    "intent_confidence": confidence,
                    "result": response,
                    "pii_masked": masked_data.entities_detected_count > 0,
                }

        except Exception as e:
            logger.error(f"Agent processing error: {e}")
            return {
                "agent": "error",
                "intent": intent,
                "error": str(e),
                "pii_masked": masked_data.entities_detected_count > 0,
            }

        # Step 5: Cache the result
        if cache_key and result:
            result["from_cache"] = False
            self.cache.put(
                cache_key, result,
                ttl_hours=settings.CACHE_TTL_QUERY_HOURS,
                service="query",
                query_text=masked_query[:100],
            )

        return result

    def _extract_symptoms(self, query: str) -> List[str]:
        """Extract symptom keywords from a query."""
        symptom_keywords = [
            "fever", "cough", "headache", "fatigue", "body pain",
            "sore throat", "runny nose", "nausea", "vomiting", "diarrhea",
            "chest pain", "shortness of breath", "joint pain", "skin rash",
            "abdominal pain", "weight loss", "frequent urination", "dizziness",
            "blurred vision", "back pain",
        ]
        found = []
        query_lower = query.lower()
        for symptom in symptom_keywords:
            if symptom in query_lower:
                found.append(symptom)
        return found if found else [query]

    def _extract_medicine_name(self, query: str) -> str:
        """Extract medicine name from a query."""
        # Remove common prefixes
        for prefix in ["find generic for", "generic alternative for", "jan aushadhi for",
                       "alternative for", "cheaper option for", "affordable alternative for",
                       "what is the generic for", "find me"]:
            if query.lower().startswith(prefix):
                return query[len(prefix):].strip()
        return query.strip()


_orchestrator: Optional[OrchestratorAgent] = None


def get_orchestrator() -> OrchestratorAgent:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent()
    return _orchestrator
