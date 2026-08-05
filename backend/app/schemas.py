from pydantic import BaseModel, Field
from typing import List, Optional

class Prescription(BaseModel):
    drug_name: str
    start_date: str

class Symptom(BaseModel):
    symptom_name: str
    onset_date: str

class Diagnosis(BaseModel):
    icd_code: Optional[str] = None
    description: str
    diagnosed_date: str
    diagnosing_physician: Optional[str] = None

class PatientRecordRequest(BaseModel):
    patient_id: str
    clinical_note: Optional[str] = None
    prescriptions: List[Prescription] = Field(default_factory=list)
    symptoms: List[Symptom] = Field(default_factory=list)
    diagnoses: List[Diagnosis] = Field(default_factory=list)

class IngestResponse(BaseModel):
    status: str
    patient_id: str
    saved: bool
    db_saved: bool = True

class ParsedNoteRequest(BaseModel):
    clinical_note: str

class ParsedNoteResponse(BaseModel):
    extracted_symptoms: List[Symptom]
    extracted_prescriptions: List[Prescription]
    confidence: float

class SideEffectEntry(BaseModel):
    symptom_name: str
    typical_onset_days_min: int
    typical_onset_days_max: int
    source: str
    frequency: Optional[str] = None

class DrugReport(BaseModel):
    display_name: str
    aliases: List[str] = Field(default_factory=list)
    drug_class: Optional[str] = None
    used_for: List[str] = Field(default_factory=list)
    clinical_summary: Optional[str] = None
    side_effects: List[SideEffectEntry] = Field(default_factory=list)

class DrugListItem(BaseModel):
    name: str
    display_name: str
    drug_class: Optional[str] = None
    used_for: List[str] = Field(default_factory=list)

class CascadeLink(BaseModel):
    from_drug: str
    caused_symptom: str
    symptom_onset_date: str
    days_after_prescription: int
    misdiagnosed_as: Optional[str] = None
    resulting_drug: Optional[str] = None
    evidence_source: Optional[str] = None
    confidence: float

class CascadeAlertResponse(BaseModel):
    patient_id: str
    has_cascade: bool
    suspected_chains: List[List[CascadeLink]]
    recommendation: str
    deprescribing_suggestions: List[str] = Field(default_factory=list)

class PatientTimelineEvent(BaseModel):
    event_type: str
    label: str
    date: Optional[str] = None
    source: Optional[str] = None
    details: Optional[dict] = None

class PatientTimelineResponse(BaseModel):
    patient_id: str
    timeline: List[PatientTimelineEvent]

class PatientRecordResponse(BaseModel):
    patient_id: str
    clinical_note: Optional[str] = None
    prescriptions: List[Prescription] = Field(default_factory=list)
    symptoms: List[Symptom] = Field(default_factory=list)
    diagnoses: List[Diagnosis] = Field(default_factory=list)