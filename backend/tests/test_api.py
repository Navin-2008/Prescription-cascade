import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_ingest_record():
    payload = {
        "patient_id": "test1",
        "clinical_note": "Patient starts amlodipine and reports swelling.",
        "prescriptions": [{"drug_name": "Amlodipine", "start_date": "2026-06-01"}],
        "symptoms": [{"symptom_name": "Ankle swelling", "onset_date": "2026-06-21"}]
    }
    resp = client.post("/api/ingest/record", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "saved": True}


def test_analyze_cascade():
    payload = {
        "patient_id": "test2",
        "clinical_note": "Patient started amlodipine and later developed ankle swelling.",
        "prescriptions": [
            {"drug_name": "Amlodipine", "start_date": "2026-06-01"},
            {"drug_name": "Furosemide", "start_date": "2026-06-30"}
        ],
        "symptoms": [{"symptom_name": "Ankle swelling", "onset_date": "2026-06-21"}]
    }
    resp = client.post("/api/cascade/analyze", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["patient_id"] == "test2"
    assert body["has_cascade"] is True
    assert "Furosemide" in body["suspected_chain"][-1]
