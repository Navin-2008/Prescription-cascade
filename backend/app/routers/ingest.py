from fastapi import APIRouter
from app.schemas import PatientRecordRequest, IngestResponse
from app.services import storage
from app.services import db

db.init_db()

router = APIRouter(prefix="/api/ingest", tags=["Ingest"])


@router.post("/record", response_model=IngestResponse)
async def ingest_record(record: PatientRecordRequest):
    """Ingest a patient record and persist it for later analysis."""
    payload = record.model_dump()
    storage.save_record(payload)
    db_saved = True
    try:
        db.save_record(payload)
    except Exception:
        # non-fatal: DB persistence can be retried later
        db_saved = False
    return {"status": "ok", "patient_id": record.patient_id, "saved": True, "db_saved": db_saved}
