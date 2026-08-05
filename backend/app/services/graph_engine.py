from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services import knowledge, nlp_parser


class TimelineEvent:
    def __init__(self, date: Optional[datetime], label: str, kind: str, source: str, details: Optional[Dict] = None):
        self.date = date
        self.label = label
        self.kind = kind
        self.source = source
        self.details = details or {}

    def __repr__(self) -> str:
        return f"TimelineEvent(date={self.date}, kind={self.kind}, label={self.label})"


def parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value or value.lower() == "unknown":
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


def _get_attribute(record: Any, name: str, default=None):
    if isinstance(record, dict):
        return record.get(name, default)
    return getattr(record, name, default)


def build_timeline(record: Any) -> List[TimelineEvent]:
    timeline: List[TimelineEvent] = []

    for pres in _get_attribute(record, "prescriptions", []):
        timeline.append(TimelineEvent(
            date=parse_date(_get_attribute(pres, "start_date", None)),
            label=_get_attribute(pres, "drug_name", ""),
            kind="prescription",
            source="ingest",
            details={"drug_name": _get_attribute(pres, "drug_name", ""), "start_date": _get_attribute(pres, "start_date", "unknown")},
        ))

    for sym in _get_attribute(record, "symptoms", []):
        timeline.append(TimelineEvent(
            date=parse_date(_get_attribute(sym, "onset_date", None)),
            label=_get_attribute(sym, "symptom_name", ""),
            kind="symptom",
            source="ingest",
            details={"symptom_name": _get_attribute(sym, "symptom_name", ""), "onset_date": _get_attribute(sym, "onset_date", "unknown")},
        ))

    for diag in _get_attribute(record, "diagnoses", []):
        diag_label = _get_attribute(diag, "description", "")
        icd_code = _get_attribute(diag, "icd_code")
        if icd_code:
            diag_label = f"{diag_label} ({icd_code})"
        timeline.append(TimelineEvent(
            date=parse_date(_get_attribute(diag, "diagnosed_date", None)),
            label=diag_label,
            kind="diagnosis",
            source="ingest",
            details={
                "description": _get_attribute(diag, "description", ""),
                "icd_code": icd_code,
                "diagnosed_date": _get_attribute(diag, "diagnosed_date", "unknown"),
                "diagnosing_physician": _get_attribute(diag, "diagnosing_physician", None),
            },
        ))

    clinical_note = _get_attribute(record, "clinical_note", None)
    if clinical_note:
        note_symptoms = nlp_parser.extract_symptoms_from_note(clinical_note)
        for item in note_symptoms:
            timeline.append(TimelineEvent(
                date=parse_date(item.get("onset_date")),
                label=item.get("symptom_name", "unknown symptom"),
                kind="symptom",
                source="clinical_note",
                details={"symptom_name": item.get("symptom_name", "unknown"), "onset_date": item.get("onset_date", "unknown")},
            ))

    return sorted(timeline, key=lambda event: event.date or datetime.max)


def _days_between(start: Optional[datetime], end: Optional[datetime]) -> int:
    if not start or not end:
        return -1
    return max(0, (end - start).days)


def _match_side_effects(drug: str, symptom: str) -> Optional[Dict]:
    candidates = knowledge.get_side_effects(drug)
    symptom_text = symptom.lower()
    for entry in candidates:
        if entry["symptom_name"].lower() in symptom_text:
            return entry
    return None


def _find_next_event(events: List[TimelineEvent], start_index: int, kind: str) -> Optional[TimelineEvent]:
    for event in events[start_index:]:
        if event.kind == kind:
            return event
    return None


def _find_next_symptom_for_drug(drug: str, events: List[TimelineEvent], start_index: int) -> Optional[tuple[TimelineEvent, Dict, int]]:
    for idx, event in enumerate(events[start_index:], start=start_index):
        if event.kind != "symptom":
            continue
        matched = _match_side_effects(drug, event.label)
        if matched:
            return event, matched, idx
    return None


def _score_confidence(effect_entry: Optional[Dict], days_after: int, has_misdiagnosis: bool) -> float:
    base = 0.2
    if effect_entry is None:
        return 0.2

    if days_after < 0:
        base = 0.5
    elif effect_entry["typical_onset_days_min"] <= days_after <= effect_entry["typical_onset_days_max"]:
        base = 0.85
    elif days_after <= effect_entry["typical_onset_days_max"] * 2:
        base = 0.6
    else:
        base = 0.4

    if has_misdiagnosis:
        base += 0.1

    return min(1.0, base)


def detect_cascade(record: Any) -> Any:
    if isinstance(record, dict):
        return detect_cascade_dict(record)
    return _detect_from_record(record)


def _detect_from_record(record: Any) -> Any:
    timeline = build_timeline(record)
    suspected_chains: List[List[Dict]] = []
    if not timeline:
        return _response(_get_attribute(record, "patient_id", "unknown"), False, [])

    for index, event in enumerate(timeline):
        if event.kind != "prescription":
            continue
        chain = _build_chain_from_prescription(event, timeline[index + 1 :])
        if chain:
            suspected_chains.append(chain)

    return _response(
        _get_attribute(record, "patient_id", "unknown"),
        bool(suspected_chains),
        suspected_chains,
    )


def _build_chain_from_prescription(start_event: TimelineEvent, later_events: List[TimelineEvent]) -> Optional[List[Dict]]:
    chain: List[Dict] = []
    cursor = 0
    current_drug = start_event.label
    base_date = start_event.date

    while cursor < len(later_events):
        symptom_match = _find_next_symptom_for_drug(current_drug, later_events, cursor)
        if not symptom_match:
            break

        symptom_event, matched_effect, symptom_index = symptom_match
        next_prescription = _find_next_event(later_events, symptom_index + 1, "prescription")
        if not next_prescription:
            break

        next_diagnosis = _find_next_event(later_events, symptom_index + 1, "diagnosis")
        misdiagnosed_as = None
        if next_diagnosis and later_events.index(next_diagnosis) < later_events.index(next_prescription):
            misdiagnosed_as = next_diagnosis.label

        days_after = _days_between(base_date, symptom_event.date)
        confidence = _score_confidence(matched_effect, days_after, bool(misdiagnosed_as))

        link = {
            "from_drug": current_drug,
            "caused_symptom": symptom_event.label,
            "symptom_onset_date": symptom_event.date.isoformat() if symptom_event.date else "unknown",
            "days_after_prescription": days_after,
            "misdiagnosed_as": misdiagnosed_as,
            "resulting_drug": next_prescription.label,
            "evidence_source": matched_effect.get("source") if matched_effect else "internal",
            "confidence": confidence,
        }
        chain.append(link)

        cursor = later_events.index(next_prescription) + 1
        current_drug = next_prescription.label
        base_date = next_prescription.date

    return chain if chain else None


def _response(patient_id: str, has_cascade: bool, chains: List[List[Dict]]) -> Any:
    from app.schemas import CascadeAlertResponse, CascadeLink

    suggestions = []
    if has_cascade:
        for chain in chains:
            for link in chain:
                if link.get("resulting_drug"):
                    suggestions.append(f"Review whether {link['resulting_drug']} is still required.")

    recommendation = (
        "Suspected prescription cascade detected. Re-evaluate the earlier medication and"
        " consider deprescribing later medications if appropriate."
    )
    if not has_cascade:
        recommendation = "No prescription cascade detected."

    mapped_chains = [
        [CascadeLink(**link) for link in chain]
        for chain in chains
    ]

    return CascadeAlertResponse(
        patient_id=patient_id,
        has_cascade=has_cascade,
        suspected_chains=mapped_chains,
        recommendation=recommendation,
        deprescribing_suggestions=list(dict.fromkeys(suggestions)),
    )


def detect_cascade_dict(data: Dict[str, Any]) -> Any:
    from app.schemas import PatientRecordRequest

    rec = PatientRecordRequest(**data)
    return _detect_from_record(rec)
