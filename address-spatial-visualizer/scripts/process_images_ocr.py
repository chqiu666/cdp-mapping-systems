#!/usr/bin/env python3
"""
OCR Processing Script

This script processes street view images to extract text using OCR (Optical Character Recognition).
It uses Tesseract OCR to identify text in street view images and saves the results for address parsing.
"""

import os
import json
import cv2
import numpy as np
import pytesseract
from PIL import Image
from pathlib import Path
from datetime import datetime
import re

class OCRProcessor:
    def __init__(self):
        self.data_dir = Path('../data')
        self.images_dir = self.data_dir / 'streetview_images'
        self.metadata_dir = self.data_dir / 'metadata'
        self.ocr_results_dir = self.data_dir / 'ocr_results'
        
        # Create OCR results directory
        self.ocr_results_dir.mkdir(exist_ok=True)
        
        # Configure Tesseract (adjust path if needed)
        # pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
    
    def preprocess_image(self, image_path):
        """Preprocess image for better OCR results"""
        # Read image
        img = cv2.imread(str(image_path))
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Apply threshold to get better contrast
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Morphological operations to clean up the image
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    def extract_text_with_confidence(self, image_path):
        """Extract text from image using OCR with confidence scores"""
        try:
            # Preprocess image
            processed_img = self.preprocess_image(image_path)
            
            # Convert to PIL Image for pytesseract
            pil_img = Image.fromarray(processed_img)
            
            # Extract text with confidence data
            ocr_data = pytesseract.image_to_data(
                pil_img, 
                output_type=pytesseract.Output.DICT,
                config='--psm 6'  # Assume uniform text block
            )
            
            # Extract text with basic settings
            full_text = pytesseract.image_to_string(
                pil_img,
                config='--psm 6'
            )
            
            # Process OCR data to get words with confidence
            words_with_confidence = []
            for i in range(len(ocr_data['text'])):
                if int(ocr_data['conf'][i]) > 30:  # Only include high-confidence text
                    text = ocr_data['text'][i].strip()
                    if text:  # Only non-empty text
                        words_with_confidence.append({
                            'text': text,
                            'confidence': int(ocr_data['conf'][i]),
                            'bbox': {
                                'x': ocr_data['left'][i],
                                'y': ocr_data['top'][i],
                                'width': ocr_data['width'][i],
                                'height': ocr_data['height'][i]
                            }
                        })
            
            return {
                'full_text': full_text.strip(),
                'words_with_confidence': words_with_confidence,
                'success': True
            }
            
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            return {
                'full_text': '',
                'words_with_confidence': [],
                'success': False,
                'error': str(e)
            }
    
    def filter_potential_addresses(self, ocr_result):
        """Filter text that might contain addresses"""
        full_text = ocr_result['full_text']
        words = ocr_result['words_with_confidence']
        
        # Common address patterns
        address_patterns = [
            r'\d+\s+[A-Za-z\s]+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Place|Pl|Court|Ct)',
            r'\d+\s+[A-Za-z\s]+(St\.|Ave\.|Rd\.|Blvd\.|Ln\.|Dr\.|Pl\.|Ct\.)',
            r'[A-Za-z\s]+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Place|Pl|Court|Ct)\s+\d+',
            r'\d+[A-Za-z]?\s+[A-Za-z]+',  # Simple number + street name
        ]
        
        potential_addresses = []
        
        # Check full text for address patterns
        for pattern in address_patterns:
            matches = re.finditer(pattern, full_text, re.IGNORECASE)
            for match in matches:
                potential_addresses.append({
                    'text': match.group(),
                    'pattern': pattern,
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 'pattern_match'
                })
        
        # Look for street-related keywords in high-confidence words
        street_keywords = [
            'street', 'st', 'avenue', 'ave', 'road', 'rd', 'boulevard', 'blvd',
            'lane', 'ln', 'drive', 'dr', 'place', 'pl', 'court', 'ct',
            'way', 'plaza', 'parkway', 'pkwy', 'circle', 'cir'
        ]
        
        for word_data in words:
            word_lower = word_data['text'].lower()
            if any(keyword in word_lower for keyword in street_keywords):
                potential_addresses.append({
                    'text': word_data['text'],
                    'confidence': word_data['confidence'],
                    'bbox': word_data['bbox'],
                    'type': 'street_keyword'
                })
        
        return potential_addresses
    
    def process_all_images(self):
        """Process all collected street view images"""
        print("Starting OCR processing of street view images...")
        
        # Get list of images to process
        image_files = list(self.images_dir.glob('*.jpg'))
        
        if not image_files:
            print("No images found to process. Run collect_streetview_data.py first.")
            return
        
        print(f"Found {len(image_files)} images to process")
        
        results_summary = {
            'processing_timestamp': datetime.now().isoformat(),
            'total_images': len(image_files),
            'processed_successfully': 0,
            'failed_processing': 0,
            'images_with_text': 0,
            'images_with_addresses': 0,
            'results': []
        }
        
        for i, image_path in enumerate(image_files, 1):
            print(f"\nProcessing {i}/{len(image_files)}: {image_path.name}")
            
            # Extract image ID from filename
            image_id = image_path.stem
            
            # Load corresponding metadata
            metadata_file = self.metadata_dir / f"{image_id}_metadata.json"
            metadata = {}
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
            
            # Perform OCR
            ocr_result = self.extract_text_with_confidence(image_path)
            
            if ocr_result['success']:
                results_summary['processed_successfully'] += 1
                
                # Filter for potential addresses
                potential_addresses = self.filter_potential_addresses(ocr_result)
                
                if ocr_result['full_text'].strip():
                    results_summary['images_with_text'] += 1
                
                if potential_addresses:
                    results_summary['images_with_addresses'] += 1
                
                # Combine all data
                result_data = {
                    'image_id': image_id,
                    'image_path': str(image_path),
                    'metadata': metadata,
                    'ocr_result': ocr_result,
                    'potential_addresses': potential_addresses,
                    'processing_timestamp': datetime.now().isoformat()
                }
                
                # Save individual result
                result_file = self.ocr_results_dir / f"{image_id}_ocr.json"
                with open(result_file, 'w') as f:
                    json.dump(result_data, f, indent=2)
                
                results_summary['results'].append({
                    'image_id': image_id,
                    'has_text': bool(ocr_result['full_text'].strip()),
                    'potential_addresses_count': len(potential_addresses),
                    'result_file': str(result_file)
                })
                
                print(f"  ✓ Text extracted: {len(ocr_result['full_text'])} characters")
                print(f"  ✓ Potential addresses found: {len(potential_addresses)}")
                
            else:
                results_summary['failed_processing'] += 1
                print(f"  ✗ Failed to process: {ocr_result.get('error', 'Unknown error')}")
        
        # Save summary
        summary_file = self.data_dir / 'ocr_processing_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(results_summary, f, indent=2)
        
        print(f"\n=== OCR Processing Complete ===")
        print(f"Total images: {results_summary['total_images']}")
        print(f"Successfully processed: {results_summary['processed_successfully']}")
        print(f"Failed processing: {results_summary['failed_processing']}")
        print(f"Images with text: {results_summary['images_with_text']}")
        print(f"Images with potential addresses: {results_summary['images_with_addresses']}")
        print(f"Summary saved to: {summary_file}")
        
        return results_summary

def main():
    try:
        processor = OCRProcessor()
        results = processor.process_all_images()
        
        if results and results['images_with_addresses'] > 0:
            print(f"\n🎉 Found potential addresses in {results['images_with_addresses']} images!")
            print("Next step: Run address parsing - python parse_addresses.py")
        else:
            print("\n⚠️  No potential addresses found. You may need to:")
            print("1. Collect more street view images")
            print("2. Adjust OCR parameters")
            print("3. Check image quality")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()