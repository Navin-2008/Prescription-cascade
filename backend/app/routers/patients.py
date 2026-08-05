from fastapi import APIRouter, HTTPException
from app.schemas import PatientRecordResponse, PatientTimelineResponse
from app.services import db

router = APIRouter(prefix="/api/patients", tags=["Patients"])


@router.get("/{patient_id}/record", response_model=PatientRecordResponse)
async def get_patient_record(patient_id: str):
    record = db.get_patient_record(patient_id)
    if not record:
        raise HTTPException(status_code=404, detail="Patient record not found")
    return record


@router.get("/{patient_id}/timeline", response_model=PatientTimelineResponse)
async def get_patient_timeline(patient_id: str):
    timeline = db.get_patient_timeline(patient_id)
    if not timeline:
        raise HTTPException(status_code=404, detail="Patient timeline not found")
    return timeline
