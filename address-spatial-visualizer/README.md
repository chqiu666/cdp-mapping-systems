# Address Spatial Visualizer

A web application that visualizes how abstract address text connects to spatial locations using Google Street View data and interactive mapping.

## Overview

This project creates a "spaghetti map" visualization that shows the connections between:
- Address text extracted from street view images via OCR
- The actual spatial coordinates those addresses refer to
- Arc-style connections visualized using deck.gl overlay on Mapbox

## Features

- **Street View Sampling**: Automated collection of NYC street view images using Google Street View Static API
- **OCR Text Extraction**: Extract text from street view images to identify address information
- **Address Geocoding**: Parse and geocode addresses to get precise coordinates
- **Interactive Visualization**: deck.gl arc layer overlay on Mapbox showing spatial connections

## API References

- [Google Maps 3D Camera Movement](https://developers.google.com/maps/documentation/javascript/examples/3d/move-camera)
- [Google Street View Static API](https://developers.google.com/maps/documentation/streetview/request-streetview)
- [Street View Metadata API](https://developers.google.com/maps/documentation/streetview/metadata)
- [Google Maps Geocoding API](https://developers.google.com/maps/documentation/javascript/geocoding)

## Quick Start

### Option 1: Demo with Sample Data
```bash
# Generate sample data and start the application
cd frontend && npm install && npm start
```

### Option 2: Real Data Collection
```bash
# 1. Install Python dependencies
cd scripts && pip install -r requirements.txt

# 2. Collect street view data (requires Google Maps API)
python3 collect_streetview_data.py 25  # collect 25 images

# 3. Process images with OCR (requires tesseract)
python3 process_images_ocr.py

# 4. Parse addresses and geocode
python3 parse_addresses.py

# 5. Start the web application
cd ../frontend && npm install && npm start
```

## Prerequisites

### For Demo (Sample Data)
- Node.js and npm
- Web browser

### For Real Data Collection
- Python 3.7+
- Node.js and npm
- Google Cloud Maps Platform API key with:
  - Street View Static API
  - Street View Metadata API
  - Geocoding API
- Tesseract OCR engine (`sudo apt-get install tesseract-ocr` on Ubuntu)

## Configuration

The API keys are already configured in the `.env` file:
- Google Maps API Key: `AIzaSyBMeNzarZclFzSf_1S0g2veaLxpMPhKDL8`
- Mapbox Token: `pk.eyJ1IjoiYW5kcmV3OWl1IiwiYSI6ImNtZGk0ejdrZTA5OWQyaXBtdWhlMTdpd2EifQ.SG4pkm1FkJI79DoutAJmrw`

## Project Structure

```
├── data/           # Collected street view images and processed data
├── scripts/        # Python scripts for data collection and processing
├── frontend/       # Web application code
└── .env           # API keys and configuration
```