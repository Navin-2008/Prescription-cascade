# Prescription Cascade Detector Backend

This backend implements a minimal FastAPI service for the Prescription Cascade Detector hackathon.

## Features

- `POST /api/ingest/record` — ingest a patient record with clinical note, prescriptions, and symptoms.
- `POST /api/cascade/analyze` — analyze a patient record for suspected prescription cascades.
- `GET /healthz` — simple health check.

## Running locally

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start the app:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

3. Open the API docs:

- http://127.0.0.1:8000/docs

## Example payload

```json
{
  "patient_id": "p1",
  "clinical_note": "Patient started amlodipine and later developed ankle swelling.",
  "prescriptions": [
    {"drug_name": "Amlodipine", "start_date": "2026-06-01"},
    {"drug_name": "Furosemide", "start_date": "2026-06-30"}
  ],
  "symptoms": [
    {"symptom_name": "Ankle swelling", "onset_date": "2026-06-21"}
  ]
}
```

## Demo script

Run the API server and then execute the demo script from the backend folder:

```bash
python demo.py
```

This script sends an ingest request and then performs cascade analysis.

## Tests

Run:

```bash
pytest
```
