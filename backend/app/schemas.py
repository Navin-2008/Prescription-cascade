from pydantic import BaseModel
from typing import List, Optional

class Prescription(BaseModel):
    drug_name: str
    start_date: str

class Symptom(BaseModel):
    symptom_name: str
    onset_date: str

class PatientRecordRequest(BaseModel):
    patient_id: str
    clinical_note: Optional[str] = None
    prescriptions: List[Prescription] = []
    symptoms: List[Symptom] = []

class CascadeAlertResponse(BaseModel):
    patient_id: str
    has_cascade: bool
    suspected_chain: List[str]
    recommendation: str