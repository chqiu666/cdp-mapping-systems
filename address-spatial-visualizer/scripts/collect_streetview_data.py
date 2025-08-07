#!/usr/bin/env python3
"""
Street View Data Collection Script

This script samples street view images from New York City using Google Street View Static API.
It saves metadata including geographical location and prepares data for OCR processing.

Configuration:
- Size: 640x640 (good balance of detail and API cost)
- No heading specified (ensures input variety)
- Source: outdoor (ensures street-level imagery)
- Pitch: 0 (default, horizontal view)
"""

import os
import sys
import json
import time
import random
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import googlemaps

# Load environment variables
load_dotenv()

class StreetViewCollector:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY not found in environment variables")
        
        self.gmaps = googlemaps.Client(key=self.api_key)
        self.base_url = "https://maps.googleapis.com/maps/api/streetview"
        
        # NYC bounding box (rough boundaries)
        self.nyc_bounds = {
            'north': 40.9176,
            'south': 40.4774,
            'east': -73.7004,
            'west': -74.2591
        }
        
        # Create data directories
        self.data_dir = Path('../data')
        self.images_dir = self.data_dir / 'streetview_images'
        self.metadata_dir = self.data_dir / 'metadata'
        
        for dir_path in [self.data_dir, self.images_dir, self.metadata_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def generate_random_nyc_location(self):
        """Generate a random latitude/longitude within NYC bounds"""
        lat = random.uniform(self.nyc_bounds['south'], self.nyc_bounds['north'])
        lng = random.uniform(self.nyc_bounds['west'], self.nyc_bounds['east'])
        return lat, lng
    
    def check_streetview_availability(self, lat, lng):
        """Check if street view is available at the given location"""
        try:
            # Use Street View Metadata API to check availability
            metadata_url = f"{self.base_url}/metadata"
            params = {
                'location': f"{lat},{lng}",
                'key': self.api_key,
                'source': 'outdoor'
            }
            
            response = requests.get(metadata_url, params=params)
            response.raise_for_status()
            
            metadata = response.json()
            return metadata.get('status') == 'OK', metadata
            
        except Exception as e:
            print(f"Error checking street view availability: {e}")
            return False, None
    
    def download_streetview_image(self, lat, lng, filename):
        """Download street view image for given coordinates"""
        try:
            params = {
                'size': '640x640',
                'location': f"{lat},{lng}",
                'key': self.api_key,
                'source': 'outdoor',
                'pitch': 0,
                # No heading parameter - let Google choose the best view
            }
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            # Save image
            image_path = self.images_dir / filename
            with open(image_path, 'wb') as f:
                f.write(response.content)
            
            return True, str(image_path)
            
        except Exception as e:
            print(f"Error downloading street view image: {e}")
            return False, None
    
    def save_metadata(self, image_id, lat, lng, streetview_metadata, image_path):
        """Save metadata for the collected image"""
        metadata = {
            'image_id': image_id,
            'timestamp': datetime.now().isoformat(),
            'coordinates': {
                'latitude': lat,
                'longitude': lng
            },
            'streetview_metadata': streetview_metadata,
            'image_path': image_path,
            'api_parameters': {
                'size': '640x640',
                'source': 'outdoor',
                'pitch': 0,
                'heading': 'auto'
            }
        }
        
        metadata_path = self.metadata_dir / f"{image_id}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return str(metadata_path)
    
    def collect_sample(self, sample_size=100, max_attempts=500):
        """Collect street view images from NYC"""
        print(f"Starting collection of {sample_size} street view images from NYC...")
        print(f"Maximum attempts: {max_attempts}")
        
        collected = 0
        attempts = 0
        failed_locations = []
        
        while collected < sample_size and attempts < max_attempts:
            attempts += 1
            
            # Generate random location
            lat, lng = self.generate_random_nyc_location()
            
            print(f"\nAttempt {attempts}: Checking location ({lat:.6f}, {lng:.6f})")
            
            # Check if street view is available
            is_available, metadata = self.check_streetview_availability(lat, lng)
            
            if not is_available:
                print("Street view not available at this location")
                failed_locations.append((lat, lng, "not_available"))
                continue
            
            # Download image
            image_id = f"streetview_{collected+1:04d}_{int(time.time())}"
            filename = f"{image_id}.jpg"
            
            success, image_path = self.download_streetview_image(lat, lng, filename)
            
            if not success:
                print("Failed to download image")
                failed_locations.append((lat, lng, "download_failed"))
                continue
            
            # Save metadata
            metadata_path = self.save_metadata(image_id, lat, lng, metadata, image_path)
            
            collected += 1
            print(f"✓ Successfully collected image {collected}/{sample_size}")
            print(f"  Image: {image_path}")
            print(f"  Metadata: {metadata_path}")
            
            # Rate limiting - be respectful to the API
            time.sleep(0.1)
        
        print(f"\n=== Collection Complete ===")
        print(f"Successfully collected: {collected} images")
        print(f"Total attempts: {attempts}")
        print(f"Failed locations: {len(failed_locations)}")
        
        # Save summary
        summary = {
            'collection_timestamp': datetime.now().isoformat(),
            'total_collected': collected,
            'total_attempts': attempts,
            'success_rate': collected / attempts if attempts > 0 else 0,
            'failed_locations': failed_locations,
            'nyc_bounds': self.nyc_bounds
        }
        
        summary_path = self.data_dir / 'collection_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"Collection summary saved to: {summary_path}")
        
        return collected

def main():
    try:
        collector = StreetViewCollector()
        
        # Default sample size
        sample_size = 50
        
        # Allow command line argument for sample size
        if len(sys.argv) > 1:
            try:
                sample_size = int(sys.argv[1])
            except ValueError:
                print("Invalid sample size. Using default of 50.")
        
        print(f"Google Street View Data Collector")
        print(f"Target sample size: {sample_size}")
        print(f"API Key configured: {'Yes' if collector.api_key else 'No'}")
        
        collected = collector.collect_sample(sample_size)
        
        if collected > 0:
            print(f"\n🎉 Successfully collected {collected} street view images!")
            print("Next steps:")
            print("1. Run OCR processing: python process_images_ocr.py")
            print("2. Parse addresses: python parse_addresses.py")
            print("3. Start the web application")
        else:
            print("\n❌ No images were collected. Please check your API key and try again.")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()