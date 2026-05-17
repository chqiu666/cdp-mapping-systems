#!/usr/bin/env bash
set -euo pipefail

/workspace/.venv/bin/python /workspace/scripts/fetch_streetview.py --city NYC --count ${1:-20}
/workspace/.venv/bin/python /workspace/scripts/ocr_and_geocode.py
/workspace/.venv/bin/python /workspace/scripts/generate_arcs.py

echo "Pipeline complete. Open the website by running: cd /workspace/website && python -m http.server 8000"