# Prescription Cascade Detector — API Spec (minimal)

## POST /api/ingest/record
- Purpose: Ingest a patient record (clinical note, prescriptions, symptoms).
- Request JSON: matches `PatientRecordRequest` pydantic model.
- Response: {"status":"ok","saved":true}

Example request:
```
{
  "patient_id": "p1",
  "clinical_note": "Patient started amlodipine and later developed ankle swelling.",
  "prescriptions": [{"drug_name": "Amlodipine", "start_date": "2026-06-01"}],
  "symptoms": [{"symptom_name": "Ankle swelling", "onset_date": "2026-06-21"}]
}
```

## POST /api/cascade/analyze
- Purpose: Analyze a patient record for suspected prescription cascades.
- Request JSON: same shape as `PatientRecordRequest` (can be previously ingested record or ad-hoc payload).
- Response JSON: `CascadeAlertResponse` with `has_cascade`, `suspected_chain`, and `recommendation`.

## GET /healthz
- Purpose: simple health check returning {"status":"ok"}.

Notes:
- This minimal spec is intended for the hackathon demo. Later steps:
  - Add authentication, rate limits, and schema examples in OpenAPI.
  - Persist ingested records to a database and add retrieval endpoints.
  - Add async background processing for heavy NLP/graph tasks.
