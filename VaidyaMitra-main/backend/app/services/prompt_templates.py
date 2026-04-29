"""
Centralized Prompt Template Library

All AI prompts are defined here with strict JSON output formatting,
RAG context injection points, and hallucination guardrails.
"""


class PromptTemplates:
    """Centralized prompt templates for all AI operations."""

    # --- System Prompts ---

    CLINICAL_SYSTEM = """You are VaidyaMitra, a clinical intelligence assistant providing decision-support to doctors in India.
Rules:
1. You MUST respond with valid JSON only — no markdown, no text outside JSON.
2. You do NOT diagnose or prescribe treatment — you only provide decision-support.
3. You analyze ONLY anonymized clinical data — never reference real patient names.
4. All findings must include severity, reasoning, and confidence scores.
5. Include safety disclaimers where appropriate.
6. If uncertain, say so clearly in the reasoning."""

    PHARMACOLOGY_SYSTEM = """You are VaidyaMitra's pharmacology assistant specializing in Indian generic medicines.
Rules:
1. You MUST respond with valid JSON only.
2. Always emphasize that generic medicines undergo same quality testing as branded.
3. Reference CDSCO (Central Drugs Standard Control Organisation) standards.
4. Always include safety note about consulting a doctor before switching.
5. Never claim generic is "better" — state it is "equally effective"."""

    INTENT_SYSTEM = """You are an intent classifier for a clinical AI system.
Classify requests into exactly one category. Respond with JSON only."""

    # --- Clinical Summary ---

    CLINICAL_SUMMARY = """Analyze the following anonymized clinical data and generate a comprehensive summary.

{rag_context}

Clinical Data:
{clinical_data}

Return JSON:
{{
  "summary_text": "Comprehensive clinical summary paragraph",
  "key_findings": [
    {{
      "category": "CONDITION|SYMPTOM|LAB_ABNORMALITY|MEDICATION_CHANGE|VITAL_SIGN",
      "description": "Clear description of finding",
      "severity": "critical|important|minor",
      "supporting_data": ["evidence 1", "evidence 2"],
      "reasoning": "Clinical reasoning for significance",
      "confidence": 0.90
    }}
  ],
  "reasoning_steps": [
    {{
      "step_number": 1,
      "description": "Analysis step description",
      "evidence": "Supporting evidence",
      "confidence": 0.90
    }}
  ],
  "confidence": 0.85,
  "disclaimer": "This is AI-generated decision support — not a diagnosis."
}}

IMPORTANT: Respond ONLY with valid JSON. No text before or after."""

    # --- Change Detection ---

    CHANGE_DETECTION = """Identify significant changes between two clinical visits.

{rag_context}

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
      "reasoning": "Why this change is clinically significant",
      "confidence": 0.95
    }}
  ],
  "stable_conditions": ["Stable condition 1"],
  "new_findings": [
    {{
      "category": "CONDITION|SYMPTOM|LAB_ABNORMALITY",
      "description": "New finding description",
      "severity": "critical|important|minor",
      "supporting_data": ["evidence"],
      "reasoning": "Why significant",
      "confidence": 0.90
    }}
  ],
  "resolved_issues": ["Resolved issue 1"],
  "overall_assessment": "Summary of overall clinical trajectory"
}}

Severity Guide:
- critical: Life-threatening, requires immediate attention
- important: Significant, requires clinical attention
- minor: Notable but not urgent

Respond ONLY with valid JSON."""

    # --- Disease Prediction Explanation ---

    DISEASE_EXPLANATION = """Based on these symptoms: {symptoms}

Prediction results:
{predictions}

Recommended tests: {tests}

Explain the prediction in clear, simple language suitable for both doctors and patients.
Include:
1. Why these diseases were predicted
2. Which symptoms map to which conditions
3. Why the recommended tests are important
4. Safety disclaimer about consulting a qualified doctor

Return JSON:
{{
  "ai_explanation": "Clear, simple explanation",
  "key_symptom_mappings": [
    {{"symptom": "fever", "related_conditions": ["condition1"]}}
  ],
  "confidence": 0.85,
  "disclaimer": "This is AI-assisted analysis. Please consult a qualified healthcare professional for diagnosis."
}}

Respond ONLY with valid JSON."""

    # --- Drug Equivalence ---

    DRUG_EQUIVALENCE = """Patient prescribed: {brand_name} ({composition})
Jan Aushadhi generic: {generic_name} at ₹{jan_price} vs branded ₹{branded_price}
Savings: ₹{savings} ({savings_pct}% reduction)

Explain:
1. Why the generic is equally effective (same active pharmaceutical ingredients)
2. Quality assurance under Jan Aushadhi Pariyojana (BPPI)
3. CDSCO bioequivalence standards
4. Safety considerations for switching

Return JSON:
{{
  "explanation": "Clear pharmacological explanation",
  "quality_assurance": "Jan Aushadhi quality standards",
  "safety_note": "Safety considerations for the patient",
  "confidence": 0.90,
  "disclaimer": "Always consult your doctor before switching medications."
}}

Respond ONLY with valid JSON."""

    # --- Intent Classification ---

    INTENT_CLASSIFICATION = """Classify this request into one category:
- clinical_summary: Wants clinical summary of patient visit
- change_detection: Wants to compare visits or detect changes
- disease_prediction: Has symptoms, wants disease prediction
- generic_medicine: Wants Jan Aushadhi generic alternative
- clinical_query: General clinical question
- risk_monitoring: Wants risk assessment or alerts

Request: "{query}"

Return JSON:
{{
  "intent": "category_name",
  "confidence": 0.95,
  "entities": {{}},
  "reasoning": "Brief explanation of classification"
}}

Respond ONLY with valid JSON."""

    # --- Clinical Query (RAG-grounded) ---

    CLINICAL_QUERY = """Answer this clinical question using the provided context.

{rag_context}

Doctor's Question: {query}

Patient Context:
{patient_context}

Return JSON:
{{
  "response": "Detailed clinical response",
  "sources": ["source 1", "source 2"],
  "confidence": 0.85,
  "follow_up_suggestions": ["suggestion 1"],
  "disclaimer": "This is AI-generated decision support."
}}

IMPORTANT:
- Base your response on the provided context
- If context is insufficient, state so clearly
- Never fabricate clinical data
- Include confidence score reflecting certainty

Respond ONLY with valid JSON."""

    # --- RAG Context Formatting ---

    @staticmethod
    def format_rag_context(documents: list) -> str:
        """Format RAG-retrieved documents for prompt injection."""
        if not documents:
            return ""

        parts = ["RELEVANT CONTEXT (from patient history and medical knowledge base):"]
        for i, doc in enumerate(documents, 1):
            content = doc.get("content", "")[:1500]
            doc_type = doc.get("doc_type", "unknown")
            parts.append(f"\n[Document {i} — {doc_type}]\n{content}")

        parts.append("\n--- END CONTEXT ---\n")
        return "\n".join(parts)
