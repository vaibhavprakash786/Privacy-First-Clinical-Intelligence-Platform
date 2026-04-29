"""
Privacy Layer Service

PII/PHI detection and anonymization.
Uses Microsoft Presidio when available (Python <3.14 with spacy),
otherwise falls back to a robust regex-based detector.

Critical first stage — NO AI processing without masking first.
Includes custom recognizers for Indian PII (Aadhaar, PAN, MRN).
"""

import logging
import re
import time
import uuid
from typing import Dict, List, Optional

from app.models.privacy import (
    AnonymizedData,
    DetectedEntity,
    PrivacyEvent,
    PrivacyException,
)

logger = logging.getLogger(__name__)

# Try to import Presidio, fall back to regex
try:
    from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
    from presidio_anonymizer import AnonymizerEngine
    PRESIDIO_AVAILABLE = True
    logger.info("Presidio available — using full NLP-based PII detection")
except ImportError:
    PRESIDIO_AVAILABLE = False
    logger.info("Presidio not available — using regex-based PII detection (Python 3.14+)")


# ===========================
# Regex-based PII patterns
# ===========================
PII_PATTERNS = {
    "PERSON": [
        # Common Indian name patterns (title + capitalized words)
        re.compile(r"\b(?:Dr\.?|Mr\.?|Mrs\.?|Ms\.?|Shri|Smt)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b"),
        # Standalone capitalized names (2-3 words, heuristic)
        re.compile(r"\b(?:Patient|Name)\s*[:\-]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b"),
    ],
    "PHONE_NUMBER": [
        # Indian phone numbers (+91, 0XX, or 10-digit)
        re.compile(r"\b(?:\+91[\s\-]?)?[6-9]\d{4}[\s\-]?\d{5}\b"),
        re.compile(r"\b0\d{2,4}[\s\-]?\d{6,8}\b"),
    ],
    "EMAIL_ADDRESS": [
        re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b"),
    ],
    "IN_AADHAAR": [
        # Aadhaar: 12 digits, groups of 4
        re.compile(r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b"),
    ],
    "IN_PAN": [
        # PAN: ABCDE1234F
        re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
    ],
    "MEDICAL_RECORD_NUMBER": [
        re.compile(r"\b(?:MRN|MR|Patient\s*ID|Hospital\s*ID)\s*[:#]?\s*[A-Z0-9]{4,12}\b", re.IGNORECASE),
    ],
    "INSURANCE_ID": [
        re.compile(r"\b(?:Insurance|Policy|Claim)\s*(?:ID|No|Number)\s*[:#]?\s*[A-Z0-9]{5,15}\b", re.IGNORECASE),
    ],
    "DATE_OF_BIRTH": [
        re.compile(r"\b(?:DOB|Date\s*of\s*Birth)\s*[:\-]?\s*\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\b", re.IGNORECASE),
    ],
    "ADDRESS": [
        re.compile(r"\b(?:Address|Addr)\s*[:\-]?\s*.{10,80}(?:Road|Rd|Street|St|Nagar|Colony|Apt|Floor|Block|Sector)\b", re.IGNORECASE),
    ],
}


class PrivacyLayer:
    """
    Privacy Layer for detecting and masking PII/PHI in clinical data.

    Detects:
    - PERSON (names)
    - PHONE_NUMBER
    - AADHAAR_NUMBER (Indian national ID)
    - PAN_NUMBER (Indian tax ID)
    - MEDICAL_RECORD_NUMBER
    - ADDRESS
    - INSURANCE_ID
    - EMAIL_ADDRESS
    - DATE_OF_BIRTH
    """

    def __init__(self, confidence_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold
        self._entity_counters: Dict[str, int] = {}
        self._entity_mappings: Dict[str, str] = {}

        if PRESIDIO_AVAILABLE:
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
            self._add_custom_recognizers()
        else:
            self.analyzer = None
            self.anonymizer = None

        logger.info(f"Privacy Layer initialized (mode={'presidio' if PRESIDIO_AVAILABLE else 'regex'})")

    def _add_custom_recognizers(self):
        """Add custom recognizers for Indian-specific PII patterns (Presidio mode)."""
        if not PRESIDIO_AVAILABLE:
            return

        aadhaar_pattern = Pattern(name="aadhaar_pattern", regex=r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b", score=0.85)
        aadhaar_recognizer = PatternRecognizer(supported_entity="IN_AADHAAR", patterns=[aadhaar_pattern], name="Indian Aadhaar Recognizer")
        self.analyzer.registry.add_recognizer(aadhaar_recognizer)

        pan_pattern = Pattern(name="pan_pattern", regex=r"\b[A-Z]{5}\d{4}[A-Z]\b", score=0.90)
        pan_recognizer = PatternRecognizer(supported_entity="IN_PAN", patterns=[pan_pattern], name="Indian PAN Recognizer")
        self.analyzer.registry.add_recognizer(pan_recognizer)

        mrn_pattern = Pattern(name="mrn_pattern", regex=r"\b(?:MRN|MR|Patient\s*ID|Hospital\s*ID)\s*[:#]?\s*[A-Z0-9]{4,12}\b", score=0.80)
        mrn_recognizer = PatternRecognizer(supported_entity="MEDICAL_RECORD_NUMBER", patterns=[mrn_pattern], name="Medical Record Number Recognizer")
        self.analyzer.registry.add_recognizer(mrn_recognizer)

        insurance_pattern = Pattern(name="insurance_pattern", regex=r"\b(?:Insurance|Policy|Claim)\s*(?:ID|No|Number)\s*[:#]?\s*[A-Z0-9]{5,15}\b", score=0.80)
        insurance_recognizer = PatternRecognizer(supported_entity="INSURANCE_ID", patterns=[insurance_pattern], name="Insurance ID Recognizer")
        self.analyzer.registry.add_recognizer(insurance_recognizer)

    def detect_pii_phi(
        self,
        text: str,
        language: str = "en",
        entities: Optional[List[str]] = None,
    ) -> List[DetectedEntity]:
        """Detect PII/PHI entities in the provided text."""
        if not text or not text.strip():
            return []

        if PRESIDIO_AVAILABLE and self.analyzer:
            return self._detect_presidio(text, language, entities)
        else:
            return self._detect_regex(text)

    def _detect_presidio(self, text: str, language: str, entities: Optional[List[str]]) -> List[DetectedEntity]:
        """Detect using Microsoft Presidio (NLP-based)."""
        try:
            results = self.analyzer.analyze(
                text=text,
                language=language,
                entities=entities,
                score_threshold=self.confidence_threshold,
            )
            detected = []
            for result in results:
                entity = DetectedEntity(
                    entity_type=result.entity_type,
                    text=text[result.start:result.end],
                    start=result.start,
                    end=result.end,
                    score=result.score,
                )
                detected.append(entity)

            detected.sort(key=lambda e: e.start, reverse=True)
            return detected

        except Exception as e:
            logger.error(f"Presidio detection failed, falling back to regex: {e}")
            return self._detect_regex(text)

    def _detect_regex(self, text: str) -> List[DetectedEntity]:
        """Detect using regex patterns (fallback for Python 3.14+)."""
        detected = []

        for entity_type, patterns in PII_PATTERNS.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    # Check if this span overlaps with an existing detection
                    overlapping = False
                    for existing in detected:
                        if not (match.end() <= existing.start or match.start() >= existing.end):
                            overlapping = True
                            break
                    if overlapping:
                        continue

                    detected.append(DetectedEntity(
                        entity_type=entity_type,
                        text=match.group(0),
                        start=match.start(),
                        end=match.end(),
                        score=0.80,
                    ))

        # Sort end-to-start for safe replacement
        detected.sort(key=lambda e: e.start, reverse=True)
        logger.info(f"Regex detected {len(detected)} PII/PHI entities")
        return detected

    def _generate_token(self, entity_type: str, original_text: str, context: str = "") -> str:
        """Generate a consistent masked token for an entity."""
        cache_key = f"{entity_type}:{original_text}"
        if cache_key in self._entity_mappings:
            return self._entity_mappings[cache_key]

        counter = self._entity_counters.get(entity_type, 0) + 1
        self._entity_counters[entity_type] = counter

        if entity_type == "PERSON":
            context_lower = context.lower()
            if any(t in context_lower for t in ["dr.", "dr ", "doctor"]):
                token = f"[PHYSICIAN_{counter}]"
            elif any(t in context_lower for t in ["nurse", "rn "]):
                token = f"[NURSE_{counter}]"
            else:
                token = f"[PATIENT_{counter}]"
        elif entity_type == "IN_AADHAAR":
            token = f"[AADHAAR_{counter}]"
        elif entity_type == "IN_PAN":
            token = f"[PAN_{counter}]"
        elif entity_type == "MEDICAL_RECORD_NUMBER":
            token = f"[MRN_{counter}]"
        elif entity_type == "INSURANCE_ID":
            token = f"[INSURANCE_{counter}]"
        elif entity_type == "PHONE_NUMBER":
            token = f"[PHONE_{counter}]"
        elif entity_type == "EMAIL_ADDRESS":
            token = f"[EMAIL_{counter}]"
        elif entity_type in ("LOCATION", "ADDRESS"):
            token = f"[LOCATION_{counter}]"
        elif entity_type == "DATE_OF_BIRTH":
            token = f"[DOB_{counter}]"
        else:
            token = f"[{entity_type}_{counter}]"

        self._entity_mappings[cache_key] = token
        return token

    def mask_entities(
        self,
        text: str,
        detected_entities: List[DetectedEntity],
    ) -> AnonymizedData:
        """Mask detected PII/PHI entities in the text."""
        start_time = time.time()

        if not detected_entities:
            return AnonymizedData(
                original_text=text,
                masked_text=text,
                detected_entities=[],
                entity_mapping={},
                entities_detected_count=0,
                processing_time_ms=0,
            )

        try:
            masked_text = text
            entity_mapping: Dict[str, str] = {}

            for entity in detected_entities:
                ctx_start = max(0, entity.start - 20)
                context = text[ctx_start:entity.start]
                token = self._generate_token(entity.entity_type, entity.text, context)
                masked_text = masked_text[:entity.start] + token + masked_text[entity.end:]
                entity_mapping[token] = entity.entity_type

            processing_time = (time.time() - start_time) * 1000

            return AnonymizedData(
                original_text=text,
                masked_text=masked_text,
                detected_entities=detected_entities,
                entity_mapping=entity_mapping,
                entities_detected_count=len(detected_entities),
                processing_time_ms=round(processing_time, 2),
            )

        except Exception as e:
            logger.error(f"Entity masking failed: {e}")
            raise PrivacyException(f"Entity masking failed: {e}")

    def detect_and_mask(
        self,
        raw_data: str,
        language: str = "en",
    ) -> AnonymizedData:
        """
        Detect and mask PII/PHI in one operation.
        This is the primary method for processing clinical data.
        """
        if not raw_data or not raw_data.strip():
            return AnonymizedData(
                original_text=raw_data or "",
                masked_text=raw_data or "",
                detected_entities=[],
                entity_mapping={},
                entities_detected_count=0,
                processing_time_ms=0,
            )

        entities = self.detect_pii_phi(raw_data, language)
        return self.mask_entities(raw_data, entities)

    def create_privacy_event(
        self,
        event_type: str,
        anonymized_data: AnonymizedData,
        user_id: Optional[str] = None,
        action_taken: str = "MASKED",
    ) -> PrivacyEvent:
        """Create a privacy event for audit logging."""
        entity_types = list(set(e.entity_type for e in anonymized_data.detected_entities))
        return PrivacyEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            entities_count=anonymized_data.entities_detected_count,
            entity_types=entity_types,
            action_taken=action_taken,
            user_id=user_id,
            success=True,
        )

    def reset_session(self):
        """Reset entity counters and mappings for a new session."""
        self._entity_counters.clear()
        self._entity_mappings.clear()

    def health_check(self) -> bool:
        """Check if privacy layer is functional."""
        try:
            test = self.detect_and_mask("Test patient Ravi Kumar, Aadhaar 9876 5432 1098, PAN ABCDE1234F")
            return test.entities_detected_count > 0
        except Exception:
            return False
