"""
Disease Predictor

Symptom-based disease prediction with AI explanation.
Integrates Medicure ML patterns with Bedrock for reasoning.
Integrated with AWS DynamoDB caching — sorted symptoms produce
order-independent cache keys.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.bedrock_client import BedrockClient, get_bedrock_client
from app.models.ai_models import DiseasePrediction, ReasoningStep
from app.core.cache_client import CacheClient, get_cache_client
from app.core.config import settings

logger = logging.getLogger(__name__)

# Rule-based symptom-disease mapping (from Medicure patterns + medical knowledge)
SYMPTOM_DISEASE_MAP = {
    "fever": ["Common Cold", "Influenza", "Dengue", "Typhoid", "Malaria", "COVID-19"],
    "cough": ["Common Cold", "Influenza", "Bronchitis", "Pneumonia", "Tuberculosis", "COVID-19"],
    "headache": ["Migraine", "Tension Headache", "Sinusitis", "Hypertension", "Dengue"],
    "fatigue": ["Anemia", "Diabetes", "Hypothyroidism", "Dengue", "Tuberculosis"],
    "body pain": ["Influenza", "Dengue", "Chikungunya", "Malaria"],
    "sore throat": ["Common Cold", "Viral Pharyngitis", "Tonsillitis", "Strep Throat"],
    "runny nose": ["Common Cold", "Allergic Rhinitis", "Sinusitis"],
    "nausea": ["Gastroenteritis", "Food Poisoning", "Migraine", "Dengue"],
    "vomiting": ["Gastroenteritis", "Food Poisoning", "Dengue", "Cholera"],
    "diarrhea": ["Gastroenteritis", "Food Poisoning", "Cholera", "IBS"],
    "chest pain": ["Angina", "GERD", "Costochondritis", "Pneumonia"],
    "shortness of breath": ["Asthma", "COPD", "Pneumonia", "Heart Failure", "COVID-19"],
    "joint pain": ["Rheumatoid Arthritis", "Osteoarthritis", "Chikungunya", "Dengue", "Gout"],
    "skin rash": ["Allergic Dermatitis", "Eczema", "Dengue", "Chickenpox", "Measles"],
    "abdominal pain": ["Gastritis", "Appendicitis", "Peptic Ulcer", "Gallstones", "IBS"],
    "weight loss": ["Diabetes", "Hyperthyroidism", "Tuberculosis", "Cancer"],
    "frequent urination": ["Diabetes", "UTI", "Prostate Enlargement"],
    "dizziness": ["Vertigo", "Anemia", "Hypotension", "Dehydration"],
    "blurred vision": ["Diabetes", "Hypertension", "Glaucoma", "Cataracts"],
    "back pain": ["Lumbar Strain", "Herniated Disc", "Kidney Stones", "UTI"],
}

RECOMMENDED_TESTS = {
    "Common Cold": ["CBC"],
    "Influenza": ["CBC", "Rapid Influenza Test"],
    "Dengue": ["CBC", "Dengue NS1 Antigen", "Dengue IgM/IgG"],
    "Typhoid": ["Widal Test", "Blood Culture", "CBC"],
    "Malaria": ["Malaria Smear", "Rapid Diagnostic Test", "CBC"],
    "Diabetes": ["Fasting Blood Sugar", "HbA1c", "Oral Glucose Tolerance Test"],
    "Hypertension": ["ECG", "Lipid Profile", "Kidney Function Tests"],
    "Anemia": ["CBC", "Iron Studies", "Vitamin B12", "Folate"],
    "Tuberculosis": ["Chest X-Ray", "Sputum AFB", "Mantoux Test"],
    "COVID-19": ["RT-PCR", "Rapid Antigen Test", "CT Chest"],
    "Pneumonia": ["Chest X-Ray", "CBC", "Sputum Culture"],
    "UTI": ["Urinalysis", "Urine Culture"],
    "Gastroenteritis": ["Stool Examination", "CBC"],
    "Asthma": ["Pulmonary Function Test", "Peak Flow Meter"],
    "Hypothyroidism": ["TSH", "T3", "T4"],
}


class DiseasePredictor:
    """Symptom-based disease prediction with AI reasoning."""

    SYSTEM_PROMPT = """You are a medical AI assistant. Given predicted diseases from a symptom analysis,
explain the prediction in simple, understandable language for the doctor and patient.
Do NOT diagnose — only explain the AI reasoning. Always recommend consulting a doctor."""

    EXPLANATION_PROMPT = """Based on these symptoms: {symptoms}

The prediction model suggests:
{predictions}

Recommended tests: {tests}

Provide a clear, simple explanation of why these diseases were predicted based on the symptoms.
Include a safety note to consult a doctor. Return JSON:
{{
  "ai_explanation": "Clear explanation in simple language",
  "confidence": 0.85
}}

Respond ONLY with valid JSON."""

    def __init__(self, ai_client: Optional[BedrockClient] = None):
        self.ai_client = ai_client or get_bedrock_client()
        self.cache = get_cache_client()
        logger.info("DiseasePredictor initialized with cache")

    def predict(self, symptoms: List[str], patient_id: Optional[str] = None) -> DiseasePrediction:
        """Predict diseases based on symptoms. Results are cached with sorted symptom keys."""
        # ── Check Cache (sorted symptoms = order-independent key) ─
        sorted_symptoms = sorted(s.lower().strip() for s in symptoms)
        cache_key = CacheClient.generate_cache_key("disease", *sorted_symptoms)
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.info(f"Disease prediction CACHE HIT for: {sorted_symptoms}")
            cached["from_cache"] = True
            return DiseasePrediction(**cached)

        # Score diseases by symptom match frequency
        disease_scores: Dict[str, float] = {}
        total_symptoms = len(symptoms)

        for symptom in symptoms:
            symptom_lower = symptom.lower().strip()
            for key, diseases in SYMPTOM_DISEASE_MAP.items():
                if key in symptom_lower or symptom_lower in key:
                    for disease in diseases:
                        disease_scores[disease] = disease_scores.get(disease, 0) + 1

        if not disease_scores:
            return DiseasePrediction(
                prediction_id=str(uuid.uuid4()),
                patient_id=patient_id,
                symptoms=symptoms,
                predicted_diseases=[],
                recommended_tests=["General Health Checkup", "CBC"],
                ai_explanation="Unable to match symptoms to known disease patterns. Please consult a doctor for proper evaluation.",
                confidence_score=0.0,
            )

        # Normalize scores to probabilities
        max_score = max(disease_scores.values())
        sorted_diseases = sorted(disease_scores.items(), key=lambda x: x[1], reverse=True)[:5]

        predicted = []
        for disease, score in sorted_diseases:
            probability = round(score / total_symptoms, 2) if total_symptoms > 0 else 0
            confidence = round(score / max_score * 0.9, 2)  # Max confidence 0.9
            predicted.append({
                "disease": disease,
                "probability": min(probability, 0.95),
                "confidence": min(confidence, 0.95),
            })

        # Collect recommended tests
        tests = set()
        for disease, _ in sorted_diseases[:3]:
            tests.update(RECOMMENDED_TESTS.get(disease, []))
        recommended_tests = list(tests)[:8]

        # Get AI explanation
        try:
            pred_text = "\n".join(
                f"- {p['disease']}: {p['probability']*100:.0f}% probability"
                for p in predicted
            )
            prompt = self.EXPLANATION_PROMPT.format(
                symptoms=", ".join(symptoms),
                predictions=pred_text,
                tests=", ".join(recommended_tests),
            )
            explanation_json = self.ai_client.invoke_json(
                prompt=prompt, system_prompt=self.SYSTEM_PROMPT
            )
            ai_explanation = explanation_json.get("ai_explanation", "")
            overall_confidence = float(explanation_json.get("confidence", predicted[0]["confidence"]))
        except Exception as e:
            logger.warning(f"AI explanation generation failed: {e}")
            ai_explanation = f"Based on the symptoms ({', '.join(symptoms)}), the system identified potential conditions. Please consult a qualified healthcare professional for proper diagnosis."
            overall_confidence = predicted[0]["confidence"] if predicted else 0.0

        reasoning_steps = [
            ReasoningStep(
                step_number=1,
                description="Analyzed input symptoms against known disease patterns",
                evidence=f"Matched {len(symptoms)} symptoms",
                confidence=0.85,
            ),
            ReasoningStep(
                step_number=2,
                description="Ranked diseases by symptom overlap frequency",
                evidence=f"Top match: {predicted[0]['disease']}" if predicted else "No strong match",
                confidence=overall_confidence,
            ),
            ReasoningStep(
                step_number=3,
                description="Generated AI explanation for predicted conditions",
                evidence="Bedrock Claude reasoning",
                confidence=overall_confidence,
            ),
        ]

        result = DiseasePrediction(
            prediction_id=str(uuid.uuid4()),
            patient_id=patient_id,
            symptoms=symptoms,
            predicted_diseases=predicted,
            recommended_tests=recommended_tests,
            reasoning_steps=reasoning_steps,
            ai_explanation=ai_explanation,
            confidence_score=overall_confidence,
        )

        # ── Store in Cache ───────────────────────────────────────
        self.cache.put(
            cache_key, result.model_dump(),
            ttl_hours=settings.CACHE_TTL_DISEASE_HOURS,
            service="disease",
            query_text=", ".join(sorted_symptoms),
        )

        return result
