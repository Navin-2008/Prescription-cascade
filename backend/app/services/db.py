import sqlite3
from pathlib import Path
from typing import Dict

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
    conn.commit()
    conn.close()


def save_record(record: Dict) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    pid = record.get("patient_id")
    clinical = record.get("clinical_note")
    cur.execute("INSERT OR REPLACE INTO patients (patient_id, clinical_note) VALUES (?,?)", (pid, clinical))
    for p in record.get("prescriptions", []):
        cur.execute("INSERT INTO prescriptions (patient_id, drug_name, start_date) VALUES (?,?,?)", (pid, p.get("drug_name"), p.get("start_date")))
    for s in record.get("symptoms", []):
        cur.execute("INSERT INTO symptoms (patient_id, symptom_name, onset_date) VALUES (?,?,?)", (pid, s.get("symptom_name"), s.get("onset_date")))
    conn.commit()
    conn.close()
