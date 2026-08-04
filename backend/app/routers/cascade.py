from fastapi import APIRouter
from app.schemas import CascadeAlertResponse
from app.services import graph_engine

router = APIRouter(prefix="/api/cascade", tags=["Prescription Cascade"])


@router.post("/analyze", response_model=CascadeAlertResponse)
async def analyze_patient_cascade(data: dict):
    """Analyze a patient record and return cascade detection results.

    Accepts a JSON payload matching `PatientRecordRequest`. We construct the
    typed model inside the graph engine to avoid circular imports during
    module import time.
    """
    result = graph_engine.detect_cascade_dict(data)
    return result