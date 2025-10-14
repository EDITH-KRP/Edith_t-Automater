#!/usr/bin/env python3
"""
Python-based Bulk Extractor Alternative
Extracts structured data from disk images without requiring the C++ bulk_extractor
"""

import os
import re
import sys
import mmap
import json
import hashlib
from datetime import datetime
from pathlib import Path

class BulkExtractorAlternative:
    def __init__(self):
        self.email_pattern = re.compile(rb'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.phone_pattern = re.compile(rb'(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}')
        self.url_pattern = re.compile(rb'https?://[^\s<>"]+')
        self.ip_pattern = re.compile(rb'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
        self.credit_card_pattern = re.compile(rb'\b4[0-9]{12}(?:[0-9]{3})?\b|\b5[1-5][0-9]{14}\b|\b3[47][0-9]{13}\b')
        self.ssn_pattern = re.compile(rb'\b[0-9]{3}-?[0-9]{2}-?[0-9]{4}\b')
        
        # Windows registry patterns
        self.registry_pattern = re.compile(rb'HKEY_[A-Z_]+\\[^\\]+(?:\\[^\\]+)*')
        
        # Common file signatures
        self.file_signatures = {
            b'\xFF\xD8\xFF': 'jpeg',
            b'\x89PNG\r\n\x1a\n': 'png',
            b'GIF87a': 'gif87a',
            b'GIF89a': 'gif89a',
            b'%PDF': 'pdf',
            b'PK\x03\x04': 'zip',
            b'PK\x05\x06': 'zip_empty',
            b'PK\x07\x08': 'zip_spanned',
            b'\x50\x4B\x03\x04': 'zip_office',
            b'RIFF': 'avi_wav',
            b'\x00\x00\x01\x00': 'ico',
            b'BM': 'bmp',
            b'\x1F\x8B\x08': 'gzip',
            b'\x42\x5A\x68': 'bzip2',
            b'\x7F\x45\x4C\x46': 'elf',
            b'MZ': 'exe',
            b'\xD0\xCF\x11\xE0': 'ole',
        }
        
    def run_extraction(self, input_file, output_dir):
        """Main extraction function"""
        print(f"🔍 Starting Python-based bulk extraction on: {os.path.basename(input_file)}")
        print(f"📁 Output directory: {output_dir}")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize results
        results = {
            'emails': set(),
            'phones': set(),
            'urls': set(),
            'ips': set(),
            'credit_cards': set(),
            'ssns': set(),
            'registry_keys': set(),
            'file_signatures': [],
            'metadata': {
                'input_file': input_file,
                'file_size': os.path.getsize(input_file),
                'extraction_time': datetime.now().isoformat(),
                'chunk_size': 1024 * 1024,  # 1MB chunks
            }
        }
        
        try:
            file_size = os.path.getsize(input_file)
            processed_bytes = 0
            
            print(f"📊 File size: {file_size / (1024*1024*1024):.2f} GB")
            print("🔄 Processing chunks...")
            
            with open(input_file, 'rb') as f:
                # Use memory mapping for large files
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    chunk_size = 1024 * 1024  # 1MB chunks
                    position = 0
                    
                    while position < len(mm):
                        # Read chunk with overlap to catch patterns spanning chunks
                        overlap = 1024  # 1KB overlap
                        start = max(0, position - overlap)
                        end = min(len(mm), position + chunk_size + overlap)
                        chunk = mm[start:end]
                        
                        # Extract patterns from chunk
                        self._extract_from_chunk(chunk, results, start)
                        
                        # Update progress
                        processed_bytes = min(position + chunk_size, file_size)
                        progress = (processed_bytes / file_size) * 100
                        if position % (chunk_size * 50) == 0:  # Print every 50MB
                            print(f"    Progress: {progress:.1f}% ({processed_bytes / (1024*1024):.1f} MB)")
                        
                        position += chunk_size
                        
                        # Safety limit for very large files
                        if position > 10 * 1024 * 1024 * 1024:  # 10GB limit
                            print("    ⚠️  Reached 10GB processing limit")
                            break
            
            # Save results
            self._save_results(results, output_dir)
            
            print(f"✅ Extraction completed successfully!")
            print(f"📋 Summary:")
            print(f"    📧 Emails found: {len(results['emails'])}")
            print(f"    📞 Phone numbers: {len(results['phones'])}")
            print(f"    🌐 URLs found: {len(results['urls'])}")
            print(f"    🌍 IP addresses: {len(results['ips'])}")
            print(f"    💳 Credit cards: {len(results['credit_cards'])}")
            print(f"    🆔 SSNs found: {len(results['ssns'])}")
            print(f"    🗂️  Registry keys: {len(results['registry_keys'])}")
            print(f"    📄 File signatures: {len(results['file_signatures'])}")
            
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            raise
    
    def _extract_from_chunk(self, chunk, results, offset):
        """Extract patterns from a chunk of data"""
        # Extract emails
        emails = self.email_pattern.findall(chunk)
        for email in emails:
            try:
                email_str = email.decode('utf-8', errors='ignore')
                if len(email_str) > 5 and '@' in email_str:
                    results['emails'].add(email_str)
            except:
                pass
        
        # Extract phone numbers
        phones = self.phone_pattern.findall(chunk)
        for phone in phones:
            try:
                phone_str = phone.decode('utf-8', errors='ignore').strip()
                if len(phone_str) >= 10:
                    results['phones'].add(phone_str)
            except:
                pass
        
        # Extract URLs
        urls = self.url_pattern.findall(chunk)
        for url in urls:
            try:
                url_str = url.decode('utf-8', errors='ignore')
                if len(url_str) > 10:
                    results['urls'].add(url_str)
            except:
                pass
        
        # Extract IP addresses
        ips = self.ip_pattern.findall(chunk)
        for ip in ips:
            try:
                ip_str = ip.decode('utf-8', errors='ignore')
                if self._is_valid_ip(ip_str):
                    results['ips'].add(ip_str)
            except:
                pass
        
        # Extract credit card numbers (basic pattern)
        cards = self.credit_card_pattern.findall(chunk)
        for card in cards:
            try:
                card_str = card.decode('utf-8', errors='ignore')
                results['credit_cards'].add(card_str)
            except:
                pass
        
        # Extract SSNs
        ssns = self.ssn_pattern.findall(chunk)
        for ssn in ssns:
            try:
                ssn_str = ssn.decode('utf-8', errors='ignore')
                results['ssns'].add(ssn_str)
            except:
                pass
        
        # Extract registry keys
        registry = self.registry_pattern.findall(chunk)
        for reg in registry:
            try:
                reg_str = reg.decode('utf-8', errors='ignore')
                results['registry_keys'].add(reg_str)
            except:
                pass
        
        # Check for file signatures
        for signature, file_type in self.file_signatures.items():
            pos = 0
            while True:
                pos = chunk.find(signature, pos)
                if pos == -1:
                    break
                results['file_signatures'].append({
                    'offset': offset + pos,
                    'type': file_type,
                    'signature': signature.hex()
                })
                pos += len(signature)
    
    def _is_valid_ip(self, ip_str):
        """Validate IP address format"""
        parts = ip_str.split('.')
        if len(parts) != 4:
            return False
        try:
            for part in parts:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            return True
        except ValueError:
            return False
    
    def _save_results(self, results, output_dir):
        """Save extraction results to files"""
        # Convert sets to lists for JSON serialization
        json_results = {}
        for key, value in results.items():
            if isinstance(value, set):
                json_results[key] = sorted(list(value))
            else:
                json_results[key] = value
        
        # Save main results as JSON
        with open(os.path.join(output_dir, 'bulk_extractor_results.json'), 'w') as f:
            json.dump(json_results, f, indent=2)
        
        # Save individual category files (bulk_extractor format)
        if results['emails']:
            with open(os.path.join(output_dir, 'email.txt'), 'w') as f:
                f.write("# Email addresses found\n")
                for email in sorted(results['emails']):
                    f.write(f"{email}\n")
        
        if results['phones']:
            with open(os.path.join(output_dir, 'telephone.txt'), 'w') as f:
                f.write("# Phone numbers found\n")
                for phone in sorted(results['phones']):
                    f.write(f"{phone}\n")
        
        if results['urls']:
            with open(os.path.join(output_dir, 'url.txt'), 'w') as f:
                f.write("# URLs found\n")
                for url in sorted(results['urls']):
                    f.write(f"{url}\n")
        
        if results['ips']:
            with open(os.path.join(output_dir, 'ip.txt'), 'w') as f:
                f.write("# IP addresses found\n")
                for ip in sorted(results['ips']):
                    f.write(f"{ip}\n")
        
        if results['credit_cards']:
            with open(os.path.join(output_dir, 'ccn.txt'), 'w') as f:
                f.write("# Credit card numbers found\n")
                for ccn in sorted(results['credit_cards']):
                    f.write(f"{ccn}\n")
        
        if results['registry_keys']:
            with open(os.path.join(output_dir, 'winprefetch.txt'), 'w') as f:
                f.write("# Windows registry keys found\n")
                for reg in sorted(results['registry_keys']):
                    f.write(f"{reg}\n")
        
        if results['file_signatures']:
            with open(os.path.join(output_dir, 'carved_files.txt'), 'w') as f:
                f.write("# File signatures found\n")
                f.write("# Format: offset:type:signature\n")
                for sig in results['file_signatures']:
                    f.write(f"{sig['offset']}:{sig['type']}:{sig['signature']}\n")
        
        # Create summary report
        with open(os.path.join(output_dir, 'report.xml'), 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<bulk_extractor_report>\n')
            f.write(f'  <input_file>{results["metadata"]["input_file"]}</input_file>\n')
            f.write(f'  <file_size>{results["metadata"]["file_size"]}</file_size>\n')
            f.write(f'  <extraction_time>{results["metadata"]["extraction_time"]}</extraction_time>\n')
            f.write('  <features>\n')
            f.write(f'    <emails count="{len(results["emails"])}"/>\n')
            f.write(f'    <phones count="{len(results["phones"])}"/>\n')
            f.write(f'    <urls count="{len(results["urls"])}"/>\n')
            f.write(f'    <ips count="{len(results["ips"])}"/>\n')
            f.write(f'    <credit_cards count="{len(results["credit_cards"])}"/>\n')
            f.write(f'    <ssns count="{len(results["ssns"])}"/>\n')
            f.write(f'    <registry_keys count="{len(results["registry_keys"])}"/>\n')
            f.write(f'    <file_signatures count="{len(results["file_signatures"])}"/>\n')
            f.write('  </features>\n')
            f.write('</bulk_extractor_report>\n')


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python bulk_extractor.py <input_file> <output_dir>")
        sys.exit(1)
    
    extractor = BulkExtractorAlternative()
    extractor.run_extraction(sys.argv[1], sys.argv[2])