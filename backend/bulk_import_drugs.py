"""
Bulk-import drugs into data/drug_knowledge.json from a CSV file.

CSV format (one row per SIDE EFFECT, drugs repeat across rows):

drug_name,display_name,aliases,drug_class,used_for,clinical_summary,symptom_name,onset_days_min,onset_days_max,source,frequency

Example rows for one drug with two side effects:

warfarin,Warfarin,coumadin,Anticoagulant,"Blood clot prevention","Narrow therapeutic index anticoagulant...",bruising,3,14,FAERS,common
warfarin,Warfarin,coumadin,Anticoagulant,"Blood clot prevention","Narrow therapeutic index anticoagulant...",bleeding gums,3,30,FAERS,common

Usage:
    python bulk_import_drugs.py path/to/drugs.csv
    python bulk_import_drugs.py path/to/drugs.csv --dry-run   # preview without writing
    python bulk_import_drugs.py path/to/drugs.csv --overwrite  # replace existing drugs instead of merging side effects
"""
import argparse
import csv
import json
import sys
from pathlib import Path

DEFAULT_JSON_PATH = Path(__file__).resolve().parent / "data" / "drug_knowledge.json"


def load_existing(json_path: Path) -> dict:
    if not json_path.exists():
        return {}
    with json_path.open("r", encoding="utf8") as f:
        return json.load(f)


def parse_csv(csv_path: Path) -> dict:
    """Groups CSV rows by drug_name, building the same shape as drug_knowledge.json entries."""
    drugs: dict = {}
    with csv_path.open("r", encoding="utf8", newline="") as f:
        reader = csv.DictReader(f)
        required = {"drug_name", "display_name", "symptom_name", "onset_days_min", "onset_days_max", "source"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV is missing required columns: {sorted(missing)}")

        for row_num, row in enumerate(reader, start=2):  # start=2 accounts for header row
            key = row["drug_name"].strip().lower()
            if not key:
                print(f"  [skip] row {row_num}: empty drug_name", file=sys.stderr)
                continue

            if key not in drugs:
                aliases_raw = row.get("aliases", "") or ""
                drugs[key] = {
                    "display_name": row.get("display_name", "").strip() or key.capitalize(),
                    "aliases": [a.strip() for a in aliases_raw.split(";") if a.strip()],
                    "drug_class": row.get("drug_class", "").strip() or None,
                    "used_for": row.get("used_for", "").strip() or None,
                    "clinical_summary": row.get("clinical_summary", "").strip() or None,
                    "side_effects": [],
                }

            symptom = row.get("symptom_name", "").strip()
            if not symptom:
                continue  # row only carried drug-level metadata, no side effect

            try:
                onset_min = int(row["onset_days_min"])
                onset_max = int(row["onset_days_max"])
            except (ValueError, KeyError):
                print(f"  [skip] row {row_num}: invalid onset_days for '{symptom}'", file=sys.stderr)
                continue

            drugs[key]["side_effects"].append({
                "symptom_name": symptom,
                "typical_onset_days_min": onset_min,
                "typical_onset_days_max": onset_max,
                "source": row.get("source", "").strip() or "internal",
                "frequency": row.get("frequency", "").strip() or None,
            })

    return drugs


def merge(existing: dict, incoming: dict, overwrite: bool) -> dict:
    result = dict(existing)
    for key, entry in incoming.items():
        if key not in result or overwrite:
            result[key] = entry
            action = "added" if key not in existing else "overwritten"
        else:
            # merge: keep existing metadata, append only new side effects (dedup by symptom_name)
            existing_symptoms = {se["symptom_name"].lower() for se in result[key].get("side_effects", [])}
            new_effects = [se for se in entry["side_effects"] if se["symptom_name"].lower() not in existing_symptoms]
            result[key]["side_effects"].extend(new_effects)
            action = f"merged (+{len(new_effects)} side effects)"
        print(f"  [{action}] {key}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Bulk import drugs into drug_knowledge.json")
    parser.add_argument("csv_path", type=Path, help="Path to the CSV file of drug data")
    parser.add_argument("--json-path", type=Path, default=DEFAULT_JSON_PATH, help="Path to drug_knowledge.json")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing drugs instead of merging side effects")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing to disk")
    args = parser.parse_args()

    if not args.csv_path.exists():
        print(f"CSV file not found: {args.csv_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Reading {args.csv_path} ...")
    incoming = parse_csv(args.csv_path)
    print(f"Parsed {len(incoming)} drug(s) from CSV.\n")

    existing = load_existing(args.json_path)
    print(f"Existing knowledge base has {len(existing)} drug(s). Merging...\n")

    merged = merge(existing, incoming, overwrite=args.overwrite)

    if args.dry_run:
        print(f"\n[dry-run] Would write {len(merged)} total drug(s) to {args.json_path}. No file written.")
        return

    args.json_path.parent.mkdir(parents=True, exist_ok=True)
    with args.json_path.open("w", encoding="utf8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    print(f"\nDone. {args.json_path} now has {len(merged)} drug(s).")


if __name__ == "__main__":
    main()
