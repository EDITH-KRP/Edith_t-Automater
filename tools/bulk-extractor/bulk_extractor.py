#!/usr/bin/env python3
"""
Python-based Bulk Extractor Alternative for Windows
Implements basic pattern extraction capabilities as a fallback
when the native bulk_extractor executable is not available.
"""

import os
import re
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path

class BulkExtractorAlternative:
    """Python implementation of basic bulk_extractor functionality"""
    
    def __init__(self):
        self.patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'url': re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'),
            'ip': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            'phone': re.compile(r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'),
            'ssn': re.compile(r'\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b'),
            'credit_card': re.compile(r'\b[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}\b'),
            'base16': re.compile(r'\b[A-Fa-f0-9]{32,}\b'),  # MD5, SHA hashes, etc.
        }
        
        self.results = {}
        self.stats = {
            'bytes_processed': 0,
            'patterns_found': 0,
            'processing_time': 0
        }

    def extract_from_chunk(self, chunk, chunk_offset=0):
        """Extract patterns from a data chunk - optimized for speed"""
        # Try different encodings for better pattern detection
        chunk_str = None
        
        # Check for UTF-16 BOM
        if chunk.startswith(b'\xff\xfe'):
            try:
                chunk_str = chunk.decode('utf-16le', errors='ignore')
            except:
                chunk_str = chunk.decode('utf-8', errors='ignore')
        elif chunk.startswith(b'\xfe\xff'):
            try:
                chunk_str = chunk.decode('utf-16be', errors='ignore')
            except:
                chunk_str = chunk.decode('utf-8', errors='ignore')
        else:
            # Default to UTF-8
            chunk_str = chunk.decode('utf-8', errors='ignore')
        
        for pattern_name, pattern in self.patterns.items():
            matches = list(pattern.finditer(chunk_str))
            
            if pattern_name not in self.results:
                self.results[pattern_name] = []
            
            if matches:  # Only process if we found matches
                for match in matches:
                    # Simplified data structure for speed
                    self.results[pattern_name].append({
                        'offset': chunk_offset + match.start(),
                        'length': len(match.group()),
                        'data': match.group()
                        # Removed context to speed up processing
                    })
                    self.stats['patterns_found'] += 1

    def process_file(self, file_path, chunk_size=10*1024*1024):  # 10MB chunks for faster processing
        """Process file in chunks to handle large files"""
        print(f"[INFO] Processing file: {file_path}")
        
        start_time = datetime.now()
        
        try:
            with open(file_path, 'rb') as f:
                offset = 0
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    self.extract_from_chunk(chunk, offset)
                    offset += len(chunk)
                    self.stats['bytes_processed'] += len(chunk)
                    
                    # Progress indicator for large files - every 100MB
                    if offset % (100 * 1024 * 1024) == 0:  # Every 100MB
                        print(f"[PROGRESS] Processed {offset // (1024*1024)} MB...")
                        
        except Exception as e:
            print(f"[ERROR] Failed to process file: {e}")
            return False
            
        end_time = datetime.now()
        self.stats['processing_time'] = (end_time - start_time).total_seconds()
        return True

    def save_results(self, output_dir):
        """Save extraction results in bulk_extractor compatible format"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save individual pattern files
        for pattern_name, matches in self.results.items():
            if matches:
                output_file = os.path.join(output_dir, f"{pattern_name}.txt")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"# BULK_EXTRACTOR-{datetime.now().strftime('%Y%m%d')}\n")
                    f.write(f"# {pattern_name.upper()} extracted by Python alternative\n")
                    f.write(f"# Total matches: {len(matches)}\n\n")
                    
                    for match in matches:
                        f.write(f"{match['offset']:010d}\t{match['data']}\n")
                
                print(f"[SAVED] {len(matches)} {pattern_name} patterns -> {output_file}")

        # Save summary report
        summary_file = os.path.join(output_dir, "report.xml")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<dfxml version="1.0">\n')
            f.write('  <metadata>\n')
            f.write(f'    <dc:type>Feature Extraction Report</dc:type>\n')
            f.write(f'    <dc:date>{datetime.now().isoformat()}</dc:date>\n')
            f.write('  </metadata>\n')
            f.write('  <creator>\n')
            f.write('    <program>Python Bulk Extractor Alternative</program>\n')
            f.write('    <version>1.0</version>\n')
            f.write('  </creator>\n')
            f.write('  <source>\n')
            f.write(f'    <bytes_processed>{self.stats["bytes_processed"]}</bytes_processed>\n')
            f.write(f'    <patterns_found>{self.stats["patterns_found"]}</patterns_found>\n')
            f.write(f'    <processing_time>{self.stats["processing_time"]:.2f}</processing_time>\n')
            f.write('  </source>\n')
            f.write('</dfxml>\n')

        # Save JSON summary for easy parsing
        json_file = os.path.join(output_dir, "summary.json")
        summary_data = {
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'patterns': {name: len(matches) for name, matches in self.results.items()},
            'files_generated': list(self.results.keys())
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2)
        
        print(f"[INFO] Summary saved to: {json_file}")

    def run_extraction(self, input_file, output_dir):
        """Main extraction workflow"""
        print(f"[BULK-EXTRACTOR-PYTHON] Starting extraction...")
        print(f"[INFO] Input: {input_file}")
        print(f"[INFO] Output: {output_dir}")
        
        if not os.path.exists(input_file):
            print(f"[ERROR] Input file not found: {input_file}")
            return False
        
        # Process the file
        if not self.process_file(input_file):
            return False
        
        # Save results
        self.save_results(output_dir)
        
        # Print summary
        print(f"\n[SUMMARY] Extraction completed:")
        print(f"  Bytes processed: {self.stats['bytes_processed']:,}")
        print(f"  Patterns found: {self.stats['patterns_found']:,}")
        print(f"  Processing time: {self.stats['processing_time']:.2f} seconds")
        print(f"  Results saved in: {output_dir}")
        
        return True

def main():
    """Command line interface"""
    if len(sys.argv) < 3:
        print("Usage: python bulk_extractor.py <input_file> <output_dir>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2]
    
    extractor = BulkExtractorAlternative()
    success = extractor.run_extraction(input_file, output_dir)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()