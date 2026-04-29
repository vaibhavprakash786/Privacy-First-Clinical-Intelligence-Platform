"""
Medical Report Processing Pipeline (AWS Lambda Adapter)

Coordinates the sequence:
1. S3 trigger -> PDF extraction
2. OpenCV Preprocessing
3. Amazon Textract (Forms & Tables)
4. DataGuard Privacy Masking
5. Amazon Bedrock Clinical Schema Extraction
6. Canonical Normalization
7. DynamoDB Storage
8. RAG Vectorization
"""

import json
import logging
import uuid
import time
from typing import Dict, Any, List

import boto3
import fitz  # PyMuPDF
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.s3_client import get_s3_client
from app.core.dynamodb_client import get_dynamodb_client, TABLE_CLINICAL_REPORTS
from app.services.privacy_layer import PrivacyLayer
from app.services.bedrock_client import get_bedrock_client
from app.services.rag_service import get_rag_service

from app.lambdas.cv2_utils import preprocess_for_ocr
from app.lambdas.clinical_normalizer import normalize_clinical_data

logger = logging.getLogger(__name__)

# Initialize singletons optimized for Lambda cold starts
privacy_layer = PrivacyLayer()
bedrock_client = get_bedrock_client()
rag_service = get_rag_service()
db_client = get_dynamodb_client()

aws_kwargs = {
    "region_name": settings.AWS_REGION,
}
if settings.AWS_ACCESS_KEY_ID:
    aws_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
    aws_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

textract_client = boto3.client('textract', **aws_kwargs)

def process_document(s3_bucket: str, s3_key: str, patient_id: str) -> Dict[str, Any]:
    """
    Main pipeline to process a clinical document.
    Can be invoked directly from FastAPI or deployed as a real Lambda handler.
    """
    report_id = str(uuid.uuid4())
    start_time = time.time()
    logger.info(f"Starting document pipeline for {s3_key}")
    
    try:
        # Step 1: Fetch from S3
        s3 = boto3.client('s3', **aws_kwargs)
        try:
            response = s3.get_object(Bucket=s3_bucket, Key=s3_key)
            file_bytes = response['Body'].read()
        except ClientError as e:
            logger.error(f"S3 fetch failed: {e}")
            return {"success": False, "error": "Could not read file from S3"}

        # Step 2: Convert to Images & OpenCV Preprocess
        images_to_process = []
        is_pdf = s3_key.lower().endswith('.pdf')
        
        if is_pdf:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=300) 
                raw_image_bytes = pix.tobytes("jpeg")
                
                # Preprocess with OpenCV
                cleaned_bytes = preprocess_for_ocr(raw_image_bytes)
                if cleaned_bytes:
                    images_to_process.append(cleaned_bytes)
                else: # Fallback to raw
                    images_to_process.append(raw_image_bytes)
        else:
            cleaned_bytes = preprocess_for_ocr(file_bytes)
            images_to_process.append(cleaned_bytes if cleaned_bytes else file_bytes)

        # Step 3: Textract OCR
        extracted_text_blocks = []
        for i, img_bytes in enumerate(images_to_process):
            logger.info(f"Running Textract on page {i+1}")
            try:
                txt_response = textract_client.analyze_document(
                    Document={'Bytes': img_bytes},
                    FeatureTypes=["FORMS", "TABLES"]
                )
                
                page_text = []
                for block in txt_response.get("Blocks", []):
                    if block["BlockType"] == "LINE":
                        page_text.append(block.get("Text", ""))
                        
                extracted_text_blocks.append("\n".join(page_text))
            except Exception as e:
                logger.error(f"Textract failed on page {i+1}: {e}")

        full_raw_text = "\n\n".join(extracted_text_blocks)
        
        if not full_raw_text.strip():
            return {"success": False, "error": "No text could be extracted from document"}

        # Step 4: Privacy Masking
        logger.info("Applying DataGuard Privacy Layer")
        masked_result = privacy_layer.detect_and_mask(full_raw_text)
        masked_text = masked_result.masked_text

        # Step 5: Bedrock Schema Extraction
        logger.info("Extracting clinical schema via Bedrock")
        system_prompt = """You are a clinical data extraction engine.
Given the OCR text of a medical report, extract the key medical entities strictly into a JSON schema.
Ensure you pull out lab results with their specific units, vital signs, medications, and diagnosed conditions.
Return ONLY valid JSON."""
        
        prompt = f"""Extract data from this medical report. Return valid JSON exactly matching:
{{
    "patient_demographics": {{"age": null, "gender": null, "blood_group": null}},
    "vitals": [ {{"name": "Blood Pressure", "value": "120/80", "unit": "mmHg"}} ],
    "diagnoses": ["condition 1", "condition 2"],
    "medications": [ {{"name": "DrugA", "dosage": "10mg", "frequency": "daily"}} ],
    "lab_results": [ {{"test_name": "Hemoglobin", "value": "14.5", "unit": "g/dl", "reference_range": "13-17"}} ],
    "clinical_notes": "Summary of any other free-text clinical findings."
}}

REPORT TEXT:
{masked_text}"""

        extracted_json = bedrock_client.invoke_json(prompt=prompt, system_prompt=system_prompt)

        # Step 6: Canonical Normalization
        final_normalized_data = normalize_clinical_data(extracted_json)
        
        # Step 7: Store to DynamoDB
        report_record = {
            "patient_id": patient_id,
            "report_id": report_id,
            "s3_key": s3_key,
            "raw_text_length": len(full_raw_text),
            "masked_text_length": len(masked_text),
            "extracted_data": json.dumps(final_normalized_data),
            "processed_at": int(time.time()),
            "status": "COMPLETED"
        }
        db_client.put_item(TABLE_CLINICAL_REPORTS, report_record)
        
        # Step 8: RAG Vectorization
        # We index the structured clinical text + original masked text
        rag_content = f"Patient {patient_id} Report Summary:\nStructured Data: {json.dumps(final_normalized_data, indent=2)}\n\nExtracted Notes: {masked_text}"
        doc_id = rag_service.store_document(
            content=rag_content,
            metadata={"patient_id": patient_id, "source": s3_key, "report_id": report_id},
            doc_type="clinical_report"
        )
        
        processing_time = round(time.time() - start_time, 2)
        logger.info(f"Pipeline completed in {processing_time}s. Report: {report_id}")
        
        return {
            "success": True, 
            "data": {
                "report_id": report_id,
                "rag_doc_id": doc_id,
                "processing_time_sec": processing_time,
                "extracted_data": final_normalized_data
            }
        }

    except Exception as e:
        logger.error(f"Pipeline failed critically: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

# Optional: AWS Lambda Event Handler wrapper
def lambda_handler(event, context):
    """Entry point when deployed via AWS Lambda triggers (S3 ObjectCreated)."""
    try:
        for record in event['Records']:
            s3_bucket = record['s3']['bucket']['name']
            s3_key = record['s3']['object']['key']
            
            # Extract patient_id from s3_key convention: /reports/{patient_id}/filename.pdf
            parts = s3_key.split('/')
            patient_id = parts[1] if len(parts) > 1 else 'unknown'
            
            process_document(s3_bucket, s3_key, patient_id)
            
        return {"statusCode": 200, "body": json.dumps("Success")}
    except Exception as e:
        logger.error(f"Lambda handler failed: {e}")
        return {"statusCode": 500, "body": json.dumps(str(e))}
