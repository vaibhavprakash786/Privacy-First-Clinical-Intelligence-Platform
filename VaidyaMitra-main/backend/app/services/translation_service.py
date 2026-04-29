"""
Translation Service

Multilingual support for Indian languages.
Supports: Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi, English.
Uses AWS Bedrock Claude for real AI translation, with phrase-swap fallback.
"""

import logging
import re
from typing import Dict, List, Optional

import hashlib
from app.core.config import settings
from app.core.cache_client import get_cache_client, CacheClient
from app.services.bedrock_client import get_bedrock_client

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "native": "English", "script": "Latin"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "script": "Devanagari"},
    "bn": {"name": "Bengali", "native": "বাংলা", "script": "Bengali"},
    "ta": {"name": "Tamil", "native": "தமிழ்", "script": "Tamil"},
    "te": {"name": "Telugu", "native": "తెలుగు", "script": "Telugu"},
    "mr": {"name": "Marathi", "native": "मराठी", "script": "Devanagari"},
    "gu": {"name": "Gujarati", "native": "ગુજરાતી", "script": "Gujarati"},
    "kn": {"name": "Kannada", "native": "ಕನ್ನಡ", "script": "Kannada"},
    "ml": {"name": "Malayalam", "native": "മലയാളം", "script": "Malayalam"},
    "pa": {"name": "Punjabi", "native": "ਪੰਜਾਬੀ", "script": "Gurmukhi"},
}

# UI translation strings for multilingual interface
UI_STRINGS = {
    "en": {
        "welcome": "Welcome to VaidyaMitra",
        "dashboard": "Dashboard",
        "clinical_data": "Clinical Data",
        "disease_prediction": "Disease Prediction",
        "generic_medicine": "Generic Medicine",
        "ai_query": "AI Query",
        "voice_query": "Voice Query",
        "patients": "Patients",
        "records": "Medical Records",
        "reports": "Reports",
        "search": "Search",
        "submit": "Submit",
        "save": "Save",
        "cancel": "Cancel",
        "loading": "Loading...",
        "no_results": "No results found",
        "error": "An error occurred",
        "privacy_notice": "Your data is privacy-protected. PII/PHI is masked before AI processing.",
        "disclaimer": "This is AI-assisted analysis. Please consult a qualified healthcare professional.",
        "medicine_identifier": "Medicine Identifier",
        "report_simplifier": "Report Simplifier",
    },
    "hi": {
        "welcome": "वैद्यमित्र में आपका स्वागत है",
        "dashboard": "डैशबोर्ड",
        "clinical_data": "नैदानिक डेटा",
        "disease_prediction": "रोग पूर्वानुमान",
        "generic_medicine": "जेनेरिक दवा",
        "ai_query": "AI क्वेरी",
        "voice_query": "आवाज़ क्वेरी",
        "patients": "मरीज़",
        "records": "चिकित्सा रिकॉर्ड",
        "reports": "रिपोर्ट",
        "search": "खोजें",
        "submit": "जमा करें",
        "save": "सहेजें",
        "cancel": "रद्द करें",
        "loading": "लोड हो रहा है...",
        "no_results": "कोई परिणाम नहीं मिला",
        "error": "एक त्रुटि हुई",
        "privacy_notice": "आपका डेटा गोपनीयता-सुरक्षित है। AI प्रोसेसिंग से पहले PII/PHI छुपाया जाता है।",
        "disclaimer": "यह AI-सहायित विश्लेषण है। कृपया योग्य चिकित्सक से परामर्श करें।",
        "medicine_identifier": "दवा पहचानकर्ता",
        "report_simplifier": "रिपोर्ट सरलीकरण",
    },
    "bn": {
        "welcome": "বৈদ্যমিত্রে স্বাগতম",
        "dashboard": "ড্যাশবোর্ড",
        "clinical_data": "ক্লিনিকাল ডেটা",
        "disease_prediction": "রোগ পূর্বাভাস",
        "generic_medicine": "জেনেরিক ওষুধ",
        "ai_query": "AI প্রশ্ন",
        "voice_query": "ভয়েস প্রশ্ন",
        "patients": "রোগী",
        "records": "মেডিকেল রেকর্ড",
        "reports": "রিপোর্ট",
        "search": "অনুসন্ধান",
        "submit": "জমা দিন",
        "save": "সংরক্ষণ",
        "cancel": "বাতিল",
        "loading": "লোড হচ্ছে...",
        "no_results": "কোন ফলাফল পাওয়া যায়নি",
        "error": "একটি ত্রুটি ঘটেছে",
        "privacy_notice": "আপনার ডেটা গোপনীয়তা-সুরক্ষিত।",
        "disclaimer": "এটি AI-সহায়ক বিশ্লেষণ। একজন যোগ্য চিকিৎসকের সাথে পরামর্শ করুন।",
        "medicine_identifier": "ওষুধ শনাক্তকারী",
        "report_simplifier": "রিপোর্ট সরলীকরণ",
    },
    "ta": {
        "welcome": "வைத்யமித்ராவிற்கு வரவேற்கிறோம்",
        "dashboard": "டாஷ்போர்ட்",
        "patients": "நோயாளிகள்",
        "records": "மருத்துவ பதிவுகள்",
        "reports": "அறிக்கைகள்",
        "search": "தேடு",
        "submit": "சமர்ப்பி",
        "disclaimer": "இது AI உதவி பகுப்பாய்வு. தகுதியான மருத்துவரை அணுகவும்.",
    },
    "te": {
        "welcome": "వైద్యమిత్రకు స్వాగతం",
        "dashboard": "డ్యాష్‌బోర్డ్",
        "patients": "రోగులు",
        "records": "వైద్య రికార్డులు",
        "reports": "నివేదికలు",
        "search": "వెతకండి",
        "submit": "సమర్పించండి",
        "disclaimer": "ఇది AI-సహాయ విశ్లేషణ. అర్హత కలిగిన వైద్యుడిని సంప్రదించండి.",
    },
    "mr": {
        "welcome": "वैद्यमित्रमध्ये आपले स्वागत आहे",
        "dashboard": "डॅशबोर्ड",
        "patients": "रुग्ण",
        "records": "वैद्यकीय नोंदी",
        "reports": "अहवाल",
        "search": "शोधा",
        "submit": "सबमिट करा",
        "disclaimer": "हे AI-सहाय्यित विश्लेषण आहे. कृपया पात्र डॉक्टरांचा सल्ला घ्या.",
    },
}

# Common medical phrases in Hindi for fallback translation
MEDICAL_PHRASES_HI = {
    "blood pressure": "रक्तचाप",
    "heart rate": "हृदय गति",
    "blood sugar": "रक्त शर्करा",
    "cholesterol": "कोलेस्ट्रॉल",
    "diabetes": "मधुमेह",
    "fever": "बुखार",
    "headache": "सिरदर्द",
    "cough": "खांसी",
    "cold": "सर्दी",
    "infection": "संक्रमण",
    "allergy": "एलर्जी",
    "medicine": "दवाई",
    "tablet": "गोली",
    "injection": "इंजेक्शन",
    "test": "जांच",
    "report": "रिपोर्ट",
    "normal": "सामान्य",
    "abnormal": "असामान्य",
    "elevated": "बढ़ा हुआ",
    "low": "कम",
    "hospital": "अस्पताल",
    "doctor": "डॉक्टर",
    "patient": "मरीज़",
    "prescription": "नुस्खा",
    "diagnosis": "निदान",
    "treatment": "उपचार",
    "surgery": "शल्य चिकित्सा",
}


def get_supported_languages() -> Dict:
    """Return all supported languages."""
    return SUPPORTED_LANGUAGES


def get_ui_strings(lang: str) -> Dict:
    """Get UI translation strings for a language, falling back to English."""
    return UI_STRINGS.get(lang, UI_STRINGS["en"])


def detect_language(text: str) -> str:
    """Detect language of input text using Unicode script ranges."""
    if not text.strip():
        return "en"

    # Check for Devanagari (Hindi/Marathi)
    if re.search(r'[\u0900-\u097F]', text):
        if any(w in text for w in ["आहे", "करा", "नोंदी"]):
            return "mr"
        return "hi"
    # Bengali
    if re.search(r'[\u0980-\u09FF]', text):
        return "bn"
    # Tamil
    if re.search(r'[\u0B80-\u0BFF]', text):
        return "ta"
    # Telugu
    if re.search(r'[\u0C00-\u0C7F]', text):
        return "te"
    # Gujarati
    if re.search(r'[\u0A80-\u0AFF]', text):
        return "gu"
    # Kannada
    if re.search(r'[\u0C80-\u0CFF]', text):
        return "kn"
    # Malayalam
    if re.search(r'[\u0D00-\u0D7F]', text):
        return "ml"
    # Gurmukhi (Punjabi)
    if re.search(r'[\u0A00-\u0A7F]', text):
        return "pa"
    return "en"


def translate_medical_text(text: str, target_lang: str, source_lang: str = "en") -> Dict:
    """
    Translate medical text to target language.
    Uses Bedrock AI when available, falls back to phrase replacement.
    """
    if target_lang == source_lang:
        return {"translated_text": text, "source_lang": source_lang, "target_lang": target_lang}

    lang_info = SUPPORTED_LANGUAGES.get(target_lang, {})
    target_name = lang_info.get("name", target_lang)

    # ── Check Cache ─────────────
    cache = get_cache_client()
    text_hash = hashlib.sha256(text.encode()).hexdigest()
    cache_key = CacheClient.generate_cache_key("translate", text_hash, target_lang)
    
    cached = cache.get(cache_key)
    if cached is not None:
        logger.info(f"Translation CACHE HIT: {target_lang}")
        cached["from_cache"] = True
        return cached

    ai_client = get_bedrock_client()

    # Try AI-powered translation
    result = None
    if ai_client.mode == "bedrock":
        try:
            result = _translate_with_ai(ai_client, text, target_lang, source_lang, lang_info)
        except Exception as e:
            logger.warning(f"Bedrock translation failed, using fallback: {e}")

    # Fallback: phrase replacement
    if result is None:
        result = _translate_fallback(text, target_lang, source_lang, lang_info)

    result["from_cache"] = False

    # ── Store in Cache ───────────────────────────────────────
    cache.put(
        cache_key, result,
        ttl_hours=settings.CACHE_TTL_REPORT_HOURS,
        service="translate",
        query_text=text[:100],
    )
    
    return result


def _translate_with_ai(ai_client, text: str, target_lang: str, source_lang: str, lang_info: dict) -> Dict:
    """Use Bedrock Claude for real medical translation."""
    target_name = lang_info.get("name", target_lang)
    target_native = lang_info.get("native", target_lang)
    target_script = lang_info.get("script", "")

    system_prompt = f"""You are a medical translator specializing in Indian languages. 
Translate medical text accurately into {target_name} ({target_native}).

RULES:
1. Use the {target_script} script for the translation
2. Keep medical drug names in English (transliterate if helpful)
3. Keep numerical values, units, and dosages unchanged
4. Use commonly understood medical terminology in {target_name}
5. Maintain the same structure and formatting as the original
6. Be accurate — do not add or omit information
7. Use polite/formal register suitable for patient communication"""

    prompt = f"""Translate the following medical text from {SUPPORTED_LANGUAGES.get(source_lang, {}).get('name', 'English')} to {target_name} ({target_native}).

Return ONLY the translated text, nothing else.

TEXT TO TRANSLATE:
{text}"""

    translated = ai_client.invoke(prompt, system_prompt=system_prompt, temperature=0.1)

    return {
        "translated_text": translated.strip(),
        "source_lang": source_lang,
        "target_lang": target_lang,
        "target_language_name": target_name,
        "target_native_name": target_native,
        "ai_powered": True,
        "note": f"AI-powered medical translation to {target_name}",
        "disclaimer": "Machine translation — verify with a bilingual medical professional.",
    }


def _translate_fallback(text: str, target_lang: str, source_lang: str, lang_info: dict) -> Dict:
    """Fallback: phase replacement for Hindi, passthrough for others."""
    translated = text

    if target_lang == "hi":
        for eng, hindi in MEDICAL_PHRASES_HI.items():
            translated = re.sub(
                re.escape(eng), f"{hindi} ({eng})", translated, flags=re.IGNORECASE
            )

    return {
        "translated_text": translated,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "target_language_name": lang_info.get("name", target_lang),
        "target_native_name": lang_info.get("native", target_lang),
        "ai_powered": False,
        "note": f"Medical-aware translation to {lang_info.get('name', target_lang)}",
        "disclaimer": "Machine translation — verify with a bilingual medical professional.",
    }
