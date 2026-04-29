"""
Privacy Data Models

Data structures for PII/PHI detection, anonymization, and audit logging.
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DetectedEntity(BaseModel):
    """A detected PII/PHI entity."""
    entity_type: str = Field(..., description="Type of entity (PERSON, PHONE_NUMBER, etc.)")
    text: str = Field(..., description="Original text that was detected")
    start: int = Field(..., description="Start position in text")
    end: int = Field(..., description="End position in text")
    score: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")


class AnonymizedData(BaseModel):
    """Result of anonymization process."""
    original_text: str = Field(..., description="Original text before masking")
    masked_text: str = Field(..., description="Text with PII/PHI masked")
    detected_entities: List[DetectedEntity] = Field(default_factory=list)
    entity_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping from masked tokens to entity types",
    )
    entities_detected_count: int = Field(default=0)
    processing_time_ms: float = Field(default=0.0)


class PrivacyEvent(BaseModel):
    """Audit log event for privacy operations."""
    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Type of event (DETECTION, MASKING, ACCESS)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    entities_count: int = Field(default=0)
    entity_types: List[str] = Field(default_factory=list)
    action_taken: str = Field(default="MASKED")
    user_id: Optional[str] = Field(None)
    success: bool = Field(default=True)
    error_message: Optional[str] = Field(None)


class PrivacyException(Exception):
    """Exception raised when privacy layer operations fail."""

    def __init__(self, message: str, event: Optional[PrivacyEvent] = None):
        super().__init__(message)
        self.event = event
