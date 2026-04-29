"""
Amazon Bedrock AI Client

Provides AI reasoning capabilities using Amazon Bedrock (Claude).
Supports mock mode for local development without AWS credentials.
"""

import json
import logging
import uuid
from typing import Any, Dict, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIError(Exception):
    """Base exception for AI client errors."""
    pass


class AITimeoutError(AIError):
    """Raised when AI request times out."""
    pass


class AIInvalidResponseError(AIError):
    """Raised when AI returns invalid response."""
    pass


class BedrockClient:
    """
    Amazon Bedrock AI client for clinical reasoning.

    Supports two modes:
    - 'mock': Returns realistic structured JSON for local development
    - 'bedrock': Uses Amazon Bedrock Claude for real AI inference
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        timeout: int = 30,
    ):
        self.model_id = model_id or settings.BEDROCK_MODEL_ID
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.mode = settings.effective_ai_mode

        if self.mode == "bedrock":
            try:
                import boto3
                boto_kwargs = {"region_name": settings.BEDROCK_REGION}
                if settings.AWS_ACCESS_KEY_ID:
                    boto_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                    boto_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
                if settings.AWS_SESSION_TOKEN:
                    boto_kwargs["aws_session_token"] = settings.AWS_SESSION_TOKEN
                self.client = boto3.client("bedrock-runtime", **boto_kwargs)
                logger.info(f"Bedrock client initialized: model={self.model_id}")
            except Exception as e:
                logger.warning(f"Bedrock init failed, falling back to mock: {e}")
                self.mode = "mock"
        else:
            logger.info("AI client running in MOCK mode")

    def invoke(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        image_bytes: Optional[bytes] = None,
        image_media_type: str = "image/jpeg",
    ) -> str:
        """Invoke AI model with prompt and return response text."""
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        logger.debug(f"AI Invoke [{self.mode}] - Prompt length: {len(prompt)}")

        if self.mode == "bedrock":
            return self._bedrock_invoke(prompt, system_prompt, temp, tokens, image_bytes, image_media_type)

        # Fallback for unexpected mode, though settings.effective_ai_mode should prevent this
        logger.error(f"Unknown AI mode: {self.mode}. Falling back to mock.")
        return self._mock_invoke(prompt, system_prompt)


    def invoke_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Invoke AI model and parse response as JSON."""
        response_text = self.invoke(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Try to extract JSON from response
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON block in the response
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(response_text[start:end])
                except json.JSONDecodeError:
                    pass
            logger.error(f"Failed to parse JSON from response: {response_text[:200]}")
            raise AIInvalidResponseError("Invalid JSON response from AI")

    def invoke_with_template(
        self,
        template: str,
        variables: Dict[str, Any],
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Invoke AI using a prompt template with variable substitution."""
        prompt = template.format(**variables)
        return self.invoke(prompt=prompt, system_prompt=system_prompt, **kwargs)

    def _bedrock_invoke(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        image_bytes: Optional[bytes] = None,
        image_media_type: str = "image/jpeg",
    ) -> str:
        """Invoke Amazon Bedrock model."""
        try:
            if "llama" in self.model_id.lower():
                # Llama 3 Format
                sys_prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>" if system_prompt else "<|begin_of_text|>"
                llama_prompt = f"{sys_prompt}<|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
                
                body = {
                    "prompt": llama_prompt,
                    "max_gen_len": min(max_tokens, 2048),
                    "temperature": temperature,
                }
                
                response = self.client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(body),
                    contentType="application/json",
                    accept="application/json",
                )
                response_body = json.loads(response["body"].read())
                return response_body.get("generation", "")

            else:
                # Default to Claude 3 Format
                content = []
                if image_bytes:
                    import base64
                    base64_img = base64.b64encode(image_bytes).decode('utf-8')
                    content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image_media_type,
                            "data": base64_img
                        }
                    })
                
                content.append({
                    "type": "text",
                    "text": prompt
                })

                messages = [{"role": "user", "content": content}]

                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": messages,
                }

                if system_prompt:
                    body["system"] = system_prompt

                response = self.client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(body),
                    contentType="application/json",
                    accept="application/json",
                )
                response_body = json.loads(response["body"].read())
                return response_body["content"][0]["text"]

        except Exception as e:
            logger.error(f"Bedrock invocation error: {e}")
            raise AIError(f"Bedrock error: {e}") from e

    def _mock_invoke(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Return realistic mock responses for local development."""
        prompt_lower = prompt.lower()

        # Clinical Summary
        if "clinical" in prompt_lower and ("summary" in prompt_lower or "summarize" in prompt_lower):
            return json.dumps({
                "summary_text": "Patient presents with controlled hypertension and well-managed Type 2 Diabetes Mellitus. Blood pressure readings are within target range on current antihypertensive regimen. HbA1c shows improvement from previous visit. No acute complaints reported.",
                "key_findings": [
                    {
                        "category": "CONDITION",
                        "description": "Hypertension — well controlled on current medication",
                        "severity": "minor",
                        "supporting_data": ["BP: 128/82 mmHg"],
                        "reasoning": "Blood pressure within target range for diabetic patients (<130/80)",
                        "confidence": 0.92,
                    },
                    {
                        "category": "LAB_ABNORMALITY",
                        "description": "HbA1c at 7.1% — showing improvement",
                        "severity": "important",
                        "supporting_data": ["HbA1c: 7.1%", "Previous: 7.8%"],
                        "reasoning": "HbA1c trending towards target of <7.0% for most adults with diabetes",
                        "confidence": 0.88,
                    },
                ],
                "reasoning_steps": [
                    {"step_number": 1, "description": "Reviewed vital signs — all within acceptable ranges", "evidence": "BP 128/82, HR 72, SpO2 98%", "confidence": 0.95},
                    {"step_number": 2, "description": "Assessed lab trends — HbA1c improving", "evidence": "Previous 7.8% → Current 7.1%", "confidence": 0.90},
                    {"step_number": 3, "description": "Evaluated medication effectiveness", "evidence": "Current regimen maintaining control", "confidence": 0.85},
                ],
                "confidence": 0.89,
            })

        # Change Detection
        if "change" in prompt_lower and ("detect" in prompt_lower or "identif" in prompt_lower):
            return json.dumps({
                "significant_changes": [
                    {
                        "category": "LABS",
                        "description": "HbA1c improved from 7.8% to 7.1%",
                        "severity": "important",
                        "previous_value": "7.8%",
                        "current_value": "7.1%",
                        "trend_direction": "improving",
                        "reasoning": "Significant improvement in glycemic control",
                        "confidence": 0.93,
                    },
                ],
                "stable_conditions": ["Blood pressure well controlled", "Heart rate within normal range"],
                "new_findings": [],
                "resolved_issues": [],
                "overall_assessment": "Patient showing positive trajectory with improving glycemic control."
            })

        # Disease Prediction
        if "symptom" in prompt_lower or "disease" in prompt_lower or "predict" in prompt_lower:
            return json.dumps({
                "predicted_diseases": [
                    {"disease": "Common Cold", "probability": 0.72, "confidence": 0.85},
                    {"disease": "Viral Pharyngitis", "probability": 0.18, "confidence": 0.70},
                    {"disease": "Allergic Rhinitis", "probability": 0.10, "confidence": 0.60},
                ],
                "recommended_tests": ["Complete Blood Count (CBC)", "Throat swab if persistent"],
                "reasoning_steps": [
                    {"step_number": 1, "description": "Analyzed symptom combination", "evidence": "Runny nose, sore throat, mild fever", "confidence": 0.85},
                    {"step_number": 2, "description": "Matched against disease patterns", "evidence": "Symptom profile matches common viral infections", "confidence": 0.80},
                ],
                "ai_explanation": "Based on the symptoms of runny nose, sore throat, and mild fever, the most likely diagnosis is Common Cold. This is a self-limiting viral infection that typically resolves within 7-10 days.",
                "confidence": 0.82,
            })

        # Drug equivalence / Generic medicine
        if "medicine" in prompt_lower or "drug" in prompt_lower or "generic" in prompt_lower or "equivalen" in prompt_lower:
            return json.dumps({
                "explanation": "Amoxicillin + Clavulanic Acid (the generic composition of Augmentin) is equally effective when manufactured according to pharmacological standards. Jan Aushadhi generic alternatives undergo the same quality testing as branded medicines and contain identical active pharmaceutical ingredients in the same proportions.",
                "safety_note": "The generic alternative contains the same active ingredients in the same strength. Both branded and generic versions must meet the same quality and bioequivalence standards set by CDSCO.",
                "confidence": 0.90,
            })

        # Intent detection
        if "intent" in prompt_lower or "classify" in prompt_lower:
            return json.dumps({
                "intent": "clinical_summary",
                "confidence": 0.88,
                "entities": {},
            })

        # Query response
        if "query" in prompt_lower or "question" in prompt_lower:
            return json.dumps({
                "response": "Based on the patient's clinical history, blood pressure has been trending stable over the last 3 visits with values consistently below 130/80 mmHg on the current antihypertensive regimen.",
                "sources": ["Visit 2024-01-15", "Visit 2024-07-22", "Visit 2025-01-10"],
                "confidence": 0.85,
            })

        # Default
        return json.dumps({
            "response": "AI analysis completed successfully.",
            "confidence": 0.75,
        })

    def health_check(self) -> bool:
        """Check if AI service is accessible."""
        try:
            if self.mode == "mock":
                return True
            response = self.invoke("Respond with 'OK'", max_tokens=10)
            return bool(response)
        except Exception as e:
            logger.error(f"AI health check failed: {e}")
            return False


# Singleton
_bedrock_client: Optional[BedrockClient] = None


def get_bedrock_client() -> BedrockClient:
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockClient()
    return _bedrock_client
