import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "cascade.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        patient_id TEXT PRIMARY KEY,
        clinical_note TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS prescriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT,
        drug_name TEXT,
        start_date TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS symptoms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT,
        symptom_name TEXT,
        onset_date TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS diagnoses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT,
        icd_code TEXT,
        description TEXT,
        diagnosed_date TEXT,
        diagnosing_physician TEXT
    )
    """)
    conn.commit()
    conn.close()


def save_record(record: Dict) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    pid = record.get("patient_id")
    clinical = record.get("clinical_note")
    cur.execute("INSERT OR REPLACE INTO patients (patient_id, clinical_note) VALUES (?,?)", (pid, clinical))
    for p in record.get("prescriptions", []):
        cur.execute(
            "INSERT INTO prescriptions (patient_id, drug_name, start_date) VALUES (?,?,?)",
            (pid, p.get("drug_name"), p.get("start_date")),
        )
    for s in record.get("symptoms", []):
        cur.execute(
            "INSERT INTO symptoms (patient_id, symptom_name, onset_date) VALUES (?,?,?)",
            (pid, s.get("symptom_name"), s.get("onset_date")),
        )
    for d in record.get("diagnoses", []):
        cur.execute(
            "INSERT INTO diagnoses (patient_id, icd_code, description, diagnosed_date, diagnosing_physician) VALUES (?,?,?,?,?)",
            (
                pid,
                d.get("icd_code"),
                d.get("description"),
                d.get("diagnosed_date"),
                d.get("diagnosing_physician"),
            ),
        )
    conn.commit()
    conn.close()


def get_patient_record(patient_id: str) -> Optional[Dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    patient_row = cur.execute(
        "SELECT patient_id, clinical_note FROM patients WHERE patient_id = ?",
        (patient_id,),
    ).fetchone()
    if not patient_row:
        conn.close()
        return None

    prescriptions = [
        {"drug_name": row["drug_name"], "start_date": row["start_date"]}
        for row in cur.execute(
            "SELECT drug_name, start_date FROM prescriptions WHERE patient_id = ? ORDER BY start_date",
            (patient_id,),
        ).fetchall()
    ]
    symptoms = [
        {"symptom_name": row["symptom_name"], "onset_date": row["onset_date"]}
        for row in cur.execute(
            "SELECT symptom_name, onset_date FROM symptoms WHERE patient_id = ? ORDER BY onset_date",
            (patient_id,),
        ).fetchall()
    ]
    diagnoses = [
        {
            "icd_code": row["icd_code"],
            "description": row["description"],
            "diagnosed_date": row["diagnosed_date"],
            "diagnosing_physician": row["diagnosing_physician"],
        }
        for row in cur.execute(
            "SELECT icd_code, description, diagnosed_date, diagnosing_physician FROM diagnoses WHERE patient_id = ? ORDER BY diagnosed_date",
            (patient_id,),
        ).fetchall()
    ]
    conn.close()

    return {
        "patient_id": patient_row["patient_id"],
        "clinical_note": patient_row["clinical_note"],
        "prescriptions": prescriptions,
        "symptoms": symptoms,
        "diagnoses": diagnoses,
    }


def get_patient_timeline(patient_id: str) -> Optional[Dict]:
    record = get_patient_record(patient_id)
    if record is None:
        return None

    from app.services import graph_engine

    timeline = graph_engine.build_timeline(record)
    return {
        "patient_id": patient_id,
        "timeline": [
            {
                "event_type": event.kind,
                "label": event.label,
                "date": event.date.isoformat() if event.date else None,
                "source": event.source,
                "details": event.details,
            }
            for event in timeline
        ],
    }
