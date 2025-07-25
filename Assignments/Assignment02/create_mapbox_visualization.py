#!/usr/bin/env python3
"""
Create Mapbox visualization combining photo location data with NYC Open Data
"""

import json
import requests
import geojson
from datetime import datetime

# Mapbox token provided by user
MAPBOX_TOKEN = 'pk.eyJ1IjoiYW5kcmV3OWl1IiwiYSI6ImNtZGk0ejdrZTA5OWQyaXBtdWhlMTdpd2EifQ.SG4pkm1FkJI79DoutAJmrw'

# NYC Open Data endpoints
PLUTO_API_URL = "https://data.cityofnewyork.us/resource/64uk-42ks.geojson"
PROPERTY_VALUES_API_URL = "https://data.cityofnewyork.us/resource/yjxr-fw8i.json"

def fetch_pluto_data_for_bounds(min_lat, max_lat, min_lon, max_lon, limit=1000):
    """
    Fetch PLUTO data for specific geographic bounds
    """
    print(f"Fetching PLUTO data for bounds: {min_lat},{min_lon} to {max_lat},{max_lon}")
    
    # Create a bounding box query
    where_clause = f"latitude > {min_lat} AND latitude < {max_lat} AND longitude > {min_lon} AND longitude < {max_lon}"
    
    params = {
        '$where': where_clause,
        '$limit': limit,
        '$order': 'bbl'
    }
    
    try:
        response = requests.get(PLUTO_API_URL, params=params, timeout=30)
        response.raise_for_status()
        
        if response.content:
            data = response.json()
            print(f"Fetched {len(data.get('features', []))} PLUTO records")
            return data
        else:
            print("No PLUTO data returned")
            return {"type": "FeatureCollection", "features": []}
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching PLUTO data: {e}")
        return {"type": "FeatureCollection", "features": []}

def fetch_property_values_for_bbls(bbls):
    """
    Fetch property assessment values for specific BBLs
    """
    if not bbls:
        return []
        
    print(f"Fetching property values for {len(bbls)} BBLs")
    
    # Create IN clause for BBLs (limit to 50 at a time due to URL length limits)
    bbl_chunks = [bbls[i:i+50] for i in range(0, len(bbls), 50)]
    all_property_data = []
    
    for chunk in bbl_chunks:
        bbl_list = "','".join(chunk)
        where_clause = f"bbl IN ('{bbl_list}')"
        
        params = {
            '$where': where_clause,
            '$limit': len(chunk),
            '$select': 'bbl,fullval,avland,avtot,exland,extot,ltfront,ltdepth,buildingclasscategory'
        }
        
        try:
            response = requests.get(PROPERTY_VALUES_API_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            all_property_data.extend(data)
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching property values for chunk: {e}")
            continue
    
    print(f"Fetched property values for {len(all_property_data)} properties")
    return all_property_data

def get_bounds_from_photos(photo_geojson_file):
    """
    Get geographic bounds from photo locations to focus data fetching
    """
    try:
        with open(photo_geojson_file, 'r') as f:
            photo_data = geojson.load(f)
        
        if not photo_data.get('features'):
            return None
            
        lons = []
        lats = []
        
        for feature in photo_data['features']:
            if feature.get('geometry', {}).get('type') == 'Point':
                coords = feature['geometry']['coordinates']
                lons.append(coords[0])
                lats.append(coords[1])
        
        if not lons or not lats:
            return None
            
        # Add buffer around the bounds (0.01 degrees ≈ 1km)
        buffer = 0.01
        bounds = {
            'min_lat': min(lats) - buffer,
            'max_lat': max(lats) + buffer,
            'min_lon': min(lons) - buffer,
            'max_lon': max(lons) + buffer
        }
        
        return bounds
        
    except Exception as e:
        print(f"Error getting bounds from photos: {e}")
        return None

def create_mapbox_html_with_data(photo_data, pluto_data, property_values):
    """
    Create an HTML file with Mapbox visualization
    """
    
    # Create property value lookup by BBL
    property_lookup = {item['bbl']: item for item in property_values}
    
    # Enhance PLUTO data with property values
    enhanced_pluto_features = []
    for feature in pluto_data.get('features', []):
        bbl = feature.get('properties', {}).get('bbl')
        if bbl and bbl in property_lookup:
            prop_data = property_lookup[bbl]
            # Add property value data to PLUTO feature properties
            feature['properties'].update({
                'fullval': prop_data.get('fullval', 'N/A'),
                'avland': prop_data.get('avland', 'N/A'),
                'avtot': prop_data.get('avtot', 'N/A'),
                'landuse_description': feature['properties'].get('landuse', 'Unknown'),
                'building_class': feature['properties'].get('bldgclass', 'Unknown')
            })
            enhanced_pluto_features.append(feature)
    
    enhanced_pluto_data = {
        "type": "FeatureCollection",
        "features": enhanced_pluto_features
    }
    
    # Calculate center point from photo data
    if photo_data.get('features'):
        lons = [f['geometry']['coordinates'][0] for f in photo_data['features'] if f.get('geometry', {}).get('type') == 'Point']
        lats = [f['geometry']['coordinates'][1] for f in photo_data['features'] if f.get('geometry', {}).get('type') == 'Point']
        center_lon = sum(lons) / len(lons) if lons else -73.9857
        center_lat = sum(lats) / len(lats) if lats else 40.7484
    else:
        center_lon = -73.9857  # Default to NYC
        center_lat = 40.7484
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Photo Locations vs NYC Property Data</title>
    <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no">
    <link href="https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.css" rel="stylesheet">
    <script src="https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.js"></script>
    <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
        .mapboxgl-popup-content {{
            max-width: 300px;
        }}
        .legend {{
            background-color: white;
            border-radius: 3px;
            bottom: 30px;
            left: 10px;
            padding: 10px;
            position: absolute;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            margin-right: 10px;
            border-radius: 50%;
        }}
        .controls {{
            background-color: white;
            border-radius: 3px;
            top: 10px;
            left: 10px;
            padding: 10px;
            position: absolute;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }}
        .control-group {{
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div class="controls">
        <div class="control-group">
            <h4>Layer Controls</h4>
            <label><input type="checkbox" id="photos-toggle" checked> Photo Locations</label><br>
            <label><input type="checkbox" id="pluto-toggle" checked> Property Data</label>
        </div>
        <div class="control-group">
            <h4>Property Value Filter</h4>
            <label>Min Value: $<input type="number" id="min-value" value="0" step="10000"></label><br>
            <label>Max Value: $<input type="number" id="max-value" value="10000000" step="10000"></label><br>
            <button onclick="filterByValue()">Apply Filter</button>
        </div>
    </div>
    
    <div class="legend">
        <h4>Legend</h4>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #FF6B6B;"></div>
            <span>High Interest (5+ photos)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #4ECDC4;"></div>
            <span>Medium Interest (2-4 photos)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #45B7D1;"></div>
            <span>Low Interest (1 photo)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #FFA07A; opacity: 0.6;"></div>
            <span>Property Boundaries</span>
        </div>
    </div>

    <script>
        mapboxgl.accessToken = '{MAPBOX_TOKEN}';
        
        const map = new mapboxgl.Map({{
            container: 'map',
            style: 'mapbox://styles/mapbox/light-v11',
            center: [{center_lon}, {center_lat}],
            zoom: 12
        }});
        
        // Data
        const photoData = {json.dumps(photo_data)};
        const plutoData = {json.dumps(enhanced_pluto_data)};
        
        map.on('load', () => {{
            // Add photo location data
            map.addSource('photos', {{
                'type': 'geojson',
                'data': photoData
            }});
            
            // Add PLUTO property data
            map.addSource('pluto', {{
                'type': 'geojson',
                'data': plutoData
            }});
            
            // Property boundaries layer
            map.addLayer({{
                'id': 'property-boundaries',
                'type': 'fill',
                'source': 'pluto',
                'paint': {{
                    'fill-color': '#FFA07A',
                    'fill-opacity': 0.3,
                    'fill-outline-color': '#FF7F50'
                }}
            }});
            
            // Photo locations layer
            map.addLayer({{
                'id': 'photo-points',
                'type': 'circle',
                'source': 'photos',
                'paint': {{
                    'circle-radius': [
                        'interpolate',
                        ['linear'],
                        ['get', 'photo_count'],
                        1, 8,
                        2, 12,
                        5, 16
                    ],
                    'circle-color': [
                        'case',
                        ['>=', ['get', 'photo_count'], 5], '#FF6B6B',
                        ['>=', ['get', 'photo_count'], 2], '#4ECDC4',
                        '#45B7D1'
                    ],
                    'circle-stroke-width': 2,
                    'circle-stroke-color': '#FFFFFF'
                }}
            }});
            
            // Click events for popups
            map.on('click', 'photo-points', (e) => {{
                const properties = e.features[0].properties;
                new mapboxgl.Popup()
                    .setLngLat(e.lngLat)
                    .setHTML(`
                        <strong>Photo Location</strong><br>
                        Photos taken: ${{properties.photo_count}}<br>
                        Interest level: ${{properties.interest_level}}<br>
                        Location: ${{properties.location_cluster}}
                    `)
                    .addTo(map);
            }});
            
            map.on('click', 'property-boundaries', (e) => {{
                const properties = e.features[0].properties;
                new mapboxgl.Popup()
                    .setLngLat(e.lngLat)
                    .setHTML(`
                        <strong>Property Information</strong><br>
                        BBL: ${{properties.bbl}}<br>
                        Land Use: ${{properties.landuse_description}}<br>
                        Building Class: ${{properties.building_class}}<br>
                        Total Value: $$${{Number(properties.fullval).toLocaleString() || 'N/A'}}<br>
                        Land Value: $$${{Number(properties.avland).toLocaleString() || 'N/A'}}<br>
                        Building Value: $$${{Number(properties.avtot).toLocaleString() || 'N/A'}}
                    `)
                    .addTo(map);
            }});
            
            // Hover effects
            map.on('mouseenter', 'photo-points', () => {{
                map.getCanvas().style.cursor = 'pointer';
            }});
            
            map.on('mouseleave', 'photo-points', () => {{
                map.getCanvas().style.cursor = '';
            }});
            
            map.on('mouseenter', 'property-boundaries', () => {{
                map.getCanvas().style.cursor = 'pointer';
            }});
            
            map.on('mouseleave', 'property-boundaries', () => {{
                map.getCanvas().style.cursor = '';
            }});
        }});
        
        // Layer toggle controls
        document.getElementById('photos-toggle').addEventListener('change', (e) => {{
            const visibility = e.target.checked ? 'visible' : 'none';
            map.setLayoutProperty('photo-points', 'visibility', visibility);
        }});
        
        document.getElementById('pluto-toggle').addEventListener('change', (e) => {{
            const visibility = e.target.checked ? 'visible' : 'none';
            map.setLayoutProperty('property-boundaries', 'visibility', visibility);
        }});
        
        // Value filter function
        function filterByValue() {{
            const minVal = document.getElementById('min-value').value;
            const maxVal = document.getElementById('max-value').value;
            
            const filter = [
                'all',
                ['>=', ['to-number', ['get', 'fullval']], parseFloat(minVal)],
                ['<=', ['to-number', ['get', 'fullval']], parseFloat(maxVal)]
            ];
            
            map.setFilter('property-boundaries', filter);
        }}
    </script>
</body>
</html>
"""
    
    return html_content

def main():
    """Main function to create the visualization"""
    
    # Load photo data
    try:
        with open('photo_locations_aggregated.geojson', 'r') as f:
            photo_data = geojson.load(f)
        print(f"Loaded {len(photo_data.get('features', []))} photo locations")
    except FileNotFoundError:
        print("Error: photo_locations_aggregated.geojson not found. Run extract_photo_locations.py first.")
        return
    
    # Get bounds from photo data
    bounds = get_bounds_from_photos('photo_locations_aggregated.geojson')
    if not bounds:
        print("Could not determine bounds from photo data")
        return
    
    print(f"Photo data bounds: {bounds}")
    
    # Fetch PLUTO data for the area around photo locations
    pluto_data = fetch_pluto_data_for_bounds(
        bounds['min_lat'], bounds['max_lat'], 
        bounds['min_lon'], bounds['max_lon']
    )
    
    # Extract BBLs from PLUTO data for property value lookup
    bbls = []
    for feature in pluto_data.get('features', []):
        bbl = feature.get('properties', {}).get('bbl')
        if bbl:
            bbls.append(bbl)
    
    # Fetch property values
    property_values = fetch_property_values_for_bbls(bbls)
    
    # Create the HTML visualization
    html_content = create_mapbox_html_with_data(photo_data, pluto_data, property_values)
    
    # Save the HTML file
    with open('photo_property_visualization.html', 'w') as f:
        f.write(html_content)
    
    print("Created photo_property_visualization.html")
    print(f"Open this file in a web browser to view the interactive map")
    
    # Save enhanced data for reference
    enhanced_data = {
        'photo_locations': photo_data,
        'pluto_properties': pluto_data,
        'property_values_count': len(property_values),
        'bounds_used': bounds,
        'created_at': datetime.now().isoformat()
    }
    
    with open('visualization_data_summary.json', 'w') as f:
        json.dump(enhanced_data, f, indent=2)
    
    print("Created visualization_data_summary.json with metadata")

if __name__ == '__main__':
    main()