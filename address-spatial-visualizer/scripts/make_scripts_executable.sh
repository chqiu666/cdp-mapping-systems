#!/bin/bash

# Make Python scripts executable
chmod +x collect_streetview_data.py
chmod +x process_images_ocr.py
chmod +x parse_addresses.py

echo "Python scripts are now executable"
echo "Run with:"
echo "  ./collect_streetview_data.py"
echo "  ./process_images_ocr.py"  
echo "  ./parse_addresses.py"