"""
Fetch real drug label + adverse-reaction data from openFDA (free, no API key
required) and merge it into data/drug_knowledge.json in the exact shape
app/services/knowledge.py expects.

openFDA docs: https://open.fda.gov/apis/drug/label/
Rate limit without a key: 240 requests/minute, 1000/day.
(Optional) Get a free API key for higher limits: https://open.fda.gov/apis/authentication/

Usage:
    python fetch_openfda_drugs.py ibuprofen amlodipine metformin
    python fetch_openfda_drugs.py --file drug_names.txt
    python fetch_openfda_drugs.py ibuprofen --dry-run
    python fetch_openfda_drugs.py ibuprofen --api-key YOUR_KEY_HERE
"""
import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

OPENFDA_LABEL_URL = "https://api.fda.gov/drug/label.json"
DEFAULT_JSON_PATH = Path(__file__).resolve().parent / "data" / "drug_knowledge.json"

# openFDA doesn't give structured onset windows, so we assign a conservative
# default range per reaction. You should refine these manually for drugs
# that matter most to your cascade detection, using PubMed/clinical judgment.
DEFAULT_ONSET_MIN_DAYS = 1
DEFAULT_ONSET_MAX_DAYS = 60

# Common noisy/non-symptom terms openFDA reaction text sometimes includes;
# filtered out so they don't pollute your side-effect list.
REACTION_STOPWORDS = {
    "product", "quality", "issue", "device", "error", "condition", "disease",
    "off label use", "therapeutic", "response", "unevaluable event",
}


def fetch_label(drug_name: str, api_key: str = None) -> dict:
    """Query openFDA for a single drug's label, matching on generic or brand name."""
    query = f'openfda.generic_name:"{drug_name}" OR openfda.brand_name:"{drug_name}"'
    params = {"search": query, "limit": 1}
    if api_key:
        params["api_key"] = api_key

    url = f"{OPENFDA_LABEL_URL}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None  # no match found
        raise
    results = data.get("results", [])
    return results[0] if results else None


def extract_reactions(label: dict, max_reactions: int = 8) -> list:
    """Pulls adverse reaction terms out of the label's free-text
    'adverse_reactions' section using simple heuristics."""
    text_blocks = label.get("adverse_reactions", []) or []
    text = " ".join(text_blocks).lower()

    # Adverse reaction sections are often semicolon/comma separated lists
    # inside a longer paragraph. Split on common delimiters and filter.
    candidates = re.split(r"[;,.]", text)
    reactions = []
    seen = set()
    for c in candidates:
        term = c.strip()
        term = re.sub(r"^(including|such as|and|or)\s+", "", term)
        if not term or len(term) > 40 or len(term) < 3:
            continue
        if any(sw in term for sw in REACTION_STOPWORDS):
            continue
        if term in seen:
            continue
        seen.add(term)
        reactions.append(term)
        if len(reactions) >= max_reactions:
            break
    return reactions


def label_to_entry(drug_name: str, label: dict) -> dict:
    openfda = label.get("openfda", {})
    display_name = (openfda.get("brand_name") or openfda.get("generic_name") or [drug_name.capitalize()])[0]
    drug_class = (openfda.get("pharm_class_epc") or openfda.get("pharm_class_cs") or [None])[0]
    aliases = list(set(
        (openfda.get("generic_name") or []) + (openfda.get("brand_name") or [])
    ) - {display_name})

    indications = label.get("indications_and_usage", [""])[0]
    clinical_summary = indications[:400].strip() if indications else None

    reactions = extract_reactions(label)
    side_effects = [
        {
            "symptom_name": r,
            "typical_onset_days_min": DEFAULT_ONSET_MIN_DAYS,
            "typical_onset_days_max": DEFAULT_ONSET_MAX_DAYS,
            "source": "FDA Label (openFDA)",
            "frequency": None,  # openFDA labels don't give structured frequency
        }
        for r in reactions
    ]

    return {
        "display_name": display_name,
        "aliases": [a.lower() for a in aliases],
        "drug_class": drug_class,
        "used_for": None,
        "clinical_summary": clinical_summary,
        "side_effects": side_effects,
    }


def load_existing(json_path: Path) -> dict:
    if not json_path.exists():
        return {}
    with json_path.open("r", encoding="utf8") as f:
        return json.load(f)


def save_all(json_path: Path, data: dict) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Fetch drug data from openFDA into drug_knowledge.json")
    parser.add_argument("drug_names", nargs="*", help="Drug names to fetch (generic or brand)")
    parser.add_argument("--file", type=Path, help="Text file with one drug name per line")
    parser.add_argument("--json-path", type=Path, default=DEFAULT_JSON_PATH)
    parser.add_argument("--api-key", type=str, default=None, help="Optional openFDA API key for higher rate limits")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    names = list(args.drug_names)
    if args.file:
        names += [line.strip() for line in args.file.read_text().splitlines() if line.strip()]

    if not names:
        print("No drug names provided. Pass names as arguments or use --file.", file=sys.stderr)
        sys.exit(1)

    existing = load_existing(args.json_path)
    print(f"Existing knowledge base has {len(existing)} drug(s).\n")

    fetched, not_found = 0, []
    for name in names:
        key = name.strip().lower()
        print(f"Fetching '{name}' from openFDA...")
        try:
            label = fetch_label(key, api_key=args.api_key)
        except Exception as e:
            print(f"  [error] {e}", file=sys.stderr)
            not_found.append(name)
            continue

        if not label:
            print(f"  [not found] no openFDA label match for '{name}'")
            not_found.append(name)
            continue

        entry = label_to_entry(key, label)
        existing[key] = entry
        fetched += 1
        print(f"  [ok] {entry['display_name']} — {len(entry['side_effects'])} reaction(s) extracted")

        time.sleep(0.3)  # stay well under the 240/min rate limit

    print(f"\nFetched {fetched} drug(s). {len(not_found)} not found: {not_found}")

    if args.dry_run:
        print(f"[dry-run] Would write {len(existing)} total drug(s) to {args.json_path}. No file written.")
        return

    save_all(args.json_path, existing)
    print(f"Saved. {args.json_path} now has {len(existing)} drug(s).")
    print("\nNOTE: onset windows were set to a generic default (1-60 days) since")
    print("openFDA labels don't provide structured onset timing. Review and tighten")
    print("these manually for the drugs most important to your cascade detection.")


if __name__ == "__main__":
    main()
