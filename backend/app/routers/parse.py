from fastapi import APIRouter
from app.schemas import ParsedNoteRequest, ParsedNoteResponse
from app.services import nlp_parser

router = APIRouter(prefix="/api/parse", tags=["Parse"])


@router.post("/clinical-note", response_model=ParsedNoteResponse)
async def parse_clinical_note(request: ParsedNoteRequest):
    return ParsedNoteResponse(**nlp_parser.extract_entities_from_note(request.clinical_note))
