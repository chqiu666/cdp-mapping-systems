# Address Spatial Visualizer - Usage Guide

## Overview

This project visualizes the connection between abstract address text and spatial locations using a "spaghetti map" style with deck.gl arc layers over Mapbox. It demonstrates how text extracted from street view images via OCR connects to their actual geographic coordinates.

## Getting Started

### Quick Demo

Run the demo with sample data:
```bash
./start_demo.sh
```

This will:
1. Generate sample NYC address connections
2. Install frontend dependencies
3. Start the web application at http://localhost:3000

### Full Data Pipeline

For real street view data collection and processing:

#### 1. Environment Setup
```bash
# Install Python dependencies
cd scripts
pip install -r requirements.txt

# Install Tesseract OCR (Ubuntu/Debian)
sudo apt-get install tesseract-ocr

# Or on macOS with Homebrew
brew install tesseract
```

#### 2. Data Collection
```bash
# Collect street view images from NYC
python3 collect_streetview_data.py [number_of_images]

# Example: collect 50 images
python3 collect_streetview_data.py 50
```

This script:
- Randomly samples coordinates within NYC bounds
- Checks street view availability using Metadata API
- Downloads 640x640 street view images
- Saves metadata including GPS coordinates
- Uses outdoor source with default pitch (0°)

#### 3. OCR Processing
```bash
# Extract text from street view images
python3 process_images_ocr.py
```

This script:
- Preprocesses images for better OCR accuracy
- Uses Tesseract to extract text with confidence scores
- Filters for potential address patterns
- Saves OCR results with bounding boxes

#### 4. Address Parsing & Geocoding
```bash
# Parse addresses and geocode to coordinates
python3 parse_addresses.py
```

This script:
- Cleans and normalizes extracted text
- Parses address components using usaddress library
- Geocodes addresses using Google Maps API
- Creates connection data linking text to coordinates
- Calculates distances between source and target locations

#### 5. Web Visualization
```bash
# Start the web application
cd ../frontend
npm install
npm start
```

## Web Application Features

### Interactive Map
- **Dark theme** Mapbox base map optimized for data visualization
- **3D perspective** with adjustable pitch and bearing
- **Responsive design** works on desktop and mobile

### Visualization Layers

#### Arc Layer
- **Gradient arcs** connecting street view locations to geocoded addresses
- **Variable width** based on distance between points
- **Color coding**: Teal (source) to Red (target)
- **Interactive tooltips** showing address text and distance

#### Scatter Plot Layers
- **Source points** (teal): Original street view capture locations
- **Target points** (red): Geocoded address coordinates
- **Size differentiation** for visual hierarchy

### UI Components

#### Header
- Project title with gradient text effect
- Descriptive subtitle explaining the visualization

#### Statistics Panel
- Total number of connections
- Unique street view images processed
- Average and maximum distances

#### Legend
- Color coding explanation
- Layer type identification

### Interaction Features
- **Pan and zoom** to explore different areas
- **Hover tooltips** with detailed information
- **3D rotation** for different viewing angles
- **Auto-fit** to data bounds on load

## Data Format

### Connection Data Structure
```json
{
  "image_id": "streetview_001_1234567890",
  "source": {
    "latitude": 40.7580,
    "longitude": -73.9855,
    "type": "streetview_location"
  },
  "target": {
    "latitude": 40.7589,
    "longitude": -73.9851,
    "type": "geocoded_address"
  },
  "connection": {
    "address_text": "Times Square, New York, NY",
    "confidence": "high",
    "distance_km": 0.12
  }
}
```

## Configuration

### API Keys
The project uses two main APIs:

1. **Google Cloud Maps Platform**
   - Street View Static API
   - Street View Metadata API  
   - Geocoding API
   - Key: `AIzaSyBMeNzarZclFzSf_1S0g2veaLxpMPhKDL8`

2. **Mapbox**
   - Maps API for base map tiles
   - Token: `pk.eyJ1IjoiYW5kcmV3OWl1IiwiYSI6ImNtZGk0ejdrZTA5OWQyaXBtdWhlMTdpd2EifQ.SG4pkm1FkJI79DoutAJmrw`

### OCR Configuration
- **Engine**: Tesseract OCR
- **Mode**: PSM 6 (uniform text block)
- **Confidence threshold**: 30+ for text extraction
- **Image preprocessing**: Grayscale, blur, threshold, morphological operations

### Geocoding Settings
- **Region bias**: New York, NY
- **Bounds**: NYC metropolitan area
- **Address cleaning**: Normalize abbreviations, remove artifacts

## Troubleshooting

### Common Issues

#### No data displayed
- Ensure `data/connections/all_connections.json` exists
- Run sample data creation: `python3 scripts/create_sample_data.py`

#### API quota exceeded
- Check Google Cloud Console for API usage
- Consider reducing sample size for testing

#### OCR not working
- Install Tesseract: `sudo apt-get install tesseract-ocr`
- Verify installation: `tesseract --version`

#### Frontend build errors
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node.js version compatibility

### Performance Optimization

#### Large datasets
- Limit initial data collection (25-50 images)
- Use data filtering in frontend
- Consider clustering for dense areas

#### Memory usage
- Reduce image resolution if needed
- Batch process OCR operations
- Clean up temporary files

## Development

### Project Structure
```
address-spatial-visualizer/
├── data/                    # Generated data files
│   ├── streetview_images/   # Downloaded images
│   ├── metadata/           # Image metadata
│   ├── ocr_results/        # OCR processing results
│   ├── parsed_addresses/   # Address parsing results
│   └── connections/        # Final connection data
├── scripts/                # Data processing scripts
│   ├── collect_streetview_data.py
│   ├── process_images_ocr.py
│   ├── parse_addresses.py
│   └── create_sample_data.py
├── frontend/               # React web application
│   ├── src/
│   │   ├── App.js         # Main application component
│   │   ├── styles.css     # Application styles
│   │   └── index.js       # Entry point
│   └── package.json       # Dependencies
└── .env                   # API keys
```

### Key Dependencies

#### Python
- `googlemaps`: Google Maps API client
- `pytesseract`: OCR processing
- `opencv-python`: Image preprocessing
- `usaddress`: Address parsing
- `requests`: HTTP client

#### JavaScript
- `@deck.gl/core`: 3D visualization framework
- `@deck.gl/layers`: Visualization layers
- `@deck.gl/mapbox`: Mapbox integration
- `react-map-gl`: React Mapbox wrapper
- `mapbox-gl`: Mapbox GL JS

## Contributing

### Adding New Features
1. **Data sources**: Extend beyond street view to other text sources
2. **Visualization**: Add new layer types or interaction modes
3. **Analysis**: Implement spatial analysis algorithms
4. **Performance**: Optimize for larger datasets

### Code Style
- Python: Follow PEP 8
- JavaScript: Use ES6+ features
- Comments: Document complex algorithms
- Error handling: Graceful degradation

This visualization demonstrates the fascinating relationship between textual representations of space and their actual geographic coordinates, revealing patterns in how we abstract and reference physical locations.