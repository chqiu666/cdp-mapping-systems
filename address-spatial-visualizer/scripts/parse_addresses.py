#!/usr/bin/env python3
"""
Address Parsing and Geocoding Script

This script processes OCR results to parse addresses and geocode them to coordinates,
creating the connection data for visualization.
"""

import os
import json
import time
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import googlemaps
import usaddress
from geopy.geocoders import GoogleV3
from geopy.exc import GeocoderTimedOut, GeocoderQuotaExceeded

# Load environment variables
load_dotenv()

class AddressParser:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY not found in environment variables")
        
        self.gmaps = googlemaps.Client(key=self.api_key)
        self.geocoder = GoogleV3(api_key=self.api_key)
        
        self.data_dir = Path('../data')
        self.ocr_results_dir = self.data_dir / 'ocr_results'
        self.parsed_addresses_dir = self.data_dir / 'parsed_addresses'
        self.connections_dir = self.data_dir / 'connections'
        
        # Create directories
        for dir_path in [self.parsed_addresses_dir, self.connections_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def clean_address_text(self, text):
        """Clean and normalize address text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common OCR artifacts
        text = re.sub(r'[^\w\s\-\.\,\#]', '', text)
        
        # Normalize common abbreviations
        abbreviations = {
            'ST': 'Street',
            'AVE': 'Avenue', 
            'RD': 'Road',
            'BLVD': 'Boulevard',
            'LN': 'Lane',
            'DR': 'Drive',
            'PL': 'Place',
            'CT': 'Court'
        }
        
        for abbr, full in abbreviations.items():
            text = re.sub(rf'\b{abbr}\b', full, text, flags=re.IGNORECASE)
        
        return text
    
    def parse_address_components(self, address_text):
        """Parse address using usaddress library"""
        try:
            cleaned_text = self.clean_address_text(address_text)
            parsed, address_type = usaddress.tag(cleaned_text)
            
            return {
                'success': True,
                'parsed_components': parsed,
                'address_type': address_type,
                'cleaned_text': cleaned_text
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'cleaned_text': self.clean_address_text(address_text)
            }
    
    def geocode_address(self, address_text, bias_location=None):
        """Geocode address to get coordinates"""
        try:
            # Add NYC context to improve geocoding accuracy
            search_address = f"{address_text}, New York, NY"
            
            # Use Google Maps Geocoding API
            geocode_result = self.gmaps.geocode(
                search_address,
                bounds={
                    'northeast': {'lat': 40.9176, 'lng': -73.7004},
                    'southwest': {'lat': 40.4774, 'lng': -74.2591}
                } if not bias_location else None,
                region='us'
            )
            
            if geocode_result:
                result = geocode_result[0]
                location = result['geometry']['location']
                
                return {
                    'success': True,
                    'latitude': location['lat'],
                    'longitude': location['lng'],
                    'formatted_address': result['formatted_address'],
                    'place_id': result['place_id'],
                    'address_components': result['address_components'],
                    'geometry': result['geometry']
                }
            else:
                return {
                    'success': False,
                    'error': 'No geocoding results found'
                }
                
        except Exception as e:
            print(f"Geocoding error for '{address_text}': {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_connection_data(self, source_location, target_location, address_text, confidence):
        """Create connection data for visualization"""
        return {
            'source': {
                'latitude': source_location['latitude'],
                'longitude': source_location['longitude'],
                'type': 'streetview_location'
            },
            'target': {
                'latitude': target_location['latitude'],
                'longitude': target_location['longitude'],
                'type': 'geocoded_address'
            },
            'connection': {
                'address_text': address_text,
                'confidence': confidence,
                'distance_km': self.calculate_distance(source_location, target_location)
            }
        }
    
    def calculate_distance(self, loc1, loc2):
        """Calculate distance between two coordinates using Haversine formula"""
        from math import radians, cos, sin, asin, sqrt
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [
            loc1['latitude'], loc1['longitude'],
            loc2['latitude'], loc2['longitude']
        ])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of Earth in kilometers
        r = 6371
        return c * r
    
    def process_ocr_results(self):
        """Process all OCR results to parse addresses and create connections"""
        print("Starting address parsing and geocoding...")
        
        # Get OCR result files
        ocr_files = list(self.ocr_results_dir.glob('*_ocr.json'))
        
        if not ocr_files:
            print("No OCR results found. Run process_images_ocr.py first.")
            return
        
        print(f"Found {len(ocr_files)} OCR result files to process")
        
        processing_summary = {
            'processing_timestamp': datetime.now().isoformat(),
            'total_ocr_files': len(ocr_files),
            'files_with_addresses': 0,
            'total_addresses_found': 0,
            'successfully_geocoded': 0,
            'failed_geocoding': 0,
            'connections_created': 0,
            'results': []
        }
        
        all_connections = []
        
        for i, ocr_file in enumerate(ocr_files, 1):
            print(f"\nProcessing {i}/{len(ocr_files)}: {ocr_file.name}")
            
            # Load OCR results
            with open(ocr_file, 'r') as f:
                ocr_data = json.load(f)
            
            image_id = ocr_data['image_id']
            potential_addresses = ocr_data.get('potential_addresses', [])
            source_location = ocr_data['metadata']['coordinates']
            
            if not potential_addresses:
                print("  No potential addresses found")
                continue
            
            processing_summary['files_with_addresses'] += 1
            processing_summary['total_addresses_found'] += len(potential_addresses)
            
            file_results = {
                'image_id': image_id,
                'source_location': source_location,
                'addresses_processed': [],
                'connections': []
            }
            
            for addr_idx, addr_data in enumerate(potential_addresses):
                address_text = addr_data['text']
                print(f"    Processing address: '{address_text}'")
                
                # Parse address components
                parse_result = self.parse_address_components(address_text)
                
                # Geocode address
                geocode_result = self.geocode_address(address_text, source_location)
                
                address_result = {
                    'original_text': address_text,
                    'parse_result': parse_result,
                    'geocode_result': geocode_result,
                    'confidence': addr_data.get('confidence', 'unknown')
                }
                
                if geocode_result['success']:
                    processing_summary['successfully_geocoded'] += 1
                    
                    # Create connection data
                    connection = self.create_connection_data(
                        source_location,
                        geocode_result,
                        address_text,
                        addr_data.get('confidence', 'unknown')
                    )
                    
                    file_results['connections'].append(connection)
                    all_connections.append({
                        'image_id': image_id,
                        **connection
                    })
                    
                    processing_summary['connections_created'] += 1
                    
                    print(f"      ✓ Geocoded: {geocode_result['formatted_address']}")
                    print(f"      ✓ Distance: {connection['connection']['distance_km']:.2f} km")
                    
                else:
                    processing_summary['failed_geocoding'] += 1
                    print(f"      ✗ Geocoding failed: {geocode_result.get('error', 'Unknown error')}")
                
                file_results['addresses_processed'].append(address_result)
                
                # Rate limiting
                time.sleep(0.1)
            
            # Save individual file results
            result_file = self.parsed_addresses_dir / f"{image_id}_parsed.json"
            with open(result_file, 'w') as f:
                json.dump(file_results, f, indent=2)
            
            processing_summary['results'].append({
                'image_id': image_id,
                'addresses_count': len(potential_addresses),
                'successful_geocodes': len(file_results['connections']),
                'result_file': str(result_file)
            })
        
        # Save all connections for visualization
        connections_file = self.connections_dir / 'all_connections.json'
        with open(connections_file, 'w') as f:
            json.dump(all_connections, f, indent=2)
        
        # Save processing summary
        summary_file = self.data_dir / 'address_parsing_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(processing_summary, f, indent=2)
        
        print(f"\n=== Address Parsing Complete ===")
        print(f"Total OCR files: {processing_summary['total_ocr_files']}")
        print(f"Files with addresses: {processing_summary['files_with_addresses']}")
        print(f"Total addresses found: {processing_summary['total_addresses_found']}")
        print(f"Successfully geocoded: {processing_summary['successfully_geocoded']}")
        print(f"Failed geocoding: {processing_summary['failed_geocoding']}")
        print(f"Connections created: {processing_summary['connections_created']}")
        print(f"Connections data saved to: {connections_file}")
        print(f"Summary saved to: {summary_file}")
        
        return processing_summary, all_connections

def main():
    try:
        parser = AddressParser()
        summary, connections = parser.process_ocr_results()
        
        if connections:
            print(f"\n🎉 Created {len(connections)} address-to-location connections!")
            print("Ready for visualization!")
            print("Next step: Start the web application")
        else:
            print("\n⚠️  No connections created. Check:")
            print("1. OCR results contain addresses")
            print("2. Google Maps API key is valid")
            print("3. Geocoding quota is not exceeded")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()