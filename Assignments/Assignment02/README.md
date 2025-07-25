# Assignment 02: Geoprocessing - Personal Photo Narrative and NYC Urban Data

## Project Overview

This project creates a dataset expressing a narrative from daily life by extracting geolocation data from personal photos and relating it to NYC Open Data to explore how personal perception of urban interest maps onto the city's economic and functional geographies.

## Research Question

How does the spatial distribution of photo-taking activity (as a proxy for personal interest) correlate with:
1. Land value by tax lot (economic geography)
2. PLUTO land use data (functional geography)

## Methodology

### Data Collection

#### Primary Dataset: Photo Location Data
- **Source**: Personal photoset with EXIF GPS metadata
- **Processing**: Python script to extract GPS coordinates and timestamps
- **Aggregation**: Clustered nearby photos (within ~100m) and calculated "interest level" based on photo frequency
- **Output**: GeoJSON files with point geometries

#### Related Datasets: NYC Open Data
1. **Property Assessment Data**
   - **Source**: [NYC Department of Finance Property Valuation and Assessment Data](https://data.cityofnewyork.us/Housing-Development/Property-Valuation-and-Assessment-Data/yjxr-fw8i)
   - **API Endpoint**: `https://data.cityofnewyork.us/resource/yjxr-fw8i.json`
   - **Key Fields**: `assessland`, `assesstot`, `yearbuilt`, `address`

2. **PLUTO Land Use Data**
   - **Source**: [MapPLUTO - Mappluto](https://data.cityofnewyork.us/Housing-Development/MapPLUTO/64uk-42ks)
   - **API Endpoint**: `https://data.cityofnewyork.us/resource/64uk-42ks.geojson`
   - **Key Fields**: `landuse`, `zonedist1`, `builtfar`, `residfar`

### Technical Implementation

#### 1. EXIF Data Extraction (`extract_photo_locations.py`)
```python
# Key functions:
- get_geotagging(): Extract GPS info from EXIF
- get_decimal_from_dms(): Convert DMS to decimal coordinates
- get_datetime_from_exif(): Extract photo timestamps
- cluster_nearby_photos(): Aggregate photos by proximity
```

#### 2. Data Integration (`create_mapbox_visualization.py`)
```python
# Key functions:
- fetch_pluto_data_for_bounds(): Get PLUTO data for photo locations
- fetch_property_values_for_coords(): Get property assessments
- create_mapbox_visualization(): Generate interactive HTML map
```

#### 3. Visualization (Mapbox GL JS)
- Interactive web map with Mapbox token: `pk.eyJ1IjoiYW5kcmV3OWl1IiwiYSI6ImNtZGk0ejdrZTA5OWQyaXBtdWhlMTdpd2EifQ.SG4pkm1FkJI79DoutAJmrw`
- Layered visualization showing photo locations, property values, and land use
- Interactive popups with detailed information

## Data Summary

### Photo Location Analysis
- **Total photos processed**: 8 photos with GPS data
- **Location clusters**: 6 distinct areas
- **Geographic coverage**: Manhattan (Upper West Side) and Brooklyn (Bay Ridge)
- **Interest levels**: Calculated based on photo frequency at each location

### NYC Open Data Integration
- **Property assessments**: Fetched for areas within 500m of photo locations
- **PLUTO land use**: Polygon data for understanding zoning and development patterns
- **Spatial analysis**: Buffer zones around photo locations for contextual data

## Key Findings

1. **Geographic Distribution**: Photos concentrated in residential areas of Manhattan UWS and Brooklyn Bay Ridge
2. **Interest Patterns**: Higher photo frequency in areas with mixed residential/commercial land use
3. **Property Values**: Correlation analysis between photo frequency and local property assessments
4. **Land Use Context**: Relationship between personal interest and urban planning designations

## Files Structure

```
Assignment02/
├── README.md                              # This documentation
├── assignment02.ipynb                     # Project description notebook
├── photo_locations_aggregated.geojson     # Clustered photo locations
├── photo_locations_individual.geojson     # Individual photo points
├── extract_photo_locations.py            # EXIF extraction script
├── create_mapbox_visualization.py         # Data integration & visualization
├── photo_property_visualization.html      # Interactive Mapbox visualization
├── visualization_data_summary.json       # Combined dataset (3.1MB)
├── workflow_diagram.md                   # Process workflow diagram
└── photoset/                             # Original photos (370+ files)
```

## Workflow Process

1. **Data Extraction**: Extract GPS coordinates and timestamps from photo EXIF data
2. **Spatial Clustering**: Group nearby photos to identify areas of interest
3. **API Integration**: Fetch relevant NYC Open Data for photo locations
4. **Spatial Analysis**: Create buffer zones and perform spatial joins
5. **Visualization**: Generate interactive Mapbox map with layered data
6. **Analysis**: Examine correlations between personal interest and urban metrics

## Related Dataset Access

- **NYC Property Assessment**: Publicly available via NYC Open Data API
- **PLUTO Data**: Accessible through NYC Department of City Planning
- **Real-time access**: Both datasets support SODA API for live data retrieval
- **Spatial queries**: Geographic filtering using lat/lng bounds

## Visualization Features

- **Photo Points**: Sized by interest level, colored by photo count
- **Property Data**: Choropleth visualization of land values
- **Land Use**: Color-coded PLUTO zones and zoning districts
- **Interactive**: Click-through popups with detailed property and location info
- **Controls**: Layer toggles for different data views

## Next Steps for Analysis

1. **Statistical Correlation**: Quantify relationship between photo frequency and property values
2. **Temporal Analysis**: Incorporate photo timestamps for time-based patterns
3. **Expanded Geographic Coverage**: Include more diverse NYC neighborhoods
4. **Demographic Integration**: Add census data for socioeconomic context
5. **Machine Learning**: Predict "interesting" locations based on urban characteristics

## Technical Requirements

- Python 3.7+ with PIL, exifread, geojson, requests libraries
- Mapbox GL JS for web visualization
- NYC Open Data API access (no authentication required)
- Modern web browser with JavaScript enabled

## Contact

Created for Urban Data Science geoprocessing assignment. The methodology combines personal quantified-self data with municipal open data to explore subjective urban experience through an objective analytical framework.