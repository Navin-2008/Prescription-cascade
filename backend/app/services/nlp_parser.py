from __future__ import annotations

import re
from typing import Dict, List, Optional
from datetime import datetime

from app.services import knowledge


def extract_symptoms_from_note(note: str) -> List[Dict]:
    """Primitive symptom extractor: finds common symptom keywords and rough dates."""
    if not note:
        return []

    keywords = ["swelling", "pain", "rash", "cough", "fever", "edema", "nausea"]
    found = []
    for kw in keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", note, flags=re.I):
            found.append({"symptom_name": kw, "onset_date": "unknown"})

    return found


def extract_prescriptions_from_note(note: str) -> List[Dict]:
    if not note:
        return []

    extracted = []
    date = extract_date(note) or "unknown"
    knowledge_data = knowledge.list_drugs()
    for drug_entry in knowledge_data:
        drug_name = drug_entry["name"]
        if re.search(r"\b" + re.escape(drug_name) + r"\b", note, flags=re.I):
            extracted.append({"drug_name": drug_name.capitalize(), "start_date": date})

    return extracted


def extract_date(note: str) -> Optional[str]:
    if not note:
        return None

    match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", note)
    if match:
        return match.group(1)

    return None


def extract_entities_from_note(note: str) -> Dict[str, object]:
    symptoms = extract_symptoms_from_note(note)
    prescriptions = extract_prescriptions_from_note(note)
    score = 0.2
    if symptoms:
        score += 0.3
    if prescriptions:
        score += 0.3
    if note and ("started" in note.lower() or "prescribed" in note.lower()):
        score += 0.1
    confidence = min(0.95, score)

    return {
        "extracted_symptoms": symptoms,
        "extracted_prescriptions": prescriptions,
        "confidence": confidence,
    }
