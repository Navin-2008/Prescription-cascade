from fastapi import APIRouter
from app.schemas import CascadeAlertResponse, PatientRecordRequest
from app.services import graph_engine

router = APIRouter(prefix="/api/cascade", tags=["Prescription Cascade"])


@router.post("/analyze", response_model=CascadeAlertResponse)
async def analyze_patient_cascade(record: PatientRecordRequest):
    """Analyze a patient record and return cascade detection results."""
    result = graph_engine.detect_cascade(record)
    return result