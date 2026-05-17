# Address-to-Place Spaghetti Map (NYC)

This project samples Google Street View images in NYC, OCRs text to extract addresses, geocodes them, and visualizes connections (arcs) between where text is seen and where it points to on a Mapbox+deck.gl map.

## Setup
- Place API keys in:
  - `google cloud map platform api key/key.txt`
  - `mapbox token/token.txt`
- Install system deps and Python packages:
  ```bash
  sudo apt-get update && sudo apt-get install -y tesseract-ocr libtesseract-dev
  pip install -r requirements.txt
  ```

## Run pipeline
```bash
python scripts/fetch_streetview.py --city NYC --count 40
python scripts/ocr_and_geocode.py
python scripts/generate_arcs.py
```

The output arcs JSON is written to `website/data/arcs.json`.

## Run website locally
```bash
cd website && python -m http.server 8000
```
Then open `http://localhost:8000`.
