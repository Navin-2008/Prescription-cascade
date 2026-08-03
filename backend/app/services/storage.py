from pathlib import Path
import json
from typing import Dict

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def save_record(record: Dict) -> None:
    """Append a record as JSON line to `data/records.jsonl`."""
    out = DATA_DIR / "records.jsonl"
    with out.open("a", encoding="utf8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
