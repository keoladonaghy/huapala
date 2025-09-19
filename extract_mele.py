#!/usr/bin/env python3
"""
Mele HTML Extraction Script

Extracts structured data from Hawaiian mele HTML files created by Claris Homepage 2.0
and outputs JSON format suitable for database import.

Usage: python extract_mele.py [input_file] [output_dir]
"""

import re
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import html


def clean_text(text):
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Convert HTML entities to Unicode first
    text = html.unescape(text)
    
    # Normalize diacriticals (basic conversion)
    replacements = {
        '&uuml;': 'ū',
        '&auml;': 'ā', 
        '&euml;': 'ē',
        '&iuml;': 'ī',
        '&ouml;': 'ō',
        '&ucirc;': 'û',
        '&acirc;': 'â'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Remove excessive whitespace but preserve line breaks for now
    text = re.sub(r'[ \t]+', ' ', text.strip())
    
    return text


def clean_text_preserve_lines(text):
    """Clean text while preserving line structure"""
    if not text:
        return ""
    
    text = html.unescape(text)
    
    # Normalize diacriticals
    replacements = {
        '&uuml;': 'ū', '&auml;': 'ā', '&euml;': 'ē',
        '&iuml;': 'ī', '&ouml;': 'ō', '&ucirc;': 'û', '&acirc;': 'â'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Split into lines and clean each line
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = re.sub(r'[ \t]+', ' ', line.strip())
        if line:  # Only keep non-empty lines
            cleaned_lines.append(line)
    
    return cleaned_lines


def normalize_id(title):
    """Create normalized ID from title"""
    if not title:
        return "unknown"
    
    # Remove diacriticals for ID
    id_text = title.lower()
    id_text = re.sub(r'[ʻ''`]', '', id_text)  # Remove okina variants
    id_text = re.sub(r'[āăâ]', 'a', id_text)
    id_text = re.sub(r'[ēĕê]', 'e', id_text)
    id_text = re.sub(r'[īĭî]', 'i', id_text)
    id_text = re.sub(r'[ōŏô]', 'o', id_text)
    id_text = re.sub(r'[ūŭû]', 'u', id_text)
    
    # Replace spaces and special chars with underscores
    id_text = re.sub(r'[^a-z0-9]', '_', id_text)
    id_text = re.sub(r'_+', '_', id_text)
    id_text = id_text.strip('_')
    
    return id_text


def extract_title_and_subtitle(soup):
    """Extract title, subtitle, and composer from header area"""
    title_info = {
        'hawaiian': '',
        'english': '',
        'alternate_titles': [],
        'composer': '',
        'subtitle': ''
    }
    
    # Look for title in HTML title tag first
    title_elem = soup.find('title')
    if title_elem:
        raw_title = clean_text(title_elem.text)
        if raw_title and not title_info['hawaiian']:
            title_info['hawaiian'] = raw_title
    
    # Look for main title in center tags or large fonts
    for elem in soup.find_all(['center', 'p', 'div']):
        if not elem:
            continue
            
        # Get all text content for this element
        full_text = clean_text(elem.get_text())
        
        # Check for title patterns in font tags
        font_tags = elem.find_all('font')
        for font in font_tags:
            size = font.get('size', '')
            if size in ['3', '+1', '4'] or 'size="3"' in str(font):
                potential_title = clean_text(font.get_text())
                
                # Skip very short or very long potential titles
                if potential_title and 3 <= len(potential_title) <= 50:
                    # If we don't have a title yet, use this
                    if not title_info['hawaiian']:
                        title_info['hawaiian'] = potential_title
                    # If this is different from current title, add as alternate
                    elif potential_title != title_info['hawaiian']:
                        if potential_title not in title_info['alternate_titles']:
                            title_info['alternate_titles'].append(potential_title)
        
        # Look for composer patterns
        composer_patterns = [
            r'-\s*(?:by\s+|music by\s+|words & music by\s+)?([^-\n(]+?)(?:\s*$|\s*\n)',
            r'(?:by|music by|words & music by)\s+([^-\n(]+?)(?:\s*$|\s*\n)',
        ]
        
        for pattern in composer_patterns:
            composer_match = re.search(pattern, full_text, re.IGNORECASE)
            if composer_match and not title_info['composer']:
                composer_candidate = clean_text(composer_match.group(1))
                # Filter out obvious non-composer text
                if composer_candidate and len(composer_candidate) < 50:
                    title_info['composer'] = composer_candidate
        
        # Look for English subtitle in parentheses
        subtitle_patterns = [
            r'\(([^)]+)\)',  # Basic parentheses
            r':\s*([^-\n]+?)(?:\s*-|\s*$)',  # After colon
        ]
        
        for pattern in subtitle_patterns:
            subtitle_match = re.search(pattern, full_text)
            if subtitle_match and not title_info['english']:
                subtitle_candidate = clean_text(subtitle_match.group(1))
                # Skip if it looks like a composer name or is too long
                if (subtitle_candidate and 
                    len(subtitle_candidate) > 2 and 
                    len(subtitle_candidate) < 50 and
                    subtitle_candidate != title_info['composer']):
                    title_info['english'] = subtitle_candidate
    
    return title_info


def extract_youtube_links(soup):
    """Extract YouTube links from the HTML"""
    links = []
    text = soup.get_text()
    
    # Look for YouTube URL patterns
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'https?://youtu\.be/[\w-]+',
        r'http://www\.youtube\.com/watch\?v=[\w-]+'
    ]
    
    for pattern in youtube_patterns:
        matches = re.findall(pattern, text)
        links.extend(matches)
    
    return list(set(links))  # Remove duplicates


def extract_source_info(soup):
    """Extract source and attribution information"""
    source_info = {
        'publication': '',
        'copyright': '',
        'translator': '',
        'hawaiian_editor': '',
        'source_editor': '',
        'additional_notes': ''
    }
    
    # Look for source information usually at bottom
    text = soup.get_text()
    
    # Find source patterns
    source_patterns = [
        r'Source:\s*([^\n]+)',
        r'Translated by\s+([^,\n]+)',
        r'Hawaiian Text edited by\s+([^,\n©]+)',
        r'©\s*(\d{4}[^,\n]*)',
        r'Copyright\s+([^,\n]+)'
    ]
    
    for pattern in source_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            found_text = clean_text(match.group(1))
            if 'Translated by' in pattern:
                source_info['translator'] = found_text
            elif 'Hawaiian Text edited by' in pattern:
                source_info['hawaiian_editor'] = found_text
            elif 'Source:' in pattern:
                source_info['publication'] = found_text
            elif '©' in pattern or 'Copyright' in pattern:
                source_info['copyright'] = found_text
    
    return source_info


def extract_lyrics_and_translation(soup):
    """Extract lyrics and translations from table structure"""
    verses = []
    
    # Find table with lyrics
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                # Assume first cell is Hawaiian, second is English
                hawaiian_cell = cells[0]
                english_cell = cells[1]
                
                # Get raw HTML to preserve <br> tags for line breaks
                hawaiian_html = str(hawaiian_cell)
                english_html = str(english_cell)
                
                # Replace <br> tags with newlines
                hawaiian_html = re.sub(r'<br[^>]*>', '\n', hawaiian_html, flags=re.IGNORECASE)
                english_html = re.sub(r'<br[^>]*>', '\n', english_html, flags=re.IGNORECASE)
                
                # Parse back to get text with preserved line breaks
                hawaiian_soup = BeautifulSoup(hawaiian_html, 'html.parser')
                english_soup = BeautifulSoup(english_html, 'html.parser')
                
                hawaiian_text_raw = hawaiian_soup.get_text()
                english_text_raw = english_soup.get_text()
                
                # Clean and split into lines
                hawaiian_lines = clean_text_preserve_lines(hawaiian_text_raw)
                english_lines = clean_text_preserve_lines(english_text_raw)
                
                # Skip if too little content
                if len(hawaiian_lines) < 2 and len(english_lines) < 2:
                    continue
                
                # Skip header rows (titles, etc)
                hawaiian_joined = ' '.join(hawaiian_lines)
                english_joined = ' '.join(english_lines)
                
                if len(hawaiian_joined) < 10:
                    continue
                
                # Try to separate verses within this cell by looking for verse breaks
                verse_sections = split_into_verses(hawaiian_lines, english_lines)
                
                for section in verse_sections:
                    h_lines = section['hawaiian_lines']
                    e_lines = section['english_lines']
                    
                    if not h_lines:
                        continue
                    
                    # Check for hui/chorus markers
                    verse_type = "verse"
                    label = ""
                    
                    first_line = h_lines[0] if h_lines else ""
                    if re.search(r'hui:', first_line, re.IGNORECASE):
                        verse_type = "hui"
                        label = "Hui:"
                        # Remove hui marker from first line
                        h_lines[0] = re.sub(r'hui:\s*', '', h_lines[0], flags=re.IGNORECASE).strip()
                        if not h_lines[0]:  # If line is now empty, remove it
                            h_lines = h_lines[1:]
                    elif re.search(r'chorus:', first_line, re.IGNORECASE):
                        verse_type = "hui"
                        label = "Chorus:"
                        h_lines[0] = re.sub(r'chorus:\s*', '', h_lines[0], flags=re.IGNORECASE).strip()
                        if not h_lines[0]:
                            h_lines = h_lines[1:]
                    
                    if h_lines:  # Only add if we have content
                        verse = {
                            'order': len(verses) + 1,
                            'type': verse_type,
                            'hawaiian_text': '\n'.join(h_lines),
                            'english_text': '\n'.join(e_lines),
                            'hawaiian_lines': h_lines,
                            'english_lines': e_lines
                        }
                        
                        if label:
                            verse['label'] = label
                        
                        verses.append(verse)
    
    return verses


def split_into_verses(hawaiian_lines, english_lines):
    """Split lines into separate verses based on blank lines or patterns"""
    sections = []
    current_h = []
    current_e = []
    e_index = 0
    
    for i, h_line in enumerate(hawaiian_lines):
        # Look for verse break indicators
        if (not h_line.strip() or 
            re.match(r'^\s*$', h_line) or
            (len(current_h) > 0 and 
             (re.search(r'hui:|chorus:', h_line, re.IGNORECASE) or
              # Look for verse number patterns
              re.match(r'^\d+\.?\s*', h_line.strip())))):
            
            # Save current section if it has content
            if current_h:
                sections.append({
                    'hawaiian_lines': current_h[:],
                    'english_lines': current_e[:]
                })
                current_h = []
                current_e = []
                e_index = 0
            
            # Don't skip the current line if it has content
            if h_line.strip():
                current_h.append(h_line)
                if e_index < len(english_lines):
                    current_e.append(english_lines[e_index])
                    e_index += 1
        else:
            current_h.append(h_line)
            if e_index < len(english_lines):
                current_e.append(english_lines[e_index])
                e_index += 1
    
    # Add the last section
    if current_h:
        sections.append({
            'hawaiian_lines': current_h,
            'english_lines': current_e
        })
    
    # If no clear verse breaks found, treat as one section
    if not sections:
        sections.append({
            'hawaiian_lines': hawaiian_lines,
            'english_lines': english_lines
        })
    
    return sections


def extract_mele_data(file_path):
    """Main extraction function"""
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract all components
    title_info = extract_title_and_subtitle(soup)
    youtube_links = extract_youtube_links(soup)
    source_info = extract_source_info(soup)
    verses = extract_lyrics_and_translation(soup)
    
    # Create structured output
    mele_data = {
        'id': normalize_id(title_info['hawaiian']),
        'title': {
            'hawaiian': title_info['hawaiian'],
            'english': title_info['english'],
            'normalized': normalize_id(title_info['hawaiian']),
            'alternate_titles': title_info['alternate_titles']
        },
        'attribution': {
            'composer': title_info['composer'],
            'lyricist': None,
            'translator': source_info['translator'],
            'hawaiian_editor': source_info['hawaiian_editor'],
            'source_editor': source_info['source_editor']
        },
        'content': {
            'verses': verses,
            'structure_notes': f"Extracted {len(verses)} sections"
        },
        'media': {
            'youtube_urls': youtube_links,
            'recordings': [],
            'sheet_music': []
        },
        'metadata': {
            'source_file': os.path.basename(file_path),
            'source_publication': source_info['publication'],
            'copyright': source_info['copyright'],
            'extraction_date': datetime.now().isoformat(),
            'processing_status': 'extracted',
            'raw_html_preserved': True
        },
        'classification': {
            'mele_type': [],
            'themes': [],
            'primary_location': '',
            'island': '',
            'cultural_elements': []
        }
    }
    
    return mele_data


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_mele.py [input_file_or_directory] [output_dir]")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('./extracted')
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Process files
    files_to_process = []
    
    if input_path.is_file():
        files_to_process = [input_path]
    elif input_path.is_dir():
        files_to_process = list(input_path.glob('*.txt'))
    else:
        print(f"Error: {input_path} not found")
        sys.exit(1)
    
    results = []
    
    for file_path in files_to_process:
        print(f"Processing: {file_path.name}")
        
        try:
            mele_data = extract_mele_data(file_path)
            
            # Write individual JSON file
            output_file = output_dir / f"{mele_data['id']}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(mele_data, f, indent=2, ensure_ascii=False)
            
            results.append(mele_data)
            print(f"  -> Extracted: {mele_data['title']['hawaiian']}")
            
        except Exception as e:
            print(f"  -> Error processing {file_path}: {e}")
    
    # Write summary file
    summary_file = output_dir / 'extraction_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_files_processed': len(results),
            'extraction_date': datetime.now().isoformat(),
            'files': [r['metadata']['source_file'] for r in results]
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nExtraction complete! Processed {len(results)} files.")
    print(f"Output directory: {output_dir}")


if __name__ == '__main__':
    main()