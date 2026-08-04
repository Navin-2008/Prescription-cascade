import json
from pathlib import Path
import requests

BASE_URL = "http://127.0.0.1:8000"

PAYLOAD = {
    "patient_id": "demo1",
    "clinical_note": "Patient started amlodipine and later developed ankle swelling.",
    "prescriptions": [
        {"drug_name": "Amlodipine", "start_date": "2026-06-01"},
        {"drug_name": "Furosemide", "start_date": "2026-06-30"}
    ],
    "symptoms": [
        {"symptom_name": "Ankle swelling", "onset_date": "2026-06-21"}
    ]
}


def main():
    print("Starting backend demo...\n")

    ingest_resp = requests.post(f"{BASE_URL}/api/ingest/record", json=PAYLOAD)
    print("Ingest response:")
    print(json.dumps(ingest_resp.json(), indent=2))
    print()

    analyze_resp = requests.post(f"{BASE_URL}/api/cascade/analyze", json=PAYLOAD)
    print("Cascade analysis response:")
    print(json.dumps(analyze_resp.json(), indent=2))


if __name__ == "__main__":
    main()
