from fastapi import APIRouter
from app.schemas import PatientRecordRequest
from app.services import storage
from app.services import db

db.init_db()

router = APIRouter(prefix="/api/ingest", tags=["Ingest"])


@router.post("/record")
async def ingest_record(record: PatientRecordRequest):
    """Ingest a patient record and persist it for later analysis."""
    # persist raw dict form
    payload = record.dict()
    storage.save_record(payload)
    try:
        db.save_record(payload)
    except Exception:
        # non-fatal: DB persistence can be retried later
        pass
    return {"status": "ok", "saved": True}
