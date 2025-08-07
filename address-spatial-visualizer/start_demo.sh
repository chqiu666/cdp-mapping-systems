#!/bin/bash

echo "🗺️  Address Spatial Visualizer - Demo Setup"
echo "=========================================="

# Check if sample data exists
if [ ! -f "data/connections/all_connections.json" ]; then
    echo "📊 Creating sample data..."
    cd scripts
    python3 create_sample_data.py
    cd ..
fi

echo "📦 Installing frontend dependencies..."
cd frontend

# Install npm dependencies if needed
if [ ! -d "node_modules" ]; then
    npm install
fi

echo "🚀 Starting the application..."
echo ""
echo "The application will open in your browser at: http://localhost:3000"
echo "Press Ctrl+C to stop the server"
echo ""

npm start