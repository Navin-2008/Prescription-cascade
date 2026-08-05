import json
from pathlib import Path
from typing import Dict, List, Optional

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "drug_knowledge.json"
DATA_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_knowledge() -> Dict[str, Dict]:
    if not DATA_PATH.exists():
        return {}
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _save_knowledge(knowledge: Dict[str, Dict]) -> None:
    with DATA_PATH.open("w", encoding="utf-8") as handle:
        json.dump(knowledge, handle, indent=2, sort_keys=True)


def _normalize_key(name: str) -> str:
    return name.strip().lower()


def _find_drug_key(knowledge: Dict[str, Dict], drug_name: str) -> Optional[str]:
    normalized = _normalize_key(drug_name)
    if normalized in knowledge:
        return normalized
    for key, entry in knowledge.items():
        aliases = entry.get("aliases", [])
        if any(_normalize_key(alias) == normalized for alias in aliases):
            return key
    return None


def list_drugs() -> List[Dict]:
    knowledge = _load_knowledge()
    return [
        {
            "name": key,
            "display_name": entry.get("display_name", key),
            "drug_class": entry.get("drug_class"),
            "used_for": entry.get("used_for", []),
        }
        for key, entry in knowledge.items()
    ]


def get_drug_report(drug_name: str) -> Dict:
    knowledge = _load_knowledge()
    key = _find_drug_key(knowledge, drug_name)
    if key is None:
        raise KeyError(drug_name)
    return knowledge[key]


def get_side_effects(drug_name: str) -> List[Dict]:
    knowledge = _load_knowledge()
    key = _find_drug_key(knowledge, drug_name)
    if key is None:
        return []
    return knowledge[key].get("side_effects", [])


def add_or_update_drug(drug_name: str, report: Dict) -> Dict:
    knowledge = _load_knowledge()
    key = _normalize_key(drug_name)
    if key != _normalize_key(report.get("display_name", key)):
        report = {**report, "display_name": report.get("display_name", drug_name)}
    knowledge[key] = report
    _save_knowledge(knowledge)
    return knowledge[key]


def delete_drug(drug_name: str) -> None:
    knowledge = _load_knowledge()
    key = _find_drug_key(knowledge, drug_name)
    if key is None:
        raise KeyError(drug_name)
    del knowledge[key]
    _save_knowledge(knowledge)
