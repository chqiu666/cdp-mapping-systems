import os
import re
import json
from typing import List, Dict, Optional, Tuple

import cv2
import pytesseract

from utils import google_geocode_address, load_json, save_json


IMAGES_DIR = "/workspace/data/streetview/images"
META_DIR = "/workspace/data/streetview/metadata"
OUTPUT_DIR = "/workspace/data/processed"


ADDRESS_SUFFIXES = [
    "St", "Street", "Ave", "Avenue", "Rd", "Road", "Blvd", "Boulevard",
    "Pl", "Place", "Ln", "Lane", "Dr", "Drive", "Ct", "Court",
]

SUFFIX_PATTERN = "|".join(ADDRESS_SUFFIXES)
# Patterns like: 123 Main St, 45-12 Broadway, 7th Ave, 200 W 34th St
ADDRESS_PATTERN = re.compile(
    rf"\b(\d+[\-\d]*\s+[A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*\s+(?:{SUFFIX_PATTERN}))\b",
    re.IGNORECASE,
)


def preprocess_image_for_ocr(image_path: str):
    image = cv2.imread(image_path)
    if image is None:
        return None
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    _, thr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thr


def extract_addresses_from_text(text: str) -> List[str]:
    candidates = set()
    for match in ADDRESS_PATTERN.finditer(text):
        addr = match.group(1)
        addr = re.sub(r"\s+", " ", addr).strip()
        candidates.add(addr)
    return list(candidates)


def ocr_image(image_path: str) -> str:
    pre = preprocess_image_for_ocr(image_path)
    if pre is None:
        return ""
    config = "--psm 6"
    text = pytesseract.image_to_string(pre, config=config)
    return text


def list_image_basenames() -> List[str]:
    files = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(".jpg")]
    bases = [os.path.splitext(f)[0] for f in files]
    bases.sort()
    return bases


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    results: List[Dict] = []

    for base in list_image_basenames():
        img_path = os.path.join(IMAGES_DIR, base + ".jpg")
        meta_path = os.path.join(META_DIR, base + ".json")
        if not os.path.exists(meta_path):
            continue
        meta = load_json(meta_path)
        pano_loc = meta.get("location", {})
        pano_lat = pano_loc.get("lat")
        pano_lng = pano_loc.get("lng")

        text = ocr_image(img_path)
        addresses = extract_addresses_from_text(text)

        geocoded: List[Dict] = []
        for addr in addresses:
            g = google_geocode_address(addr)
            if not g:
                continue
            loc = g.get("geometry", {}).get("location", {})
            geocoded.append({
                "address_text": addr,
                "formatted_address": g.get("formatted_address"),
                "lat": loc.get("lat"),
                "lng": loc.get("lng"),
                "source_image": base + ".jpg",
                "pano_lat": pano_lat,
                "pano_lng": pano_lng,
            })

        if geocoded:
            results.extend(geocoded)

    save_json(os.path.join(OUTPUT_DIR, "ocr_geocoded.json"), results)
    print(f"Saved {len(results)} OCR+geocode records to {OUTPUT_DIR}/ocr_geocoded.json")


if __name__ == "__main__":
    main()