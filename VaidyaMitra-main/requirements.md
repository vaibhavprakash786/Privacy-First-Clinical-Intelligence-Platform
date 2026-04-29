
# Requirements Document: VAIDYAMITRA

## Introduction

VAIDYAMITRA is a privacy-preserving clinical intelligence system designed to improve doctor efficiency and understanding of patient data during consultations. The system acts as a decision-support assistant that processes clinical information while maintaining strict privacy standards through mandatory PII/PHI masking. It addresses the critical challenge of information overload faced by doctors who must quickly understand patient conditions from long histories, multiple lab reports, prescriptions, and visit notes within limited consultation time.

Beyond clinical intelligence, VaidyaMitra integrates affordable healthcare access through Jan Aushadhi (PMBJP) generic medicine alternatives, multilingual support for 9 Indian languages, and AI-powered medical report simplification to make complex medical jargon understandable at a Grade 6 reading level.

This system is strictly a decision-support tool and does NOT provide diagnosis or treatment recommendations.

## Glossary

- **VaidyaMitra_System**: The complete VAIDYAMITRA system
- **Privacy_Layer**: The component responsible for detecting and masking PII/PHI using Microsoft Presidio and custom regex patterns
- **PII**: Personally Identifiable Information (names, phone numbers, addresses, email)
- **PHI**: Protected Health Information (medical record numbers, Aadhaar numbers, PAN numbers)
- **Clinical_Intelligence_Engine**: The AI-powered component that generates summaries, detects changes, predicts diseases, and provides insights via AWS Bedrock (Meta Llama 3)
- **Agentic_Orchestrator**: The intent-aware routing layer that classifies user queries and delegates to specialized sub-agents
- **Doctor_Interface**: The Next.js frontend for doctors to interact with the system
- **Clinical_Data**: Patient medical information including histories, lab reports, prescriptions, and visit notes
- **Clinical_Summary**: A concise AI-generated overview of patient clinical status
- **Change_Detection**: The process of identifying important differences between patient visits
- **Voice_Query_System**: The component that processes voice-based doctor queries in 9 Indian languages
- **Anonymized_Data**: Clinical data with all PII/PHI removed or masked
- **Decision_Support**: Information provided to assist clinical decision-making without making diagnoses
- **DataGuard**: The privacy scrubbing service that handles text, image, PDF, and JSON data
- **Jan_Aushadhi_Engine**: The generic medicine search component using the PMBJP catalog
- **Medicine_Identifier**: The drug identification and comparison service
- **Report_Simplifier**: The AI-powered medical report simplification engine
- **RAG_Service**: Retrieval-Augmented Generation service for context-grounded AI responses
- **Translation_Service**: Multilingual translation supporting 9 Indian languages plus English
- **VM_ID**: VaidyaMitra Patient Identifier — unique ID assigned to each registered patient
- **PMBJP**: Pradhan Mantri Bhartiya Janaushadhi Pariyojana — government generic medicines catalog

---

## Requirements

### Requirement 1: Privacy-Preserving Data Protection

**User Story:** As a healthcare provider, I want all patient identifiable information automatically protected, so that clinical data can be safely processed while maintaining privacy and compliance.

#### Acceptance Criteria

1. WHEN Clinical_Data is received by THE VaidyaMitra_System, THE Privacy_Layer SHALL detect all PII and PHI before any AI processing occurs
2. WHEN PII or PHI is detected, THE Privacy_Layer SHALL mask or anonymize the sensitive information in real-time before any downstream processing
3. THE Clinical_Intelligence_Engine SHALL process only Anonymized_Data
4. WHEN Clinical_Data contains names, phone numbers, Aadhaar numbers, PAN numbers, email addresses, or medical record numbers, THE Privacy_Layer SHALL replace them with anonymized tokens
5. THE VaidyaMitra_System SHALL maintain a privacy-first architecture where no component can access raw PII/PHI except the Privacy_Layer
6. THE Privacy_Layer SHALL support dual detection modes: Microsoft Presidio (NLP-based) and custom regex patterns for Indian-specific identifiers

---

### Requirement 2: Multi-Format Data Input

**User Story:** As a doctor, I want to input patient data through multiple methods, so that I can work with different data sources and formats efficiently.

#### Acceptance Criteria

1. WHEN a user manually enters Clinical_Data, THE VaidyaMitra_System SHALL accept and process the text input through the clinical data submission endpoint
2. WHEN a user uploads a medical report as a PDF, THE VaidyaMitra_System SHALL extract the clinical content using OCR (PyMuPDF + OpenCV preprocessing)
3. WHEN a user uploads a medical report as an image (JPEG/PNG), THE VaidyaMitra_System SHALL extract clinical content using image OCR
4. WHEN structured data is provided in JSON format, THE VaidyaMitra_System SHALL parse and process the data through the DataGuard scrubbing endpoint
5. WHEN data input fails validation, THE VaidyaMitra_System SHALL return a descriptive error message indicating the specific validation failure

---

### Requirement 3: AI-Powered Clinical Summarization

**User Story:** As a doctor, I want AI-generated concise clinical summaries, so that I can quickly understand patient status without reading through lengthy records.

#### Acceptance Criteria

1. WHEN Anonymized_Data is provided, THE Clinical_Intelligence_Engine SHALL generate a Clinical_Summary using AWS Bedrock Meta Llama 3
2. THE Clinical_Intelligence_Engine SHALL use semantic understanding to identify key clinical concepts from patient history, vitals, visits, and lab results
3. THE Clinical_Summary SHALL include current conditions, key findings, medication review, risk factors, and recommended follow-ups
4. THE Clinical_Intelligence_Engine SHALL provide explainable reasoning for each insight included in the summary
5. WHEN a patient has multiple visits, THE Clinical_Intelligence_Engine SHALL generate a comprehensive summary incorporating the full visit history

---

### Requirement 4: Temporal Change Detection

**User Story:** As a doctor, I want to see what changed since the last visit, so that I can focus on new developments and progression patterns.

#### Acceptance Criteria

1. WHEN Clinical_Data from multiple visits is available, THE Clinical_Intelligence_Engine SHALL identify significant changes between visits
2. THE Clinical_Intelligence_Engine SHALL detect trends in vitals, symptoms, diagnoses, and medication changes
3. WHEN changes are detected, THE Clinical_Intelligence_Engine SHALL highlight clinically relevant changes with severity categorization (critical, important, minor)
4. THE Clinical_Intelligence_Engine SHALL identify progression patterns in chronic conditions
5. WHEN no significant changes are detected, THE Clinical_Intelligence_Engine SHALL explicitly indicate clinical stability

---

### Requirement 5: Voice-Based Query Interface

**User Story:** As a doctor, I want to ask questions using voice commands in my preferred language, so that I can interact with the system hands-free during patient consultations.

#### Acceptance Criteria

1. WHEN a doctor speaks a query, THE Voice_Query_System SHALL accept the transcribed text in any of the 9 supported Indian languages plus English
2. WHEN a voice query is received in a non-English language, THE Translation_Service SHALL detect the language and translate the query to English for AI processing
3. THE Clinical_Intelligence_Engine SHALL generate contextually relevant responses to clinical queries via the Agentic_Orchestrator
4. WHEN the AI generates a response, THE Translation_Service SHALL translate the response back to the doctor's language
5. THE Voice_Query_System SHALL support text-to-speech playback of the AI response

---

### Requirement 6: Doctor-Friendly Dashboard

**User Story:** As a doctor, I want a simplified clinical view, so that I can access critical information quickly without navigating complex interfaces.

#### Acceptance Criteria

1. THE Doctor_Interface SHALL display a dashboard with patient statistics, system architecture overview, quick access to all modules, and recent activity
2. THE Doctor_Interface SHALL provide dedicated pages for: Patients, Clinical Data, Medical Records, Report Simplifier, Disease Prediction, Generic Medicine, Medicine Identifier, Voice Query, and AI Query
3. THE Doctor_Interface SHALL support both dark mode and light mode themes with proper contrast
4. THE Doctor_Interface SHALL provide a persistent sidebar navigation with categorized menu items (Clinical, AI Tools, Assistant)
5. THE Doctor_Interface SHALL maintain responsive layouts optimized for clinical workflows

---

### Requirement 7: Patient Management

**User Story:** As a healthcare provider, I want to register, manage, and track patients throughout their care journey with unique identifiers.

#### Acceptance Criteria

1. WHEN a new patient is registered, THE VaidyaMitra_System SHALL assign a unique VM_ID (VaidyaMitra Patient Identifier)
2. THE VaidyaMitra_System SHALL capture patient demographics: name, age, gender, blood group, phone, email, address, allergies, chronic conditions, current medications, emergency contact, and language preference
3. WHEN patient PII is submitted, THE Privacy_Layer SHALL mask the data before storage in DynamoDB
4. THE VaidyaMitra_System SHALL support adding visit records to a patient with vitals, complaints, assessments, diagnoses, and follow-up dates
5. THE VaidyaMitra_System SHALL maintain EHR-style records per patient with AI-powered clinical summaries and health trends

---

### Requirement 8: Disease Prediction

**User Story:** As a doctor, I want AI-assisted disease risk assessment based on symptoms, so that I can consider possible conditions and order appropriate tests.

#### Acceptance Criteria

1. WHEN a list of symptoms is provided, THE Clinical_Intelligence_Engine SHALL predict possible diseases using a combination of Medicure ML symptom-disease mapping and AI reasoning
2. THE Clinical_Intelligence_Engine SHALL cover at least 60 conditions in the symptom-disease knowledge base
3. WHEN diseases are predicted, THE Clinical_Intelligence_Engine SHALL provide risk percentages, recommended diagnostic tests, and AI reasoning for each prediction
4. THE Clinical_Intelligence_Engine SHALL clearly indicate these are AI-assisted assessments requiring doctor validation
5. THE VaidyaMitra_System SHALL cache disease prediction results in DynamoDB with configurable TTL

---

### Requirement 9: Generic Medicine Engine (Jan Aushadhi)

**User Story:** As a doctor, I want to find affordable generic alternatives for branded medicines, so that I can help patients reduce healthcare costs.

#### Acceptance Criteria

1. WHEN a branded medicine name is provided, THE Jan_Aushadhi_Engine SHALL search the PMBJP catalog for matching generic alternatives
2. THE Jan_Aushadhi_Engine SHALL display price comparisons and calculate savings percentage between branded and generic options
3. WHEN no exact match is found in the PMBJP catalog, THE Jan_Aushadhi_Engine SHALL use AI to identify the generic equivalent and provide alternatives
4. THE Jan_Aushadhi_Engine SHALL support image-based medicine identification for finding generic alternatives
5. THE VaidyaMitra_System SHALL maintain a local PMBJP catalog (CSV) with 50+ medicines for offline capability

---

### Requirement 10: Medicine Identifier

**User Story:** As a doctor or pharmacist, I want to identify medicines and compare branded vs generic versions, so that I can make informed prescription decisions.

#### Acceptance Criteria

1. WHEN a medicine name is provided, THE Medicine_Identifier SHALL return comprehensive drug information including composition, uses, side effects, and alternatives
2. THE Medicine_Identifier SHALL support AI-powered image identification of medicine tablets and packaging
3. WHEN a branded medicine is queried, THE Medicine_Identifier SHALL provide a comparison with its generic equivalent including efficacy, cost, and availability
4. THE Medicine_Identifier SHALL support full-text search across the medicines catalog
5. THE VaidyaMitra_System SHALL cache medicine identification results with configurable TTL (7 days default)

---

### Requirement 11: Medical Report Simplification

**User Story:** As a doctor, I want to convert complex medical reports into patient-friendly language, so that patients can understand their health conditions better.

#### Acceptance Criteria

1. WHEN a medical report text is provided, THE Report_Simplifier SHALL convert complex medical jargon to Grade 6 readability using AI
2. THE Report_Simplifier SHALL support multiple input formats: plain text, uploaded PDF, and uploaded images
3. WHEN Bedrock AI is unavailable, THE Report_Simplifier SHALL fall back to a jargon-replacement map covering 40+ medical terms
4. THE Report_Simplifier SHALL generate structured summaries with: overview, key findings, health concerns, action items, medications, and severity assessment
5. THE Report_Simplifier SHALL support translation of simplified reports into any of the 9 supported Indian languages

---

### Requirement 12: Multilingual Support

**User Story:** As a healthcare provider serving diverse patient populations, I want the system to operate in multiple Indian languages, so that language is not a barrier to healthcare access.

#### Acceptance Criteria

1. THE Translation_Service SHALL support translation between English and 9 Indian languages: Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, and Punjabi
2. THE Translation_Service SHALL provide language detection using Unicode script range analysis
3. THE Translation_Service SHALL use AI-powered translation via Bedrock for accurate medical terminology translation
4. WHEN Bedrock AI is unavailable, THE Translation_Service SHALL fall back to medical phrase replacement for Hindi
5. THE Doctor_Interface SHALL provide pre-translated UI strings for all supported languages

---

### Requirement 13: Agentic AI Orchestration

**User Story:** As a doctor, I want to ask natural language questions and have the AI automatically route to the right tool, so that I get the most relevant response without selecting specific features.

#### Acceptance Criteria

1. WHEN a natural language query is received, THE Agentic_Orchestrator SHALL classify the intent into one of: clinical_summary, change_detection, disease_prediction, generic_medicine, clinical_query, or risk_monitoring
2. THE Agentic_Orchestrator SHALL apply privacy masking to the query before any AI processing
3. THE Agentic_Orchestrator SHALL route the query to the appropriate sub-agent based on classified intent
4. THE Agentic_Orchestrator SHALL check DynamoDB cache for identical masked queries before invoking AI
5. THE Agentic_Orchestrator SHALL return structured responses with intent classification, agent used, reasoning, and source citations

---

### Requirement 14: Real-Time PII Detection Pipeline

**User Story:** As a security officer, I want PII detection to occur before AI processing across all data formats, so that privacy breaches are prevented.

#### Acceptance Criteria

1. THE Privacy_Layer SHALL operate as the first processing stage for all incoming Clinical_Data
2. THE DataGuard service SHALL support PII scrubbing across four formats: text, images, PDFs, and JSON dictionaries
3. IF THE Privacy_Layer fails, THE VaidyaMitra_System SHALL prevent AI processing and return a privacy error
4. THE Privacy_Layer SHALL log PII/PHI detection events for audit purposes with entity types, confidence scores, and timestamps
5. THE Privacy_Layer SHALL support consistent tokenization where the same PII always maps to the same anonymized token within a session

---

### Requirement 15: Scalable Cloud Architecture

**User Story:** As an IT administrator, I want the system deployed on AWS with scalable infrastructure, so that it can handle production workloads reliably.

#### Acceptance Criteria

1. THE VaidyaMitra_System SHALL support deployment on AWS EC2 using Docker Compose with Nginx reverse proxy
2. THE VaidyaMitra_System SHALL support serverless deployment via AWS SAM (Lambda + API Gateway + DynamoDB + S3)
3. THE VaidyaMitra_System SHALL implement rate limiting, request audit logging, and graceful error handling middleware
4. THE VaidyaMitra_System SHALL implement DynamoDB-backed caching with configurable TTLs per service (medicine: 7d, disease: 1d, reports: 3d, queries: 12h, embeddings: 30d)
5. THE VaidyaMitra_System SHALL support auto/bedrock/mock AI modes for flexible deployment without AWS dependencies during development
