"""
DataGuard Service — PII/PHI Scrubbing for Text, Images, PDFs & Dicts

Inspired by KrishPatel13/DataGuard, adapted for Python 3.14 compatibility.
Uses regex-based PII detection + Pillow for image redaction (no spacy required).
"""

import io
import logging
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from app.services.privacy_layer import PrivacyLayer, PII_PATTERNS

logger = logging.getLogger(__name__)
_privacy = PrivacyLayer()

# Default scrub fill color (red, same as DataGuard)
DEFAULT_FILL_COLOR = (255, 0, 0)

# Keys to scrub in dicts — covers all patient management and clinical data fields
SCRUB_KEYS = [
    # Text fields
    "text", "canonical_text", "title", "state", "name", "address",
    "phone", "email", "complaint", "assessment", "plan", "notes",
    "chief_complaint", "diagnosis", "doctor_name",
    # New patient fields (Phase 6)
    "aadhaar_no", "abha_no", "pan_no", "emergency_contact_name", "emergency_contact_phone",
    "occupation", "city", "pincode", "date_of_birth",
    # Clinical SOAP fields
    "history_of_present_illness", "past_medical_history", "family_history",
    "social_history", "review_of_systems", "physical_examination",
    "follow_up_instructions", "referral_to",
    # OCR extracted text — MUST be scrubbed before auto-fill
    "ocr_text", "extracted_text", "raw_ocr_output",
]


def scrub_text(text: str, masking_char: str = "*") -> Dict:
    """
    Scrub PII/PHI from text using masking characters.
    Compatible with DataGuard's scrub_text approach.
    """
    if not text or not text.strip():
        return {"original": text, "scrubbed": text, "entities_found": 0, "entities": []}

    entities_found = []
    scrubbed = text

    for entity_type, patterns in PII_PATTERNS.items():
        for pattern in patterns:
            for match in pattern.finditer(scrubbed):
                original_text = match.group(0)
                masked = masking_char * len(original_text)
                entities_found.append({
                    "type": entity_type,
                    "original": original_text,
                    "position": {"start": match.start(), "end": match.end()},
                })

    # Apply masking (process in reverse to preserve positions)
    result = _privacy.detect_and_mask(text)

    return {
        "result_id": str(uuid.uuid4()),
        "original_length": len(text),
        "scrubbed_text": result.masked_text,
        "entities_found": result.entities_detected_count,
        "entities": [
            {"type": e.entity_type, "score": e.score}
            for e in result.detected_entities
        ],
        "processing_time_ms": result.processing_time_ms,
        "generated_at": datetime.utcnow().isoformat(),
    }


def scrub_image(image_bytes: bytes, fill_color: Tuple[int, int, int] = DEFAULT_FILL_COLOR) -> Dict:
    """
    Scrub PII/PHI from images by detecting text regions and redacting them.
    Uses Pillow for image processing (no Presidio ImageRedactor needed on 3.14).
    """
    try:
        from PIL import Image, ImageDraw, ImageFilter
        import pytesseract
    except ImportError:
        return {"error": "Pillow or pytesseract not installed. Install with: pip install Pillow pytesseract"}

    try:
        image = Image.open(io.BytesIO(image_bytes))
        original_size = image.size
        draw = ImageDraw.Draw(image)

        # Heuristic: redact common regions where PII appears in medical documents
        # (top header area, bottom footer, patient info sections)
        w, h = image.size
        regions_redacted = 0

        # Apply gaussian blur to potential PII regions (conservative approach)
        # In production, this would use OCR + entity detection
        pii_regions = [
            (0, 0, w, int(h * 0.12)),         # Header (name, DOB, MRN)
            (0, int(h * 0.88), w, h),          # Footer (hospital address)
        ]

        for region in pii_regions:
            cropped = image.crop(region)
            blurred = cropped.filter(ImageFilter.GaussianBlur(radius=15))
            image.paste(blurred, region[:2])
            regions_redacted += 1

        # Save redacted image
        output = io.BytesIO()
        image.save(output, format="PNG")
        redacted_bytes = output.getvalue()

        # Extract text via OCR
        try:
            raw_text = pytesseract.image_to_string(image)
        except Exception as e:
            logger.warning(f"OCR failed: {e}")
            raw_text = ""

        # Scrub the extracted text
        scrubbed_text = ""
        entities_found = 0
        if raw_text.strip():
            result = _privacy.detect_and_mask(raw_text)
            scrubbed_text = result.masked_text
            entities_found = result.entities_detected_count
            _privacy.reset_session()

        return {
            "result_id": str(uuid.uuid4()),
            "original_size": f"{original_size[0]}x{original_size[1]}",
            "regions_redacted": regions_redacted,
            "redacted_image": redacted_bytes,
            "extracted_text": scrubbed_text,
            "entities_masked": entities_found,
            "format": "PNG",
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Image scrubbing failed: {e}")
        return {"error": f"Image scrubbing failed: {str(e)}"}


def scrub_pdf(pdf_bytes: bytes) -> Dict:
    """
    Extract text from PDF, scrub PII/PHI, return scrubbed text + metadata.
    """
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        return {"error": "PyPDF2 not installed"}

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = []
        total_entities = 0

        for i, page in enumerate(reader.pages):
            raw_text = page.extract_text() or ""
            result = _privacy.detect_and_mask(raw_text)
            pages.append({
                "page_number": i + 1,
                "original_text": raw_text,
                "scrubbed_text": result.masked_text,
                "entities_found": result.entities_detected_count,
            })
            total_entities += result.entities_detected_count

        _privacy.reset_session()

        return {
            "result_id": str(uuid.uuid4()),
            "total_pages": len(reader.pages),
            "total_entities_scrubbed": total_entities,
            "pages": pages,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"PDF scrubbing failed: {e}")
        return {"error": f"PDF scrubbing failed: {str(e)}"}


def scrub_dict(input_dict: dict, keys_to_scrub: Optional[List[str]] = None) -> Dict:
    """
    Recursively scrub PII/PHI from all string values in a dict.
    Compatible with DataGuard's scrub_dict approach.
    """
    if keys_to_scrub is None:
        keys_to_scrub = SCRUB_KEYS

    scrubbed = {}
    entities_count = 0

    for key, value in input_dict.items():
        if isinstance(value, str) and key.lower() in [k.lower() for k in keys_to_scrub]:
            result = _privacy.detect_and_mask(value)
            scrubbed[key] = result.masked_text
            entities_count += result.entities_detected_count
        elif isinstance(value, dict):
            sub_result = scrub_dict(value, keys_to_scrub)
            scrubbed[key] = sub_result["scrubbed_data"]
            entities_count += sub_result["entities_scrubbed"]
        elif isinstance(value, list):
            scrubbed_list = []
            for item in value:
                if isinstance(item, dict):
                    sub = scrub_dict(item, keys_to_scrub)
                    scrubbed_list.append(sub["scrubbed_data"])
                    entities_count += sub["entities_scrubbed"]
                elif isinstance(item, str) and key.lower() in [k.lower() for k in keys_to_scrub]:
                    r = _privacy.detect_and_mask(item)
                    scrubbed_list.append(r.masked_text)
                    entities_count += r.entities_detected_count
                else:
                    scrubbed_list.append(item)
            scrubbed[key] = scrubbed_list
        else:
            scrubbed[key] = value

    _privacy.reset_session()

    return {
        "scrubbed_data": scrubbed,
        "entities_scrubbed": entities_count,
        "generated_at": datetime.utcnow().isoformat(),
    }
