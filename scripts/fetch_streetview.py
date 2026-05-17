import argparse
import os
import math
import time
import random
from typing import List, Tuple, Optional

import requests

from utils import get_google_api_key, save_json


NYC_BBOX = {
    "min_lng": -74.25909,
    "min_lat": 40.477399,
    "max_lng": -73.700272,
    "max_lat": 40.916178,
}


def generate_random_points_in_bbox(count: int) -> List[Tuple[float, float]]:
    pts: List[Tuple[float, float]] = []
    for _ in range(count * 3):
        lat = random.uniform(NYC_BBOX["min_lat"], NYC_BBOX["max_lat"])
        lng = random.uniform(NYC_BBOX["min_lng"], NYC_BBOX["max_lng"])
        pts.append((lat, lng))
    random.shuffle(pts)
    return pts


def fetch_metadata(lat: float, lng: float, api_key: str) -> Optional[dict]:
    url = "https://maps.googleapis.com/maps/api/streetview/metadata"
    for radius in (50, 100, 200, 300):
        params = {
            "location": f"{lat},{lng}",
            "source": "outdoor",
            "key": api_key,
            "radius": radius,
        }
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        meta = r.json()
        if meta.get("status") == "OK":
            return meta
    return None


def download_image(pano_id: Optional[str], lat: Optional[float], lng: Optional[float], out_path: str, api_key: str, size: str = "640x640") -> None:
    url = "https://maps.googleapis.com/maps/api/streetview"
    params = {
        "size": size,
        # Do not specify heading; keep default pitch 0; source outdoor
        "source": "outdoor",
        "pitch": 0,
        "key": api_key,
    }
    if pano_id:
        params["pano"] = pano_id
    elif lat is not None and lng is not None:
        params["location"] = f"{lat},{lng}"
    else:
        raise ValueError("Either pano_id or lat/lng must be provided")

    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(r.content)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", default="NYC")
    parser.add_argument("--count", type=int, default=40, help="Target number of images to download")
    parser.add_argument("--delay", type=float, default=0.2, help="Delay between requests to be gentle on API")
    args = parser.parse_args()

    api_key = get_google_api_key()

    target_count = args.count
    points = generate_random_points_in_bbox(target_count)

    saved = 0
    for idx, (lat, lng) in enumerate(points):
        if saved >= target_count:
            break

        meta = fetch_metadata(lat, lng, api_key)
        if not meta:
            continue

        pano_id = meta.get("pano_id")
        actual_location = meta.get("location", {})
        actual_lat = actual_location.get("lat")
        actual_lng = actual_location.get("lng")

        base_name = f"nyc_{saved:04d}"
        img_path = f"/workspace/data/streetview/images/{base_name}.jpg"
        meta_path = f"/workspace/data/streetview/metadata/{base_name}.json"

        # Save metadata first
        save_json(meta_path, meta)

        try:
            download_image(pano_id=pano_id, lat=actual_lat, lng=actual_lng, out_path=img_path, api_key=api_key)
            saved += 1
            time.sleep(args.delay)
        except Exception:
            try:
                os.remove(meta_path)
            except Exception:
                pass

    print(f"Saved {saved} images and metadata to /workspace/data/streetview")


if __name__ == "__main__":
    main()