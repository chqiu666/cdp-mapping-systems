import os
import csv
import time
import json
import math
import random
from typing import Dict, Tuple, Optional

import requests
from dotenv import load_dotenv

# Configuration
SAMPLES_TARGET = 100
OUTPUT_DIR_IMAGES = os.path.join(os.getcwd(), "images")
OUTPUT_DIR_METADATA = os.path.join(os.getcwd(), "metadata")
OUTPUT_CSV_PATH = os.path.join(os.getcwd(), "streetview_samples.csv")

# NYC bounding box
NYC_LAT_MIN, NYC_LAT_MAX = 40.4774, 40.9176
NYC_LNG_MIN, NYC_LNG_MAX = -74.2591, -73.7004

# API endpoints
STREETVIEW_METADATA_URL = "https://maps.googleapis.com/maps/api/streetview/metadata"
STREETVIEW_IMAGE_URL = "https://maps.googleapis.com/maps/api/streetview"

# Request settings
REQUESTS_PER_SECOND = 5  # be gentle
SLEEP_BETWEEN_REQUESTS = 1.0 / REQUESTS_PER_SECOND
METADATA_RADIUS_METERS = 75  # help find a pano near random point
IMAGE_SIZE = "640x640"

random.seed(42)


def ensure_dirs() -> None:
    os.makedirs(OUTPUT_DIR_IMAGES, exist_ok=True)
    os.makedirs(OUTPUT_DIR_METADATA, exist_ok=True)


def load_api_key() -> str:
    load_dotenv()
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_MAPS_API_KEY not set in environment or .env")
    return api_key


def random_point_in_nyc() -> Tuple[float, float]:
    lat = random.uniform(NYC_LAT_MIN, NYC_LAT_MAX)
    lng = random.uniform(NYC_LNG_MIN, NYC_LNG_MAX)
    return lat, lng


def fetch_streetview_metadata(api_key: str, lat: float, lng: float) -> Optional[Dict]:
    params = {
        "location": f"{lat:.6f},{lng:.6f}",
        "source": "outdoor",
        "key": api_key,
        "radius": METADATA_RADIUS_METERS,
    }
    try:
        resp = requests.get(STREETVIEW_METADATA_URL, params=params, timeout=15)
        if resp.status_code != 200:
            return None
        data = resp.json()
        return data
    except Exception:
        return None


def download_streetview_image_by_pano(api_key: str, pano_id: str, out_path: str) -> bool:
    params = {
        # Do not specify heading; default orientation
        # Keep pitch default 0 by omitting it
        "pano": pano_id,
        "size": IMAGE_SIZE,
        "source": "outdoor",
        "key": api_key,
    }
    try:
        resp = requests.get(STREETVIEW_IMAGE_URL, params=params, timeout=30)
        if resp.status_code != 200:
            return False
        with open(out_path, "wb") as f:
            f.write(resp.content)
        return True
    except Exception:
        return False


def main() -> None:
    ensure_dirs()
    api_key = load_api_key()

    collected_rows = []
    seen_pano_ids = set()

    attempts = 0
    max_attempts = 2000  # upper bound to avoid infinite loop if quota or coverage issues

    print(f"Starting collection: target={SAMPLES_TARGET} images")

    while len(collected_rows) < SAMPLES_TARGET and attempts < max_attempts:
        attempts += 1
        lat, lng = random_point_in_nyc()
        meta = fetch_streetview_metadata(api_key, lat, lng)
        time.sleep(SLEEP_BETWEEN_REQUESTS)

        if not meta:
            continue

        status = meta.get("status")
        if status != "OK":
            continue

        pano_id = meta.get("pano_id")
        if not pano_id or pano_id in seen_pano_ids:
            continue

        location = meta.get("location", {})
        pano_lat = location.get("lat")
        pano_lng = location.get("lng")
        date = meta.get("date")

        idx = len(collected_rows) + 1
        image_filename = f"nyc_streetview_{idx:03d}.jpg"
        image_path = os.path.join(OUTPUT_DIR_IMAGES, image_filename)

        ok = download_streetview_image_by_pano(api_key, pano_id, image_path)
        time.sleep(SLEEP_BETWEEN_REQUESTS)

        if not ok:
            # if image failed to download, skip this pano id and continue
            continue

        # Save raw metadata JSON for traceability
        meta_path = os.path.join(OUTPUT_DIR_METADATA, f"nyc_streetview_{idx:03d}_meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        collected_rows.append({
            "index": idx,
            "image_filename": image_filename,
            "pano_id": pano_id,
            "lat": pano_lat,
            "lng": pano_lng,
            "date": date,
            "status": status,
        })
        seen_pano_ids.add(pano_id)

        if idx % 10 == 0:
            print(f"Collected {idx}/{SAMPLES_TARGET} images...")

    # Write CSV
    with open(OUTPUT_CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[
            "index", "image_filename", "pano_id", "lat", "lng", "date", "status"
        ])
        writer.writeheader()
        for row in collected_rows:
            writer.writerow(row)

    print(f"Done. Collected {len(collected_rows)} images. CSV: {OUTPUT_CSV_PATH}")


if __name__ == "__main__":
    main()