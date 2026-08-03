from app.services import nlp_parser
from typing import List
from typing import Any, Dict


def _detect_from_record(record: Any) -> Any:
    # internal helper expects a typed pydantic model with attributes
    drug_names = [p.drug_name.lower() for p in record.prescriptions]

    # merge explicit symptoms with ones parsed from the clinical note
    parsed = nlp_parser.extract_symptoms_from_note(record.clinical_note or "")
    symptom_names = [s.symptom_name.lower() for s in record.symptoms] if record.symptoms else []
    symptom_names += [s["symptom_name"] for s in parsed]

    suspected_chain: List[str] = []
    if "amlodipine" in drug_names and any("swelling" in s for s in symptom_names):
        if "furosemide" in drug_names:
            suspected_chain = [
                "Amlodipine (Hypertension) -> Prescribed",
                "Ankle Swelling (Side Effect) -> Documented",
                "Furosemide (Diuretic) -> Prescribed"
            ]

    from app.schemas import CascadeAlertResponse

    if suspected_chain:
        return CascadeAlertResponse(
            patient_id=record.patient_id,
            has_cascade=True,
            suspected_chain=suspected_chain,
            recommendation=(
                "Suspected prescription cascade: consider deprescribing Furosemide and"
                " re-evaluating Amlodipine. Discuss with prescribing clinician."
            ),
        )

    return CascadeAlertResponse(
        patient_id=record.patient_id,
        has_cascade=False,
        suspected_chain=[],
        recommendation="No prescription cascade detected."
    )


def detect_cascade(record: Any) -> Any:
    """Public API: accept a typed `PatientRecordRequest` or dict-ish object.

    If a dict is provided, call `detect_cascade_dict` instead.
    """
    # if it's a mapping/dict-like, delegate to dict-based constructor
    if isinstance(record, dict):
        return detect_cascade_dict(record)

    return _detect_from_record(record)


def detect_cascade_dict(data: Dict[str, Any]) -> Any:
    """Construct pydantic model from dict and run the detector.

    Importing the pydantic model is done here to avoid module import cycles
    during application startup in small demos.
    """
    from app.schemas import PatientRecordRequest

    rec = PatientRecordRequest(**data)
    return _detect_from_record(rec)
