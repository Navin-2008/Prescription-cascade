from typing import List, Dict
import re


def extract_symptoms_from_note(note: str) -> List[Dict]:
    """Primitive symptom extractor: finds common symptom keywords and rough dates.

    This is a stub for the NLP component; replace with a proper model later.
    """
    if not note:
        return []

    keywords = ["swelling", "pain", "rash", "cough", "fever", "edema", "nausea"]
    found = []
    for kw in keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", note, flags=re.I):
            found.append({"symptom_name": kw, "onset_date": "unknown"})

    return found


def normalize_prescriptions(prescriptions: List[Dict]) -> List[Dict]:
    """Normalize prescription dicts to lower-case drug names and iso dates when present."""
    out = []
    for p in prescriptions:
        out.append({
            "drug_name": p.get("drug_name", "").lower(),
            "start_date": p.get("start_date") or "unknown",
        })
    return out
