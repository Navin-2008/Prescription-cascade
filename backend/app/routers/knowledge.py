from typing import List
from fastapi import APIRouter, HTTPException
from app.schemas import DrugListItem, DrugReport, SideEffectEntry
from app.services import knowledge

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge"])


@router.get("/drugs", response_model=List[DrugListItem])
async def list_drugs():
    return knowledge.list_drugs()


@router.get("/drugs/{drug_name}", response_model=DrugReport)
async def get_drug_report(drug_name: str):
    try:
        return knowledge.get_drug_report(drug_name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Drug knowledge not found for {drug_name}")


@router.put("/drugs/{drug_name}", response_model=DrugReport)
async def add_or_update_drug(drug_name: str, report: DrugReport):
    return knowledge.add_or_update_drug(drug_name, report.model_dump())


@router.delete("/drugs/{drug_name}")
async def delete_drug(drug_name: str):
    try:
        knowledge.delete_drug(drug_name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Drug knowledge not found for {drug_name}")
    return {"status": "deleted", "drug": drug_name}


@router.get("/side-effects", response_model=List[SideEffectEntry])
async def get_side_effects(drug_name: str):
    effects = knowledge.get_side_effects(drug_name)
    if not effects:
        raise HTTPException(status_code=404, detail=f"No side-effect knowledge found for {drug_name}")
    return effects
