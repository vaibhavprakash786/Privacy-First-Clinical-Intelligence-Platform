/**
 * VaidyaMitra API Client v2
 * Supports all endpoints: patients, records, reports, scrubbing, voice, medicine, translation
 */

let API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
if (API_URL === '/' || API_URL.trim() === '') {
  API_URL = 'http://localhost:8000';
}

async function request(endpoint: string, options: RequestInit = {}): Promise<any> {
  const url = `${API_URL}${endpoint}`;
  const config: RequestInit = {
    headers: { 'Content-Type': 'application/json', ...options.headers as Record<string, string> },
    ...options,
  };
  const res = await fetch(url, config);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'API request failed');
  }
  return res.json();
}

// ===== Health =====
export const healthCheck = () => request('/api/v1/health');

// ===== Clinical (existing) =====
export const submitClinicalData = (data: any) =>
  request('/api/v1/clinical-data', { method: 'POST', body: JSON.stringify(data) });

export const predictDisease = (symptoms: string[], patientId?: string) =>
  request('/api/v1/predict-disease', { method: 'POST', body: JSON.stringify({ symptoms, patient_id: patientId }) });

export const findGenericMedicine = (name: string, qty: number = 1) =>
  request('/api/v1/generic-medicine', { method: 'POST', body: JSON.stringify({ medicine_name: name, quantity: qty }) });

export const findGenericMedicineImage = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const url = `${API_URL}/api/v1/generic-medicine/image`;
  const res = await fetch(url, { method: 'POST', body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Image upload failed');
  }
  return res.json();
};

export const aiQuery = (query: string, patientId?: string) =>
  request('/api/v1/query', { method: 'POST', body: JSON.stringify({ query, patient_id: patientId }) });

// ===== Patients =====
export const registerPatient = (data: any) =>
  request('/api/v1/patients', { method: 'POST', body: JSON.stringify(data) });

export const listPatients = (search?: string) =>
  request(`/api/v1/patients${search ? `?search=${encodeURIComponent(search)}` : ''}`);

export const getPatient = (id: string) => request(`/api/v1/patients/${id}`);

export const updatePatient = (id: string, data: any) =>
  request(`/api/v1/patients/${id}`, { method: 'PUT', body: JSON.stringify(data) });

export const addVisit = (patientId: string, data: any) =>
  request(`/api/v1/patients/${patientId}/visits`, { method: 'POST', body: JSON.stringify(data) });

export const getVisits = (patientId: string) =>
  request(`/api/v1/patients/${patientId}/visits`);

export const getRecords = (patientId: string) =>
  request(`/api/v1/patients/${patientId}/records`);

export const getTrends = (patientId: string) =>
  request(`/api/v1/patients/${patientId}/trends`);

export const getPatientAISummary = (patientId: string) =>
  request(`/api/v1/patients/${patientId}/ai-summary`, { method: 'POST' });

// ===== Reports =====
export const simplifyReport = (text: string, lang: string = 'en') =>
  request('/api/v1/reports/simplify', { method: 'POST', body: JSON.stringify({ report_text: text, language: lang }) });

export const summarizeReport = (text: string) =>
  request('/api/v1/reports/summarize', { method: 'POST', body: JSON.stringify({ report_text: text }) });

export const translateReport = (text: string, targetLang: string, sourceLang: string = 'en') =>
  request('/api/v1/reports/translate', { method: 'POST', body: JSON.stringify({ text, target_lang: targetLang, source_lang: sourceLang }) });

export const uploadReportFile = async (file: File, patientId?: string): Promise<any> => {
  const formData = new FormData();
  formData.append('file', file);
  if (patientId) formData.append('patient_id', patientId);

  const url = `${API_URL}/api/v1/upload/report`;
  const res = await fetch(url, { method: 'POST', body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
};

// ===== DataGuard Scrubbing =====
export const scrubText = (text: string) =>
  request('/api/v1/scrub/text', { method: 'POST', body: JSON.stringify({ text }) });

export const scrubDict = (data: any) =>
  request('/api/v1/scrub/dict', { method: 'POST', body: JSON.stringify({ data }) });

// ===== Voice =====
export const voiceQuery = (text: string, lang: string = 'en', patientId?: string) =>
  request('/api/v1/voice/query', { method: 'POST', body: JSON.stringify({ transcribed_text: text, language: lang, patient_id: patientId }) });

// ===== Medicine Identifier =====
export const identifyMedicine = (name: string) =>
  request('/api/v1/medicine/identify', { method: 'POST', body: JSON.stringify({ medicine_name: name }) });

export const identifyMedicineImage = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const url = `${API_URL}/api/v1/medicine/identify/image`;
  const res = await fetch(url, { method: 'POST', body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
};

export const compareMedicine = (brand: string) =>
  request('/api/v1/medicine/compare', { method: 'POST', body: JSON.stringify({ brand_name: brand }) });

export const listMedicines = () => request('/api/v1/medicine/list');

export const searchMedicines = (q: string) =>
  request(`/api/v1/medicine/search?q=${encodeURIComponent(q)}`);

// ===== Translation =====
export const getLanguages = () => request('/api/v1/languages');

export const getUIStrings = (lang: string) => request(`/api/v1/languages/${lang}/ui`);

export const translateText = (text: string, targetLang: string, sourceLang: string = 'en') =>
  request('/api/v1/translate', { method: 'POST', body: JSON.stringify({ text, target_lang: targetLang, source_lang: sourceLang }) });

export const detectLanguage = (text: string) =>
  request('/api/v1/detect-language', { method: 'POST', body: JSON.stringify({ text }) });
