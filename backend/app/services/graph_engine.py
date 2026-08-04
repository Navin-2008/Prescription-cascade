from __future__ import annotations

from app.services import nlp_parser
from datetime import datetime
from typing import Any, Dict, List, Optional

SIDE_EFFECT_MAP = {
    "amlodipine": ["swelling", "edema", "ankle swelling"],
    "furosemide": ["gout", "joint pain", "dehydration"],
    "lisinopril": ["cough", "dizziness"],
}


class TimelineEvent:
    def __init__(self, date: Optional[datetime], label: str, kind: str, source: str):
        self.date = date
        self.label = label
        self.kind = kind
        self.source = source

    def __repr__(self) -> str:
        return f"TimelineEvent(date={self.date}, kind={self.kind}, label={self.label})"


def parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def build_timeline(record: Any) -> List[TimelineEvent]:
    timeline: List[TimelineEvent] = []
    for pres in record.prescriptions:
        timeline.append(TimelineEvent(
            date=parse_date(pres.start_date),
            label=pres.drug_name,
            kind="prescription",
            source=pres.drug_name,
        ))

    for sym in record.symptoms:
        timeline.append(TimelineEvent(
            date=parse_date(sym.onset_date),
            label=sym.symptom_name,
            kind="symptom",
            source=sym.symptom_name,
        ))

    if record.clinical_note:
        note_symptoms = nlp_parser.extract_symptoms_from_note(record.clinical_note)
        for item in note_symptoms:
            timeline.append(TimelineEvent(
                date=parse_date(item.get("onset_date")),
                label=item.get("symptom_name", "unknown symptom"),
                kind="symptom",
                source="clinical_note",
            ))

    return sorted(timeline, key=lambda event: event.date or datetime.min)


def match_side_effects(drug: str, symptom: str) -> bool:
    drug_key = drug.lower()
    symptom_text = symptom.lower()
    return any(effect in symptom_text for effect in SIDE_EFFECT_MAP.get(drug_key, []))


def detect_cascade(record: Any) -> Any:
    if isinstance(record, dict):
        return detect_cascade_dict(record)
    return _detect_from_record(record)


def _detect_from_record(record: Any) -> Any:
    timeline = build_timeline(record)
    suspected_chain: List[str] = []
    detection_found = False
    if not timeline:
        return _response(record.patient_id, False, [])

    for i, event in enumerate(timeline):
        if event.kind != "prescription":
            continue
        drug = event.label
        for later_event in timeline[i+1:]:
            if later_event.kind == "symptom" and match_side_effects(drug, later_event.label):
                for follow_event in timeline[timeline.index(later_event)+1:]:
                    if follow_event.kind == "prescription" and follow_event.label.lower() != drug.lower():
                        suspected_chain = [
                            f"{drug} -> Prescribed",
                            f"{later_event.label} -> Documented",
                            f"{follow_event.label} -> Prescribed",
                        ]
                        detection_found = True
                        break
                if detection_found:
                    break
        if detection_found:
            break

    if detection_found:
        return _response(record.patient_id, True, suspected_chain)
    return _response(record.patient_id, False, [])


def _response(patient_id: str, has_cascade: bool, chain: List[str]) -> Any:
    from app.schemas import CascadeAlertResponse

    recommendation = (
        "Suspected prescription cascade detected. Re-evaluate the earlier medication and"
        " consider deprescribing the later medication if appropriate."
    )
    if not has_cascade:
        recommendation = "No prescription cascade detected."
    return CascadeAlertResponse(
        patient_id=patient_id,
        has_cascade=has_cascade,
        suspected_chain=chain,
        recommendation=recommendation,
    )


def detect_cascade_dict(data: Dict[str, Any]) -> Any:
    from app.schemas import PatientRecordRequest

    rec = PatientRecordRequest(**data)
    return _detect_from_record(rec)
