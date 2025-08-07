import os
import json
from typing import Optional, Dict, Any

import requests


def read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def get_google_api_key() -> str:
    key_path = "/workspace/google cloud map platform api key/key.txt"
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"Missing Google API key at {key_path}")
    return read_text_file(key_path)


def get_mapbox_token() -> str:
    key_path = "/workspace/mapbox token/token.txt"
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"Missing Mapbox token at {key_path}")
    return read_text_file(key_path)


def google_geocode_address(address: str, default_city_state: str = "New York, NY") -> Optional[Dict[str, Any]]:
    """
    Geocode using Google Geocoding API. If the address lacks city/state, append default.
    Returns the best result dict or None.
    """
    api_key = get_google_api_key()

    addr = address.strip()
    if "," not in addr and "NY" not in addr and "New York" not in addr:
        addr = f"{addr}, {default_city_state}"

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": addr, "key": api_key}
    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "OK" or not data.get("results"):
        return None
    return data["results"][0]


def save_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)