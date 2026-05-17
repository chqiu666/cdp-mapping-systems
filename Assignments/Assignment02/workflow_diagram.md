# Workflow Diagram: Photo Location Analysis + NYC Open Data Integration

## Process Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           INPUT DATA SOURCES                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │   Personal      │    │   NYC Property  │    │   NYC PLUTO     │            │
│  │   Photoset      │    │   Assessment    │    │   Land Use      │            │
│  │   (370+ files)  │    │   Data API      │    │   Data API      │            │
│  │   📷 EXIF GPS   │    │   💰 Values     │    │   🏢 Zoning     │            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
│           │                       │                       │                    │
└───────────┼───────────────────────┼───────────────────────┼────────────────────┘
            │                       │                       │
            ▼                       │                       │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        STEP 1: EXIF EXTRACTION                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   📷 extract_photo_locations.py                                                │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  • Read EXIF metadata from each photo                                  │   │
│   │  • Extract GPS coordinates (lat, lng)                                  │   │
│   │  • Extract timestamps                                                  │   │
│   │  • Convert DMS coordinates to decimal                                  │   │
│   │  • Filter out photos without GPS data                                  │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                            │
│                                    ▼                                            │
│   📊 RESULT: 8 photos with valid GPS coordinates                               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       STEP 2: SPATIAL CLUSTERING                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   🎯 cluster_nearby_photos()                                                   │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  • Group photos within ~100m of each other                             │   │
│   │  • Calculate photo frequency per location                              │   │
│   │  • Assign "interest level" based on frequency:                         │   │
│   │    - Low: 1 photo                                                      │   │
│   │    - Medium: 2 photos                                                  │   │
│   │    - High: 3+ photos                                                   │   │
│   │  • Create location cluster identifiers                                 │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                            │
│                                    ▼                                            │
│   📊 RESULT: 6 distinct location clusters                                      │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     STEP 3: GEOJSON GENERATION                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   📋 Output GeoJSON Files                                                      │
│   ┌────────────────────────────┐    ┌────────────────────────────┐            │
│   │  Individual Points         │    │  Aggregated Clusters       │            │
│   │  photo_locations_          │    │  photo_locations_          │            │
│   │  individual.geojson        │    │  aggregated.geojson        │            │
│   │                            │    │                            │            │
│   │  • Each photo as point     │    │  • Cluster centroids      │            │
│   │  • Original coordinates    │    │  • Photo count             │            │
│   │  • Timestamp metadata      │    │  • Interest level          │            │
│   └────────────────────────────┘    └────────────────────────────┘            │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
            │                       ┌─────────────────────────────────────┐
            │                       │         PARALLEL PROCESS            │
            ▼                       └─────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      STEP 4: NYC OPEN DATA INTEGRATION                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   🌐 create_mapbox_visualization.py                                            │
│                                                                                 │
│   ┌─────────────────────────────┐    ┌─────────────────────────────┐          │
│   │   Property Assessment API   │    │    PLUTO Land Use API       │          │
│   │                             │    │                             │          │
│   │  📍 For each photo cluster: │    │  📍 For each photo cluster: │          │
│   │   • Create 500m buffer      │    │   • Query polygon data      │          │
│   │   • Query property values   │    │   • Extract land use codes  │          │
│   │   • Get assessment data     │    │   • Get zoning districts    │          │
│   │   • Calculate averages      │    │   • Analyze built FAR       │          │
│   └─────────────────────────────┘    └─────────────────────────────┘          │
│              │                                   │                            │
│              └──────────────┬────────────────────┘                            │
│                             ▼                                                  │
│   📊 COMBINED DATASET: photo locations + property data + land use              │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      STEP 5: DATA STORAGE & PROCESSING                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   💾 visualization_data_summary.json (3.1MB)                                   │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  Combined dataset containing:                                           │   │
│   │  • Photo location points with interest levels                          │   │
│   │  • Property assessment data (land value, total assessment)             │   │
│   │  • PLUTO land use polygons and zoning information                      │   │
│   │  • Spatial relationships and buffer analyses                           │   │
│   │  • Metadata for visualization rendering                                │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    STEP 6: INTERACTIVE VISUALIZATION                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   🗺️  photo_property_visualization.html                                        │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  Mapbox GL JS Interactive Map:                                          │   │
│   │                                                                         │   │
│   │  🎨 Visual Layers:                                                      │   │
│   │   • Photo points (sized by interest, colored by count)                 │   │
│   │   • Property value choropleth (color gradient)                         │   │
│   │   • Land use zones (categorical colors)                                │   │
│   │   • Base map (streets, buildings, labels)                              │   │
│   │                                                                         │   │
│   │  🎛️  Interactive Controls:                                              │   │
│   │   • Layer toggle switches                                              │   │
│   │   • Zoom and pan navigation                                            │   │
│   │   • Click popups with detailed info                                    │   │
│   │   • Legend and data explanations                                       │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          FINAL OUTPUT                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   📊 Analysis Ready Dataset for:                                               │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  • Correlation analysis (photo frequency ↔ property values)            │   │
│   │  • Land use pattern recognition                                        │   │
│   │  • Personal interest mapping                                           │   │
│   │  • Urban perception vs. economic reality                               │   │
│   │  • Temporal pattern analysis (with photo timestamps)                   │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Summary

1. **Input**: 370+ personal photos → **Filter**: 8 photos with GPS data
2. **Cluster**: 8 photo locations → **Aggregate**: 6 distinct clusters  
3. **Enrich**: Query NYC APIs → **Combine**: Photo + Property + Land Use data
4. **Visualize**: Interactive Mapbox map → **Analyze**: Correlations and patterns

## Technical Stack

- **Backend**: Python 3.13 (PIL, exifread, geojson, requests)
- **APIs**: NYC Open Data SODA API (Property Assessment, PLUTO)
- **Frontend**: Mapbox GL JS with custom styling and interactions
- **Data Formats**: GeoJSON for spatial data, JSON for metadata
- **Workflow**: Command-line Python scripts → Web-based visualization

## Key Innovations

1. **Personal Data Mining**: Extracting narrative from existing photo metadata
2. **Spatial Intelligence**: Clustering algorithm for meaningful location aggregation  
3. **Multi-source Integration**: Combining personal and municipal data seamlessly
4. **Interactive Analysis**: Real-time exploration of correlations through web interface