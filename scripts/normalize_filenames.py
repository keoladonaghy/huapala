#!/usr/bin/env python3
"""
Normalize source_html filenames according to rules:
- All letters lowercase
- Vowel macrons changed to plain vowels (ā→a, ē→e, ī→i, ō→o, ū→u)
- ʻOkina removed
- Spaces replaced with _
- .txt changed to .html
"""

import os
import re
import unicodedata

def normalize_filename(filename):
    """Normalize a filename according to the specified rules"""
    
    # Remove .txt extension first to work with base name
    if filename.endswith('.txt'):
        base_name = filename[:-4]
    else:
        base_name = filename
    
    # Convert to lowercase
    normalized = base_name.lower()
    
    # Remove ʻokina (U+02BB and other variants)
    okina_chars = ['\u02bb', '\u2018', '\u2019', '`', "'"]
    for okina in okina_chars:
        normalized = normalized.replace(okina, '')
    
    # Replace vowel macrons with plain vowels
    # Using Unicode normalization to handle composed characters
    macron_map = {
        'ā': 'a', 'ē': 'e', 'ī': 'i', 'ō': 'o', 'ū': 'u',
        'Ā': 'a', 'Ē': 'e', 'Ī': 'i', 'Ō': 'o', 'Ū': 'u'
    }
    
    for macron, plain in macron_map.items():
        normalized = normalized.replace(macron, plain)
    
    # Also handle decomposed Unicode (macron as combining character)
    normalized = unicodedata.normalize('NFD', normalized)
    # Remove combining macron (U+0304)
    normalized = ''.join(c for c in normalized if ord(c) != 0x0304)
    normalized = unicodedata.normalize('NFC', normalized)
    
    # Replace spaces with underscores
    normalized = normalized.replace(' ', '_')
    
    # Add .html extension
    normalized += '.html'
    
    return normalized

def main():
    source_dir = 'data/source_html'
    
    # Get all .txt files
    txt_files = [f for f in os.listdir(source_dir) if f.endswith('.txt')]
    
    print(f"Found {len(txt_files)} .txt files to normalize:")
    print()
    
    rename_mapping = {}
    
    for filename in txt_files:
        old_path = os.path.join(source_dir, filename)
        new_filename = normalize_filename(filename)
        new_path = os.path.join(source_dir, new_filename)
        
        rename_mapping[old_path] = new_path
        
        print(f"'{filename}' → '{new_filename}'")
    
    print()
    print("Proceed with renaming? (y/n): ", end="")
    choice = input().strip().lower()
    
    if choice == 'y':
        print()
        print("Renaming files...")
        
        for old_path, new_path in rename_mapping.items():
            try:
                os.rename(old_path, new_path)
                print(f"✅ Renamed: {os.path.basename(old_path)} → {os.path.basename(new_path)}")
            except Exception as e:
                print(f"❌ Error renaming {old_path}: {e}")
        
        print()
        print("Filename normalization complete!")
        
        # Show final directory listing
        print()
        print("Current .html files:")
        html_files = [f for f in os.listdir(source_dir) if f.endswith('.html')]
        for f in sorted(html_files):
            print(f"  {f}")
            
    else:
        print("Renaming cancelled.")

if __name__ == "__main__":
    main()