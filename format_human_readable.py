#!/usr/bin/env python3
"""
Human Readable Formatter for Mele JSON Files

Converts structured JSON mele data back to human-readable text format
with clear data type labels for review and editing.

Usage: python format_human_readable.py [input_dir] [output_dir]
"""

import json
import os
import sys
from pathlib import Path


def format_mele_to_text(mele_data):
    """Convert JSON mele data to human-readable text format"""
    
    lines = []
    
    # Header with data type labels
    lines.append("=" * 80)
    lines.append("MELE DATA - HUMAN READABLE FORMAT")
    lines.append("=" * 80)
    lines.append("")
    
    # ID
    lines.append("[DATA TYPE: INTERNAL_ID]")
    lines.append(f"ID: {mele_data.get('id', 'N/A')}")
    lines.append("")
    
    # Title Information
    lines.append("[DATA TYPE: TITLE_INFORMATION]")
    title = mele_data.get('title', {})
    lines.append(f"Hawaiian Title: {title.get('hawaiian', 'N/A')}")
    if title.get('english'):
        lines.append(f"English Title: {title.get('english', 'N/A')}")
    if title.get('alternate_titles'):
        lines.append(f"Alternative Titles: {', '.join(title.get('alternate_titles', []))}")
    lines.append("")
    
    # Attribution
    lines.append("[DATA TYPE: ATTRIBUTION]")
    attribution = mele_data.get('attribution', {})
    
    if attribution.get('composer'):
        lines.append(f"Composer: {attribution.get('composer', 'N/A')}")
    if attribution.get('lyricist'):
        lines.append(f"Lyricist: {attribution.get('lyricist', 'N/A')}")
    if attribution.get('translator'):
        lines.append(f"Translator: {attribution.get('translator', 'N/A')}")
    if attribution.get('hawaiian_editor'):
        lines.append(f"Hawaiian Text Editor: {attribution.get('hawaiian_editor', 'N/A')}")
    if attribution.get('source_editor'):
        lines.append(f"Source Editor: {attribution.get('source_editor', 'N/A')}")
    
    # Add empty line only if we had attribution data
    if any([attribution.get('composer'), attribution.get('lyricist'), 
            attribution.get('translator'), attribution.get('hawaiian_editor'), 
            attribution.get('source_editor')]):
        lines.append("")
    
    # Content - Hawaiian Text
    lines.append("[DATA TYPE: HAWAIIAN_LYRICS]")
    content = mele_data.get('content', {})
    verses = content.get('verses', [])
    
    for verse in verses:
        verse_type = verse.get('type', 'verse')
        order = verse.get('order', 0)
        
        # Add verse header
        if verse_type == 'hui':
            label = verse.get('label', 'Hui:')
            lines.append(f"{label}")
        else:
            lines.append(f"Verse {order}:")
        
        # Add Hawaiian text
        hawaiian_text = verse.get('hawaiian_text', '')
        if hawaiian_text:
            lines.append(hawaiian_text)
        lines.append("")
    
    # Content - English Translation
    lines.append("[DATA TYPE: ENGLISH_TRANSLATION]")
    
    for verse in verses:
        verse_type = verse.get('type', 'verse')
        order = verse.get('order', 0)
        
        # Add verse header
        if verse_type == 'hui':
            label = verse.get('label', 'Hui:')
            lines.append(f"{label} (Translation)")
        else:
            lines.append(f"Verse {order}: (Translation)")
        
        # Add English text
        english_text = verse.get('english_text', '')
        if english_text:
            lines.append(english_text)
        lines.append("")
    
    # Media Links
    media = mele_data.get('media', {})
    youtube_urls = media.get('youtube_urls', [])
    
    if youtube_urls:
        lines.append("[DATA TYPE: MEDIA_LINKS]")
        for i, url in enumerate(youtube_urls, 1):
            lines.append(f"YouTube Link {i}: {url}")
        lines.append("")
    
    # Source and Publication Information
    lines.append("[DATA TYPE: SOURCE_INFORMATION]")
    metadata = mele_data.get('metadata', {})
    
    if metadata.get('source_publication'):
        lines.append(f"Source Publication: {metadata.get('source_publication', 'N/A')}")
    if metadata.get('copyright'):
        lines.append(f"Copyright: {metadata.get('copyright', 'N/A')}")
    if metadata.get('source_file'):
        lines.append(f"Original File: {metadata.get('source_file', 'N/A')}")
    
    lines.append("")
    
    # Classification (if any data exists)
    classification = mele_data.get('classification', {})
    has_classification = any([
        classification.get('mele_type'),
        classification.get('themes'),
        classification.get('primary_location'),
        classification.get('island'),
        classification.get('cultural_elements')
    ])
    
    if has_classification:
        lines.append("[DATA TYPE: CLASSIFICATION]")
        
        if classification.get('mele_type'):
            lines.append(f"Mele Type: {', '.join(classification.get('mele_type', []))}")
        if classification.get('themes'):
            lines.append(f"Themes: {', '.join(classification.get('themes', []))}")
        if classification.get('primary_location'):
            lines.append(f"Primary Location: {classification.get('primary_location', 'N/A')}")
        if classification.get('island'):
            lines.append(f"Island: {classification.get('island', 'N/A')}")
        if classification.get('cultural_elements'):
            lines.append(f"Cultural Elements: {', '.join(classification.get('cultural_elements', []))}")
        
        lines.append("")
    
    # Processing Information
    lines.append("[DATA TYPE: PROCESSING_METADATA]")
    lines.append(f"Extraction Date: {metadata.get('extraction_date', 'N/A')}")
    lines.append(f"Processing Status: {metadata.get('processing_status', 'N/A')}")
    
    # Structure notes
    if content.get('structure_notes'):
        lines.append(f"Structure Notes: {content.get('structure_notes', 'N/A')}")
    
    lines.append("")
    lines.append("=" * 80)
    lines.append("END OF MELE DATA")
    lines.append("=" * 80)
    
    return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python format_human_readable.py [input_dir] [output_dir]")
        sys.exit(1)
    
    input_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('./human_readable')
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Find all JSON files
    json_files = list(input_dir.glob('*.json'))
    
    # Filter out summary files
    mele_files = [f for f in json_files if 'summary' not in f.name.lower()]
    
    processed_count = 0
    
    for json_file in mele_files:
        print(f"Processing: {json_file.name}")
        
        try:
            # Load JSON data
            with open(json_file, 'r', encoding='utf-8') as f:
                mele_data = json.load(f)
            
            # Format to human readable
            formatted_text = format_mele_to_text(mele_data)
            
            # Create output filename
            base_name = json_file.stem
            output_file = output_dir / f"{base_name}.txt"
            
            # Write formatted text
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_text)
            
            processed_count += 1
            title = mele_data.get('title', {}).get('hawaiian', 'Unknown')
            print(f"  -> Created: {output_file.name} ({title})")
            
        except Exception as e:
            print(f"  -> Error processing {json_file}: {e}")
    
    print(f"\nFormatting complete! Processed {processed_count} files.")
    print(f"Output directory: {output_dir}")


if __name__ == '__main__':
    main()