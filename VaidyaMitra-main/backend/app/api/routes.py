"""
VaidyaMitra API Routes

All REST endpoints with mandatory privacy-first data flow.
Every flow: raw data → privacy masking → AI → structured JSON.
"""

import logging
import uuid
import json
from datetime import datetime
import io

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from PIL import Image
import pytesseract
from typing import Dict, List, Optional

from app.services.privacy_layer import PrivacyLayer
from app.services.bedrock_client import BedrockClient, get_bedrock_client
from app.services.summary_generator import SummaryGenerator
from app.services.change_detector import ChangeDetector
from app.services.disease_predictor import DiseasePredictor
from app.services.generic_medicine_engine import GenericMedicineEngine
from app.services.rag_service import RAGService
from app.services.report_simplifier import simplify_report, summarize_report
from app.services.dataguard_service import scrub_text as dg_scrub_text, scrub_image as dg_scrub_image, scrub_pdf, scrub_dict
from app.core.s3_client import get_s3_client
from app.core.cache_client import get_cache_client
from app.services.translation_service import (
    get_supported_languages, get_ui_strings, detect_language, translate_medical_text,
)
from app.services.medicine_identifier import (
    identify_medicine, get_medicine_info, compare_medicines, list_all_medicines, search_medicines, identify_medicine_ai
)
from app.services import patient_service
from app.agents.orchestrator import OrchestratorAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["VaidyaMitra API"])

# Initialize services
privacy = PrivacyLayer()
bedrock = get_bedrock_client()
summary_gen = SummaryGenerator(bedrock)
change_det = ChangeDetector(bedrock)
disease_pred = DiseasePredictor(bedrock)
medicine_engine = GenericMedicineEngine(bedrock)
rag = RAGService()
orchestrator = OrchestratorAgent()


# ===========================
# Request/Response Models
# ===========================
class ClinicalDataRequest(BaseModel):
    patient_id: Optional[str] = None
    visit_type: str = "ROUTINE"
    chief_complaint: str = ""
    assessment: str = ""
    plan: str = ""
    notes: str = ""
    vitals: Optional[Dict] = None

class PredictRequest(BaseModel):
    symptoms: List[str]
    patient_id: Optional[str] = None

class MedicineRequest(BaseModel):
    medicine_name: str
    quantity: Optional[int] = 1

class QueryRequest(BaseModel):
    query: str
    patient_id: Optional[str] = None

class PatientRegisterRequest(BaseModel):
    name: str
    age: int
    gender: str
    blood_group: str = "Unknown"
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    allergies: List[str] = []
    chronic_conditions: List[str] = []
    current_medications: List[str] = []
    emergency_contact: Optional[str] = None
    language_preference: str = "en"

class PatientVisitRequest(BaseModel):
    visit_type: str = "ROUTINE"
    chief_complaint: str = ""
    assessment: str = ""
    plan: str = ""
    notes: str = ""
    vitals: Dict[str, float] = {}
    diagnosis: List[str] = []
    doctor_name: Optional[str] = None
    follow_up_date: Optional[str] = None

class ReportSimplifyRequest(BaseModel):
    report_text: str
    language: str = "en"

class ScrubTextRequest(BaseModel):
    text: str

class ScrubDictRequest(BaseModel):
    data: Dict

class TranslateRequest(BaseModel):
    text: str
    target_lang: str
    source_lang: str = "en"

class VoiceQueryRequest(BaseModel):
    transcribed_text: str
    language: str = "en"
    patient_id: Optional[str] = None

class MedicineIdentifyRequest(BaseModel):
    medicine_name: str

class MedicineCompareRequest(BaseModel):
    brand_name: str

class PipelineTestRequest(BaseModel):
    s3_bucket: str
    s3_key: str
    patient_id: str


# ===========================
# Health & Info
# ===========================
@router.get("/health")
async def health_check():
    return {
        "status": "operational",
        "version": "2.0.0",
        "services": {
            "privacy_layer": privacy.health_check(),
            "ai_service": True,
            "patient_service": True,
            "translation": True,
            "dataguard": True,
            "medicine_identifier": True,
        },
        "supported_languages": list(get_supported_languages().keys()),
        "timestamp": datetime.utcnow().isoformat(),
    }

@router.get("/languages")
async def get_languages():
    return {"languages": get_supported_languages()}

@router.get("/languages/{lang}/ui")
async def get_language_ui(lang: str):
    return {"language": lang, "strings": get_ui_strings(lang)}


# ===========================
# Patient Management
# ===========================
@router.post("/patients")
async def register_patient(req: PatientRegisterRequest):
    patient = patient_service.register_patient(req.model_dump())
    return {"success": True, "data": patient.model_dump()}

@router.get("/patients")
async def list_patients(search: Optional[str] = None):
    if search:
        patients = patient_service.search_patients(search)
    else:
        patients = patient_service.list_all_patients()
    return {"success": True, "data": [p.model_dump() for p in patients], "count": len(patients)}

@router.get("/patients/{patient_id}")
async def get_patient(patient_id: str):
    patient = patient_service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    summary = patient_service.get_patient_summary(patient_id)
    return {"success": True, "data": {"patient": patient.model_dump(), "summary": summary.model_dump() if summary else None}}

@router.put("/patients/{patient_id}")
async def update_patient(patient_id: str, updates: Dict):
    patient = patient_service.update_patient(patient_id, updates)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"success": True, "data": patient.model_dump()}

@router.post("/patients/{patient_id}/visits")
async def add_patient_visit(patient_id: str, req: PatientVisitRequest):
    visit = patient_service.add_visit(patient_id, req.model_dump())
    if not visit:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"success": True, "data": visit.model_dump()}

@router.get("/patients/{patient_id}/visits")
async def get_patient_visits(patient_id: str):
    visits = patient_service.get_visits(patient_id)
    return {"success": True, "data": [v.model_dump() for v in visits], "count": len(visits)}

@router.get("/patients/{patient_id}/records")
async def get_patient_records(patient_id: str):
    records = patient_service.get_masked_records(patient_id)
    return {"success": True, "data": [r.model_dump() for r in records], "count": len(records), "privacy_applied": True}

@router.get("/patients/{patient_id}/trends")
async def get_patient_trends(patient_id: str):
    trends = patient_service.get_health_trends(patient_id)
    return {"success": True, "data": [t.model_dump() for t in trends]}


@router.post("/patients/{patient_id}/ai-summary")
async def get_patient_ai_summary(patient_id: str):
    """Generate an AI-powered comprehensive summary of a patient's medical history."""
    from app.core.cache_client import CacheClient, get_cache_client
    from app.core.config import settings

    # Check cache first
    cache = get_cache_client()
    cache_key = CacheClient.generate_cache_key("patient_summary", patient_id.lower())
    cached = cache.get(cache_key)
    if cached is not None:
        cached["from_cache"] = True
        return {"success": True, "data": cached}

    # Fetch patient info and visits
    patient = patient_service.get_patient(patient_id)
    if not patient:
        return {"success": False, "error": f"Patient {patient_id} not found"}

    visits = patient_service.get_visits(patient_id)
    if not visits:
        return {"success": False, "error": "No visit history available for this patient"}

    trends = patient_service.get_health_trends(patient_id)

    # Build structured clinical prompt
    visit_summaries = []
    for i, v in enumerate(visits):
        vitals_str = ", ".join(f"{k}: {val}" for k, val in v.vitals.items()) if v.vitals else "Not recorded"
        meds_str = ", ".join(m.get("name", str(m)) for m in v.medications_prescribed) if v.medications_prescribed else "None"
        diag_str = ", ".join(v.diagnosis) if v.diagnosis else "None"
        labs_str = ", ".join(f"{l.get('test','')}: {l.get('value','')} {l.get('unit','')}" for l in v.lab_results) if v.lab_results else "None"
        visit_summaries.append(
            f"Visit {i+1} ({v.visit_date}, {v.visit_type}):\n"
            f"  Complaint: {v.chief_complaint}\n"
            f"  Assessment: {v.assessment}\n"
            f"  Plan: {v.plan}\n"
            f"  Vitals: {vitals_str}\n"
            f"  Diagnosis: {diag_str}\n"
            f"  Medications: {meds_str}\n"
            f"  Lab Results: {labs_str}"
        )

    trend_summaries = []
    for t in trends:
        pts = t.data_points
        vals = [p["value"] for p in pts]
        trend_summaries.append(f"{t.metric_name}: {', '.join(str(v) for v in vals)} {t.unit} — trend: {t.trend}")

    prompt = f"""You are an expert clinical AI assistant specialized in healthcare analytics.
Analyze the following patient's complete medical history and provide a comprehensive clinical summary.

Patient: {patient.name}, Age: {patient.age}, Gender: {patient.gender}
Blood Group: {patient.blood_group}
Allergies: {', '.join(patient.allergies) if patient.allergies else 'None known'}
Chronic Conditions: {', '.join(patient.chronic_conditions) if patient.chronic_conditions else 'None known'}
Family History: {', '.join(patient.family_history) if patient.family_history else 'Not provided'}

=== VISIT HISTORY ({len(visits)} visits) ===
{'\n\n'.join(visit_summaries)}

=== VITAL SIGN TRENDS ===
{'\n'.join(trend_summaries) if trend_summaries else 'Insufficient data'}

Provide your response as valid JSON with these keys:
{{
  "overall_assessment": "2-3 sentence overall clinical assessment",
  "key_findings": ["list of important clinical findings"],
  "vital_sign_analysis": "analysis of vital sign trends, noting any concerning patterns or fluctuations",
  "risk_factors": ["list of identified risk factors"],
  "medication_review": "review of medications across visits, noting any changes or concerns",
  "recommendations": ["list of clinical recommendations for follow-up"],
  "condition_progression": "how the patient's condition has progressed across visits"
}}

Respond ONLY with valid JSON."""

    try:
        result = bedrock.invoke_json(prompt=prompt)
        result["patient_id"] = patient_id
        result["total_visits"] = len(visits)
        result["from_cache"] = False

        # Cache the result
        cache.put(
            cache_key, result,
            ttl_hours=getattr(settings, "CACHE_TTL_DISEASE_HOURS", 24),
            service="patient_summary",
            query_text=f"AI summary for {patient_id}",
        )

        return {"success": True, "data": result}
    except Exception as e:
        logger.warning(f"AI summary generation failed: {e}")
        # Fallback: structured summary without AI
        return {
            "success": True,
            "data": {
                "overall_assessment": f"Patient {patient.name} has {len(visits)} recorded visits. Manual review of visit history is recommended.",
                "key_findings": [v.chief_complaint for v in visits if v.chief_complaint],
                "vital_sign_analysis": "AI analysis unavailable. Review vital trends manually.",
                "risk_factors": list(patient.chronic_conditions),
                "medication_review": "AI analysis unavailable.",
                "recommendations": ["Schedule follow-up", "Review medication adherence"],
                "condition_progression": "Refer to visit history for detailed progression.",
                "patient_id": patient_id,
                "total_visits": len(visits),
                "from_cache": False,
                "ai_fallback": True,
            },
        }


# ===========================
# Clinical Data (existing)
# ===========================
@router.post("/clinical-data")
async def submit_clinical_data(req: ClinicalDataRequest):
    raw = f"Complaint: {req.chief_complaint}\nAssessment: {req.assessment}\nPlan: {req.plan}\nNotes: {req.notes}"
    privacy_result = privacy.detect_and_mask(raw)

    visit_id = str(uuid.uuid4())

    # If patient_id provided, also add as a visit
    if req.patient_id:
        patient_service.add_visit(req.patient_id, {
            "visit_type": req.visit_type,
            "chief_complaint": req.chief_complaint,
            "assessment": req.assessment,
            "plan": req.plan,
            "notes": req.notes,
            "vitals": req.vitals or {},
        })

    return {
        "success": True,
        "data": {
            "visit_id": visit_id,
            "patient_id": req.patient_id,
            "masked_text": privacy_result.masked_text,
            "entities_masked": privacy_result.entities_detected_count,
        },
        "privacy_applied": True,
    }


# ===========================
# Disease Prediction (existing)
# ===========================
@router.post("/predict-disease")
async def predict_disease(req: PredictRequest):
    prediction = disease_pred.predict(req.symptoms, req.patient_id)
    return {"success": True, "data": prediction, "privacy_applied": False}


# ===========================
# Generic Medicine (Jan Aushadhi)
# ===========================
@router.post("/generic-medicine")
async def find_generic_medicine(req: MedicineRequest):
    # Route text queries to the AI engine
    result = medicine_engine.find_alternatives(req.medicine_name)
    return {"success": True, "data": result.model_dump()}

@router.post("/generic-medicine/image")
async def find_generic_medicine_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Use Tesseract to get text from the wrapper
        extracted_text = pytesseract.image_to_string(image)
        logger.info(f"Extracted {len(extracted_text)} characters via OCR for Jan Aushadhi search.")
        
        # Send to AI Engine
        result = medicine_engine.find_alternatives("Find Jan Aushadhi generic for this medicine wrapper", extracted_text=extracted_text)
        
        return {"success": True, "data": result.model_dump()}
    except Exception as e:
        logger.error(f"Failed to process generic medicine image: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze uploaded wrapper image.")


# ===========================
# AI Query / Orchestrator (existing)
# ===========================
@router.post("/query")
async def process_query(req: QueryRequest):
    # If patient_id is provided, inject patient visit history as AI context
    query_text = req.query
    if req.patient_id:
        visits = patient_service.get_visits(req.patient_id)
        patient = patient_service.get_patient(req.patient_id)
        if visits:
            context_parts = []
            if patient:
                context_parts.append(f"Patient: {patient.name}, Age: {patient.age}, Gender: {patient.gender}")
                if patient.allergies:
                    context_parts.append(f"Allergies: {', '.join(patient.allergies)}")
                if patient.chronic_conditions:
                    context_parts.append(f"Chronic Conditions: {', '.join(patient.chronic_conditions)}")
            for i, v in enumerate(visits[-5:]):  # Last 5 visits for context
                vitals_str = ", ".join(f"{k}: {val}" for k, val in v.vitals.items()) if v.vitals else "N/A"
                diag_str = ", ".join(v.diagnosis) if v.diagnosis else "N/A"
                meds_str = ", ".join(m.get("name", str(m)) for m in v.medications_prescribed) if v.medications_prescribed else "N/A"
                context_parts.append(
                    f"Visit {i+1} ({v.visit_date}): {v.chief_complaint or 'N/A'} | "
                    f"Vitals: {vitals_str} | Diagnosis: {diag_str} | Meds: {meds_str}"
                )
            patient_context = "\n".join(context_parts)
            query_text = f"[Patient Data for {req.patient_id}]\n{patient_context}\n\n[User Query]\n{req.query}"

    masked = privacy.detect_and_mask(query_text)
    result = orchestrator.process_request(masked.masked_text, req.patient_id)
    return {"success": True, "data": result, "privacy_applied": True}


# ===========================
# Report Simplifier & Summarizer
# ===========================
@router.post("/reports/simplify")
async def simplify_medical_report(req: ReportSimplifyRequest):
    masked = privacy.detect_and_mask(req.report_text)
    result = simplify_report(masked.masked_text, req.language)
    return {"success": True, "data": result, "privacy_applied": True, "entities_masked": masked.entities_detected_count}

@router.post("/reports/summarize")
async def summarize_medical_report(req: ReportSimplifyRequest):
    masked = privacy.detect_and_mask(req.report_text)
    result = summarize_report(masked.masked_text)
    return {"success": True, "data": result, "privacy_applied": True}

@router.post("/reports/translate")
async def translate_report(req: TranslateRequest):
    result = translate_medical_text(req.text, req.target_lang, req.source_lang)
    return {"success": True, "data": result}


# ===========================
# DataGuard Scrubbing
# ===========================
@router.post("/scrub/text")
async def scrub_text_endpoint(req: ScrubTextRequest):
    result = dg_scrub_text(req.text)
    return {"success": True, "data": result}

@router.post("/scrub/image")
async def scrub_image_endpoint(file: UploadFile = File(...)):
    image_bytes = await file.read()
    result = dg_scrub_image(image_bytes)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    # Don't return raw bytes in JSON
    result.pop("redacted_image", None)
    return {"success": True, "data": result}

@router.post("/scrub/pdf")
async def scrub_pdf_endpoint(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    result = scrub_pdf(pdf_bytes)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "data": result}

@router.post("/scrub/dict")
async def scrub_dict_endpoint(req: ScrubDictRequest):
    result = scrub_dict(req.data)
    return {"success": True, "data": result}


# ===========================
# Voice Query
# ===========================
@router.post("/voice/query")
async def voice_query(req: VoiceQueryRequest):
    detected_lang = detect_language(req.transcribed_text)
    query_text = req.transcribed_text

    # If not English, note the original language
    source_lang = detected_lang if detected_lang != "en" else req.language
    
    # 1. Translate Query to English for the AI Orchestrator
    english_query = query_text
    if source_lang != "en":
        translation_result = translate_medical_text(query_text, "en", source_lang)
        english_query = translation_result.get("translated_text", query_text)

    # 1.5. Inject patient context if patient_id provided
    if req.patient_id:
        visits = patient_service.get_visits(req.patient_id)
        patient = patient_service.get_patient(req.patient_id)
        if visits:
            context_parts = []
            if patient:
                context_parts.append(f"Patient: {patient.name}, Age: {patient.age}, Gender: {patient.gender}")
            for i, v in enumerate(visits[-5:]):
                vitals_str = ", ".join(f"{k}: {val}" for k, val in v.vitals.items()) if v.vitals else "N/A"
                diag_str = ", ".join(v.diagnosis) if v.diagnosis else "N/A"
                context_parts.append(
                    f"Visit {i+1} ({v.visit_date}): {v.chief_complaint or 'N/A'} | Vitals: {vitals_str} | Diagnosis: {diag_str}"
                )
            patient_context = "\n".join(context_parts)
            english_query = f"[Patient Data for {req.patient_id}]\n{patient_context}\n\n[User Query]\n{english_query}"

    # 2. Process through orchestrator
    masked = privacy.detect_and_mask(english_query)
    ai_result = orchestrator.process_request(masked.masked_text, req.patient_id)
    
    # Extract the response text safely.
    # Different agents return slightly different text keys (e.g. 'response' vs 'ai_explanation' vs dictionary dump)
    ai_response_text = ""
    if isinstance(ai_result, dict):
        result_payload = ai_result.get("result", {})
        
        if isinstance(result_payload, dict):
            if "response" in result_payload:
                ai_response_text = result_payload["response"]
            elif "ai_explanation" in result_payload:
                ai_response_text = result_payload["ai_explanation"]
            else:
                ai_response_text = str(result_payload)
        elif "response" in ai_result:
            ai_response_text = ai_result["response"]
        else:
            ai_response_text = str(ai_result)
    else:
        ai_response_text = str(ai_result)

    # 3. Translate Response Back to Native Language
    final_response_text = ai_response_text
    if source_lang != "en" and ai_response_text:
        back_translation = translate_medical_text(ai_response_text, source_lang, "en")
        final_response_text = back_translation.get("translated_text", ai_response_text)
        
    # Build a clean response object for the frontend
    clean_result = {
        "response": final_response_text,
        "raw_data": ai_result if isinstance(ai_result, dict) else {}
    }

    return {
        "success": True,
        "data": {
            "detected_language": source_lang,
            "transcribed_text": req.transcribed_text,
            "result": clean_result,
        },
        "privacy_applied": True,
    }


# ===========================
# Medicine Identifier
# ===========================
@router.post("/medicine/identify")
async def identify_medicine_endpoint(req: MedicineIdentifyRequest):
    result = identify_medicine_ai(req.medicine_name)
    return {"success": True, "data": result}

@router.post("/medicine/identify/image")
async def identify_medicine_image_endpoint(file: UploadFile = File(...)):
    try:
        content = await file.read()
        image = Image.open(io.BytesIO(content))
        
        # Read text from wrapper using OCR
        extracted_text = pytesseract.image_to_string(image)
        logger.info(f"Medicine Image OCR extracted: {len(extracted_text)} chars")
        
        # We don't have a direct query, so we pass an empty string
        # The AI will infer the medicine entirely from the extracted text
        result = identify_medicine_ai(query="Identify medicine from this wrapper", extracted_text=extracted_text)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Failed to identify medicine from image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/medicine/compare")
async def compare_medicine_endpoint(req: MedicineCompareRequest):
    result = compare_medicines(req.brand_name)
    return {"success": True, "data": result}

@router.get("/medicine/list")
async def list_medicines():
    return {"success": True, "data": list_all_medicines()}

@router.get("/medicine/search")
async def search_medicine(q: str):
    results = search_medicines(q)
    return {"success": True, "data": results, "count": len(results)}


# ===========================
# File Upload (combined)
# ===========================
@router.post("/upload/report")
async def upload_report(file: UploadFile = File(...), patient_id: Optional[str] = Form(None)):
    content = await file.read()
    filename = file.filename or "unknown"
    
    # Store in S3
    s3 = get_s3_client()
    safe_patient_id = patient_id or "anonymous"
    s3_key = f"reports/{safe_patient_id}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
    content_type = file.content_type or "application/octet-stream"
    s3.upload_file(s3_key, content, content_type=content_type)
    file_url = s3.get_presigned_url(s3_key, expires_in=86400) # 24 hour URL

    if filename.lower().endswith(".pdf"):
        scrub_result = scrub_pdf(content)
        full_text = ""
        if scrub_result.get("pages"):
            full_text = " ".join(p["scrubbed_text"] for p in scrub_result["pages"])
            
        # Add PDF fallback via Bedrock Vision
        pdf_image_bytes = None
        try:
            from pdf2image import convert_from_bytes
            import io
            # Convert first page to image for AI Vision processing
            images = convert_from_bytes(content, dpi=200, first_page=1, last_page=1)
            if images:
                img_byte_arr = io.BytesIO()
                images[0].save(img_byte_arr, format='JPEG')
                pdf_image_bytes = img_byte_arr.getvalue()
        except Exception as e:
            logger.warning(f"Frontend Simplifier: Failed to convert PDF to image: {e}")

        simplified = simplify_report(report_text=full_text, image_bytes=pdf_image_bytes, raw_file_bytes=content)
        summary = summarize_report(report_text=full_text, image_bytes=pdf_image_bytes, raw_file_bytes=content)
        
        return {
            "success": True,
            "data": {
                "filename": filename,
                "type": "pdf",
                "file_url": file_url,
                "scrub_result": {k: v for k, v in scrub_result.items() if k != "pages"},
                "simplified_report": simplified,
                "summary": summary,
                "patient_id": patient_id,
            },
        }
    elif filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
        scrub_result = dg_scrub_image(content)
        scrub_result.pop("redacted_image", None)
        
        # Pass the original image content to Bedrock for vision-based simplification & summarization
        # Only do this if we haven't already extracted text (or even if we have, to be safe)
        simplified = simplify_report(report_text=scrub_result.get("extracted_text", ""), image_bytes=content)
        summary = summarize_report(report_text=scrub_result.get("extracted_text", ""), image_bytes=content)
        
        return {
            "success": True,
            "data": {
                "filename": filename,
                "type": "image",
                "file_url": file_url,
                "scrub_result": scrub_result,
                "simplified_report": simplified,
                "summary": summary,
                "patient_id": patient_id,
            },
        }

    return {"success": False, "error": "Unsupported file type. Upload PDF or image files."}

@router.get("/patients/{patient_id}/documents/upload-url")
async def get_document_upload_url(patient_id: str, filename: str, content_type: str = "application/pdf"):
    from app.core.config import settings
    s3 = get_s3_client()
    s3_key = f"reports/{patient_id}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
    url = s3.get_presigned_url(s3_key, expires_in=3600, client_method="put_object", content_type=content_type)
    return {
        "success": True,
        "data": {
            "upload_url": url,
            "s3_key": s3_key,
            "s3_bucket": settings.S3_BUCKET_NAME,
            "patient_id": patient_id
        }
    }

@router.post("/documents/test-pipeline")
async def test_report_pipeline(req: PipelineTestRequest):
    from app.lambdas.report_pipeline import process_document
    result = process_document(req.s3_bucket, req.s3_key, req.patient_id)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Pipeline failed"))
    return result

# ===========================
# Translation
# ===========================
@router.post("/translate")
async def translate_text(req: TranslateRequest):
    result = translate_medical_text(req.text, req.target_lang, req.source_lang)
    return {"success": True, "data": result}

@router.post("/detect-language")
async def detect_lang(req: ScrubTextRequest):
    lang = detect_language(req.text)
    lang_info = get_supported_languages().get(lang, {})
    return {"success": True, "data": {"detected": lang, "info": lang_info}}


# ===========================
# Cache Administration
# ===========================
@router.get("/cache/stats")
async def cache_stats():
    """Get cache performance statistics."""
    cache = get_cache_client()
    stats = cache.get_stats()
    return {"success": True, "data": stats}


class CacheClearRequest(BaseModel):
    service: Optional[str] = None  # None = clear all


@router.post("/cache/clear")
async def cache_clear(req: CacheClearRequest = CacheClearRequest()):
    """Clear cache entries. Optionally filter by service."""
    cache = get_cache_client()
    cleared = cache.clear(service=req.service)
    return {
        "success": True,
        "data": {
            "cleared_count": cleared,
            "service": req.service or "all",
        },
    }
