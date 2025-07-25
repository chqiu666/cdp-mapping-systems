#!/usr/bin/env python3
"""
Extract GPS coordinates and timestamps from photo EXIF data and create GeoJSON
"""

import os
import json
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import geojson
from collections import defaultdict

def get_geotagging(exif):
    """Extract GPS information from EXIF data"""
    if not exif:
        return None
        
    geotagging = {}
    for (idx, tag) in TAGS.items():
        if tag == 'GPSInfo':
            if idx not in exif:
                return None
                
            for (key, val) in GPSTAGS.items():
                if key in exif[idx]:
                    geotagging[val] = exif[idx][key]

    return geotagging

def get_decimal_from_dms(dms, ref):
    """Convert DMS (degrees, minutes, seconds) to decimal degrees"""
    degrees = dms[0]
    minutes = dms[1] / 60.0
    seconds = dms[2] / 3600.0
    
    if ref in ['S', 'W']:
        degrees = -degrees
        minutes = -minutes
        seconds = -seconds
        
    return degrees + minutes + seconds

def get_coordinates(geotags):
    """Extract latitude and longitude from geotags"""
    lat = geotags.get('GPSLatitude')
    lat_ref = geotags.get('GPSLatitudeRef')
    lon = geotags.get('GPSLongitude')
    lon_ref = geotags.get('GPSLongitudeRef')
    
    if lat and lat_ref and lon and lon_ref:
        lat = get_decimal_from_dms(lat, lat_ref)
        lon = get_decimal_from_dms(lon, lon_ref)
        return (lon, lat)  # GeoJSON uses [longitude, latitude]
    return None

def get_date_taken(exif):
    """Extract date taken from EXIF data"""
    date_tags = ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']
    
    for tag in date_tags:
        for (key, val) in TAGS.items():
            if val == tag and key in exif:
                try:
                    return datetime.strptime(exif[key], '%Y:%m:%d %H:%M:%S').isoformat()
                except ValueError:
                    continue
    return None

def process_photos(photo_dir):
    """Process all photos in directory and extract location/time data"""
    features = []
    location_counts = defaultdict(int)
    
    for filename in os.listdir(photo_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.tiff', '.tif')):
            filepath = os.path.join(photo_dir, filename)
            
            try:
                with Image.open(filepath) as image:
                    exif = image._getexif()
                    
                    if exif:
                        # Extract GPS coordinates
                        geotags = get_geotagging(exif)
                        if geotags:
                            coords = get_coordinates(geotags)
                            if coords:
                                # Extract timestamp
                                date_taken = get_date_taken(exif)
                                
                                # Round coordinates to reduce precision for clustering nearby photos
                                rounded_coords = (round(coords[0], 4), round(coords[1], 4))
                                location_counts[rounded_coords] += 1
                                
                                # Create GeoJSON feature
                                feature = geojson.Feature(
                                    geometry=geojson.Point(coords),
                                    properties={
                                        'filename': filename,
                                        'date_taken': date_taken,
                                        'photo_count': 1
                                    }
                                )
                                features.append(feature)
                                
                print(f"Processed: {filename}")
                                
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                continue
    
    # Create aggregated features based on location clusters
    aggregated_features = []
    processed_locations = set()
    
    for feature in features:
        coords = tuple(feature.geometry.coordinates)
        rounded_coords = (round(coords[0], 4), round(coords[1], 4))
        
        if rounded_coords not in processed_locations:
            processed_locations.add(rounded_coords)
            
            # Count photos at this location
            count = location_counts[rounded_coords]
            
            # Use the original coordinates for the first photo at this location
            aggregated_feature = geojson.Feature(
                geometry=geojson.Point(coords),
                properties={
                    'photo_count': count,
                    'location_cluster': f"{rounded_coords[1]:.4f},{rounded_coords[0]:.4f}",
                    'interest_level': 'high' if count >= 5 else 'medium' if count >= 2 else 'low'
                }
            )
            aggregated_features.append(aggregated_feature)
    
    return features, aggregated_features

def main():
    """Main function to process photos and create GeoJSON"""
    photo_dir = 'photoset'
    
    print("Extracting EXIF data from photos...")
    features, aggregated_features = process_photos(photo_dir)
    
    print(f"Found {len(features)} photos with GPS data")
    print(f"Created {len(aggregated_features)} location clusters")
    
    # Create GeoJSON FeatureCollection for individual photos
    individual_collection = geojson.FeatureCollection(features)
    
    # Create GeoJSON FeatureCollection for aggregated locations
    aggregated_collection = geojson.FeatureCollection(aggregated_features)
    
    # Save individual photos GeoJSON
    with open('photo_locations_individual.geojson', 'w') as f:
        geojson.dump(individual_collection, f, indent=2)
    
    # Save aggregated locations GeoJSON
    with open('photo_locations_aggregated.geojson', 'w') as f:
        geojson.dump(aggregated_collection, f, indent=2)
    
    print("Created:")
    print("- photo_locations_individual.geojson (all individual photo locations)")
    print("- photo_locations_aggregated.geojson (clustered locations with photo counts)")
    
    # Print some statistics
    if aggregated_features:
        photo_counts = [f.properties['photo_count'] for f in aggregated_features]
        print(f"\nStatistics:")
        print(f"- Total locations: {len(aggregated_features)}")
        print(f"- Max photos at one location: {max(photo_counts)}")
        print(f"- Average photos per location: {sum(photo_counts)/len(photo_counts):.1f}")
        
        # Top locations
        top_locations = sorted(aggregated_features, 
                             key=lambda x: x.properties['photo_count'], 
                             reverse=True)[:5]
        print(f"\nTop 5 locations by photo count:")
        for i, loc in enumerate(top_locations, 1):
            coords = loc.geometry.coordinates
            count = loc.properties['photo_count']
            print(f"{i}. {count} photos at ({coords[1]:.4f}, {coords[0]:.4f})")

if __name__ == '__main__':
    main()