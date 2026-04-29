"""
Patient Management Service

Handles patient registration, unique ID assignment, visit tracking,
and medical history persistence. Uses DynamoDB for persistent storage
with in-memory cache for performance.
"""

import json
import logging
import random
import string
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from app.core.dynamodb_client import (
    get_dynamodb_client, TABLE_PATIENTS, TABLE_PATIENT_VISITS,
)
from app.models.patient_models import (
    Patient, PatientVisit, PatientRecord, PatientSummary, HealthTrend,
)
from app.services.privacy_layer import PrivacyLayer

logger = logging.getLogger(__name__)

# In-memory cache (write-through: writes go to both cache + DynamoDB)
_patients_cache: Dict[str, Patient] = {}
_visits_cache: Dict[str, List[PatientVisit]] = {}
_cache_loaded = False
_privacy = PrivacyLayer()


def _get_db():
    """Get DynamoDB client singleton."""
    return get_dynamodb_client()


def _load_cache_from_db():
    """Load all patients from DynamoDB into memory cache on first access."""
    global _cache_loaded
    if _cache_loaded:
        return
    try:
        db = _get_db()
        # Load patients
        items = db.scan_items(TABLE_PATIENTS, limit=1000)
        for item in items:
            try:
                patient = Patient(**item)
                _patients_cache[patient.patient_id] = patient
            except Exception as e:
                logger.warning(f"Skipping malformed patient record: {e}")

        # Load visits for each patient
        for patient_id in _patients_cache:
            try:
                visit_items = db.query_items(
                    TABLE_PATIENT_VISITS,
                    key_condition="patient_id = :pid",
                    expression_values={":pid": patient_id},
                    limit=500,
                    scan_forward=True,
                )
                visits = []
                for vi in visit_items:
                    try:
                        visits.append(PatientVisit(**vi))
                    except Exception:
                        pass
                _visits_cache[patient_id] = visits
            except Exception:
                _visits_cache[patient_id] = []

        _cache_loaded = True
        logger.info(f"Loaded {len(_patients_cache)} patients from DynamoDB")
    except Exception as e:
        _cache_loaded = True  # Don't retry on failure
        logger.warning(f"DynamoDB load failed (using empty cache): {e}")


def _generate_patient_id() -> str:
    """Generate unique VaidyaMitra Patient ID (format: VM-XXXXXX)."""
    chars = string.ascii_uppercase + string.digits
    suffix = "".join(random.choices(chars, k=6))
    return f"VM-{suffix}"


def register_patient(patient_data: dict) -> Patient:
    """Register a new patient and assign a unique ID."""
    _load_cache_from_db()

    patient_id = _generate_patient_id()
    while patient_id in _patients_cache:
        patient_id = _generate_patient_id()

    now = datetime.utcnow().isoformat()
    patient = Patient(
        patient_id=patient_id,
        name=patient_data.get("name", ""),
        age=patient_data.get("age", 0),
        gender=patient_data.get("gender", "O"),
        blood_group=patient_data.get("blood_group", "Unknown"),
        phone=patient_data.get("phone"),
        email=patient_data.get("email"),
        address=patient_data.get("address"),
        allergies=patient_data.get("allergies", []),
        chronic_conditions=patient_data.get("chronic_conditions", []),
        current_medications=patient_data.get("current_medications", []),
        emergency_contact=patient_data.get("emergency_contact"),
        language_preference=patient_data.get("language_preference", "en"),
        registered_at=now,
        updated_at=now,
    )

    # Write to cache
    _patients_cache[patient_id] = patient
    _visits_cache[patient_id] = []

    # Persist to DynamoDB
    try:
        db = _get_db()
        db.put_item(TABLE_PATIENTS, patient.model_dump())
    except Exception as e:
        logger.error(f"DynamoDB put_item failed for patient {patient_id}: {e}")

    logger.info(f"Patient registered: {patient_id}")
    return patient


def get_patient(patient_id: str) -> Optional[Patient]:
    """Retrieve patient by ID."""
    _load_cache_from_db()
    return _patients_cache.get(patient_id)


def update_patient(patient_id: str, updates: dict) -> Optional[Patient]:
    """Update patient information."""
    _load_cache_from_db()
    patient = _patients_cache.get(patient_id)
    if not patient:
        return None

    data = patient.model_dump()
    data.update(updates)
    data["updated_at"] = datetime.utcnow().isoformat()
    updated = Patient(**data)

    # Write to cache
    _patients_cache[patient_id] = updated

    # Persist to DynamoDB
    try:
        db = _get_db()
        db.put_item(TABLE_PATIENTS, updated.model_dump())
    except Exception as e:
        logger.error(f"DynamoDB update failed for patient {patient_id}: {e}")

    return updated


def search_patients(query: str) -> List[Patient]:
    """Search patients by name, phone, or ID."""
    _load_cache_from_db()
    
    query_lower = query.strip().lower()
    
    # Calculate meaningful query length to prevent broad prefix matching
    meaningful_query = query_lower
    if meaningful_query.startswith("vm-"):
        meaningful_query = meaningful_query[3:]
    elif meaningful_query.startswith("vm"):
        meaningful_query = meaningful_query[2:]
        
    meaningful_query = meaningful_query.strip()
    
    # Require at least 2 meaningful characters to search
    if len(meaningful_query) < 2:
        return []

    results = []
    for p in _patients_cache.values():
        if (query_lower in p.name.lower()
                or query_lower in p.patient_id.lower()
                or (p.phone and query_lower in p.phone)):
            results.append(p)
            
            # Limit results to 10 to prevent data dumping
            if len(results) >= 10:
                break
                
    return results


def add_visit(patient_id: str, visit_data: dict) -> Optional[PatientVisit]:
    """Add a new visit for a patient."""
    _load_cache_from_db()
    if patient_id not in _patients_cache:
        return None

    visit = PatientVisit(
        visit_id=str(uuid.uuid4()),
        patient_id=patient_id,
        visit_type=visit_data.get("visit_type", "ROUTINE"),
        visit_date=visit_data.get("visit_date", datetime.utcnow().isoformat()),
        chief_complaint=visit_data.get("chief_complaint", ""),
        assessment=visit_data.get("assessment", ""),
        plan=visit_data.get("plan", ""),
        notes=visit_data.get("notes", ""),
        vitals=visit_data.get("vitals", {}),
        lab_results=visit_data.get("lab_results", []),
        medications_prescribed=visit_data.get("medications_prescribed", []),
        diagnosis=visit_data.get("diagnosis", []),
        follow_up_date=visit_data.get("follow_up_date"),
        doctor_name=visit_data.get("doctor_name"),
    )

    # Write to cache
    _visits_cache.setdefault(patient_id, []).append(visit)

    # Persist to DynamoDB
    try:
        db = _get_db()
        db.put_item(TABLE_PATIENT_VISITS, visit.model_dump())
    except Exception as e:
        logger.error(f"DynamoDB put_item failed for visit {visit.visit_id}: {e}")

    logger.info(f"Visit added for patient {patient_id}: {visit.visit_id}")
    return visit


def get_visits(patient_id: str) -> List[PatientVisit]:
    """Get all visits for a patient."""
    _load_cache_from_db()
    return _visits_cache.get(patient_id, [])


def get_masked_records(patient_id: str) -> List[PatientRecord]:
    """Get privacy-masked medical records for a patient."""
    visits = get_visits(patient_id)
    records = []

    # Clinical thresholds for severity classification
    NORMAL_RANGES = {
        "blood_pressure_systolic": (90, 130),
        "blood_pressure_diastolic": (60, 85),
        "heart_rate": (60, 100),
        "temperature": (36.1, 37.5),
        "oxygen_saturation": (95, 100),
        "respiratory_rate": (12, 20),
        "blood_glucose": (70, 140),
    }
    CRITICAL_RANGES = {
        "blood_pressure_systolic": (70, 180),
        "blood_pressure_diastolic": (40, 120),
        "heart_rate": (40, 150),
        "temperature": (35, 39.5),
        "oxygen_saturation": (90, 100),
        "respiratory_rate": (8, 30),
        "blood_glucose": (50, 300),
    }

    for visit in visits:
        # Mask PII/PHI in clinical text
        complaint_result = _privacy.detect_and_mask(visit.chief_complaint)
        assessment_result = _privacy.detect_and_mask(visit.assessment)
        plan_result = _privacy.detect_and_mask(visit.plan)
        hpi_result = _privacy.detect_and_mask(visit.history_of_present_illness) if visit.history_of_present_illness else None

        total_masked = (
            complaint_result.entities_detected_count
            + assessment_result.entities_detected_count
            + plan_result.entities_detected_count
            + (hpi_result.entities_detected_count if hpi_result else 0)
        )

        # Compute severity from vitals
        severity = "normal"
        for key, val in visit.vitals.items():
            if key in CRITICAL_RANGES:
                crit_low, crit_high = CRITICAL_RANGES[key]
                norm_low, norm_high = NORMAL_RANGES.get(key, (crit_low, crit_high))
                if val <= crit_low or val >= crit_high:
                    severity = "critical"
                    break  # critical is worst, stop checking
                elif val < norm_low or val > norm_high:
                    severity = "elevated"  # keep checking for critical

        record = PatientRecord(
            record_id=visit.visit_id,
            patient_id=patient_id,
            visit_date=visit.visit_date,
            visit_type=visit.visit_type,
            department=visit.department,
            doctor_name=visit.doctor_name,
            masked_complaint=complaint_result.masked_text,
            masked_assessment=assessment_result.masked_text,
            masked_plan=plan_result.masked_text,
            masked_hpi=hpi_result.masked_text if hpi_result else "",
            vitals=visit.vitals,
            diagnosis=visit.diagnosis,
            icd_codes=visit.icd_codes,
            lab_results=visit.lab_results,
            medications_prescribed=visit.medications_prescribed,
            follow_up_date=visit.follow_up_date,
            privacy_applied=True,
            entities_masked=total_masked,
            severity=severity,
        )
        records.append(record)

    _privacy.reset_session()
    return records


def get_health_trends(patient_id: str) -> List[HealthTrend]:
    """Extract health trends from visit history."""
    visits = get_visits(patient_id)
    if not visits:
        return []

    # Track vital metrics across visits
    metrics: Dict[str, List[Dict]] = {
        "blood_pressure_systolic": [],
        "blood_pressure_diastolic": [],
        "heart_rate": [],
        "temperature": [],
        "oxygen_saturation": [],
        "weight": [],
        "respiratory_rate": [],
        "blood_glucose": [],
        "bmi": [],
    }
    normal_ranges = {
        "blood_pressure_systolic": {"min": 90, "max": 140},
        "blood_pressure_diastolic": {"min": 60, "max": 90},
        "heart_rate": {"min": 60, "max": 100},
        "temperature": {"min": 36.1, "max": 37.2},
        "oxygen_saturation": {"min": 95, "max": 100},
        "weight": {"min": 40, "max": 120},
        "respiratory_rate": {"min": 12, "max": 20},
        "blood_glucose": {"min": 70, "max": 140},
        "bmi": {"min": 18.5, "max": 24.9},
    }
    units = {
        "blood_pressure_systolic": "mmHg",
        "blood_pressure_diastolic": "mmHg",
        "heart_rate": "bpm",
        "temperature": "°C",
        "oxygen_saturation": "%",
        "weight": "kg",
        "respiratory_rate": "bpm",
        "blood_glucose": "mg/dL",
        "bmi": "kg/m²",
    }

    for visit in visits:
        for metric_name in metrics:
            if metric_name in visit.vitals:
                metrics[metric_name].append({
                    "date": visit.visit_date,
                    "value": visit.vitals[metric_name],
                })

    trends = []
    for metric_name, data_points in metrics.items():
        if len(data_points) < 1:
            continue
        # Determine trend
        trend = "stable"
        if len(data_points) >= 2:
            recent = data_points[-1]["value"]
            previous = data_points[-2]["value"]
            diff = recent - previous
            if abs(diff) > 0.05 * previous:
                trend = "improving" if diff < 0 else "worsening"
                # For weight, direction depends on context
                if metric_name in ("oxygen_saturation",):
                    trend = "improving" if diff > 0 else "worsening"

        trends.append(HealthTrend(
            metric_name=metric_name.replace("_", " ").title(),
            unit=units.get(metric_name, ""),
            data_points=data_points,
            trend=trend,
            normal_range=normal_ranges.get(metric_name),
        ))

    return trends


def get_patient_summary(patient_id: str) -> Optional[PatientSummary]:
    """Get aggregated patient summary."""
    patient = get_patient(patient_id)
    if not patient:
        return None

    visits = get_visits(patient_id)
    trends = get_health_trends(patient_id)

    # Collect all diagnoses across visits
    all_diagnoses = []
    for v in visits:
        all_diagnoses.extend(v.diagnosis)

    return PatientSummary(
        patient_id=patient_id,
        patient_name=patient.name,
        total_visits=len(visits),
        last_visit_date=visits[-1].visit_date if visits else None,
        active_conditions=patient.chronic_conditions,
        current_medications=patient.current_medications,
        allergies=patient.allergies,
        health_trends=trends,
        risk_factors=list(set(all_diagnoses)),
    )


def list_all_patients() -> List[Patient]:
    """List all registered patients."""
    _load_cache_from_db()
    return list(_patients_cache.values())
