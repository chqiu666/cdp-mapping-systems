import os
from typing import List, Dict

from utils import load_json, save_json

INPUT_JSON = "/workspace/data/processed/ocr_geocoded.json"
OUTPUT_JSON = "/workspace/website/data/arcs.json"


def main() -> None:
    if not os.path.exists(INPUT_JSON):
        raise FileNotFoundError(f"Missing input {INPUT_JSON}. Run ocr_and_geocode.py first.")

    records: List[Dict] = load_json(INPUT_JSON)

    arcs: List[Dict] = []
    for r in records:
        if r.get("lat") is None or r.get("lng") is None:
            continue
        if r.get("pano_lat") is None or r.get("pano_lng") is None:
            continue
        arcs.append({
            "sourcePosition": [r["pano_lng"], r["pano_lat"]],
            "targetPosition": [r["lng"], r["lat"]],
            "addressText": r.get("address_text"),
            "formattedAddress": r.get("formatted_address"),
            "image": r.get("source_image"),
        })

    save_json(OUTPUT_JSON, arcs)
    print(f"Wrote {len(arcs)} arcs to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()