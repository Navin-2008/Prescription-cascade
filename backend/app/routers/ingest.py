from fastapi import APIRouter
from app.schemas import PatientRecordRequest
from app.services import storage

router = APIRouter(prefix="/api/ingest", tags=["Ingest"])


@router.post("/record")
async def ingest_record(record: PatientRecordRequest):
    """Ingest a patient record and persist it for later analysis."""
    # persist raw dict form
    storage.save_record(record.dict())
    return {"status": "ok", "saved": True}
