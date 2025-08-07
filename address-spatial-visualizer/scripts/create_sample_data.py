#!/usr/bin/env python3
"""
Create Sample Data Script

This script creates sample connection data for testing the visualization
when real street view data collection hasn't been run yet.
"""

import json
import random
from pathlib import Path
from datetime import datetime

def create_sample_data():
    """Create sample connection data for NYC"""
    
    # NYC sample addresses and coordinates
    sample_addresses = [
        {"address": "Times Square, New York, NY", "lat": 40.7580, "lng": -73.9855},
        {"address": "Central Park, New York, NY", "lat": 40.7829, "lng": -73.9654},
        {"address": "Brooklyn Bridge, New York, NY", "lat": 40.7061, "lng": -73.9969},
        {"address": "Empire State Building, New York, NY", "lat": 40.7484, "lng": -73.9857},
        {"address": "Statue of Liberty, New York, NY", "lat": 40.6892, "lng": -74.0445},
        {"address": "Wall Street, New York, NY", "lat": 40.7074, "lng": -74.0113},
        {"address": "High Line, New York, NY", "lat": 40.7480, "lng": -74.0048},
        {"address": "9/11 Memorial, New York, NY", "lat": 40.7115, "lng": -74.0134},
        {"address": "Chinatown, New York, NY", "lat": 40.7158, "lng": -73.9970},
        {"address": "Little Italy, New York, NY", "lat": 40.7196, "lng": -73.9977}
    ]
    
    connections = []
    
    for i, addr_data in enumerate(sample_addresses):
        # Create random source location (street view capture point)
        # Offset from the actual address to simulate OCR extraction
        source_lat = addr_data["lat"] + random.uniform(-0.01, 0.01)
        source_lng = addr_data["lng"] + random.uniform(-0.01, 0.01)
        
        # Calculate distance
        distance = ((addr_data["lat"] - source_lat) ** 2 + (addr_data["lng"] - source_lng) ** 2) ** 0.5 * 111  # rough km conversion
        
        connection = {
            "image_id": f"sample_{i+1:03d}",
            "source": {
                "latitude": source_lat,
                "longitude": source_lng,
                "type": "streetview_location"
            },
            "target": {
                "latitude": addr_data["lat"],
                "longitude": addr_data["lng"],
                "type": "geocoded_address"
            },
            "connection": {
                "address_text": addr_data["address"],
                "confidence": random.choice(["high", "medium", "pattern_match"]),
                "distance_km": distance
            }
        }
        
        connections.append(connection)
        
        # Add some additional random connections
        if i < 5:  # Add extra connections for first 5 locations
            extra_lat = addr_data["lat"] + random.uniform(-0.005, 0.005)
            extra_lng = addr_data["lng"] + random.uniform(-0.005, 0.005)
            extra_distance = ((addr_data["lat"] - extra_lat) ** 2 + (addr_data["lng"] - extra_lng) ** 2) ** 0.5 * 111
            
            extra_connection = {
                "image_id": f"sample_{i+1:03d}_extra",
                "source": {
                    "latitude": extra_lat,
                    "longitude": extra_lng,
                    "type": "streetview_location"
                },
                "target": {
                    "latitude": addr_data["lat"],
                    "longitude": addr_data["lng"],
                    "type": "geocoded_address"
                },
                "connection": {
                    "address_text": addr_data["address"].replace(",", " St,"),  # Slight variation
                    "confidence": random.choice(["medium", "low"]),
                    "distance_km": extra_distance
                }
            }
            connections.append(extra_connection)
    
    return connections

def main():
    print("Creating sample connection data...")
    
    # Create data directories
    data_dir = Path('../data')
    connections_dir = data_dir / 'connections'
    
    data_dir.mkdir(exist_ok=True)
    connections_dir.mkdir(exist_ok=True)
    
    # Generate sample data
    connections = create_sample_data()
    
    # Save sample connections
    sample_file = connections_dir / 'all_connections.json'
    with open(sample_file, 'w') as f:
        json.dump(connections, f, indent=2)
    
    # Create a summary file
    summary = {
        "creation_timestamp": datetime.now().isoformat(),
        "data_type": "sample",
        "total_connections": len(connections),
        "unique_locations": len(set(conn["target"]["latitude"] for conn in connections)),
        "description": "Sample data for testing the address spatial visualizer"
    }
    
    summary_file = data_dir / 'sample_data_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"✓ Created {len(connections)} sample connections")
    print(f"✓ Sample data saved to: {sample_file}")
    print(f"✓ Summary saved to: {summary_file}")
    print("\nSample data is ready for visualization!")
    print("You can now start the web application to see the demo.")

if __name__ == "__main__":
    main()