#!/usr/bin/env python3
"""
Enhanced HTML Parser for Huapala Songs

Automatically extracts songs from raw HTML files without requiring cleaned format.
Identifies table structures, extracts titles/composers, and parses verses/chorus.
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from bs4 import BeautifulSoup
from datetime import datetime

@dataclass
class SongLine:
    hawaiian_text: str = ""
    english_text: str = ""
    line_number: int = 0
    
@dataclass
class SongSection:
    section_type: str = "verse"  # verse, chorus, hui
    number: int = 1
    lines: List[SongLine] = field(default_factory=list)

@dataclass
class ParsedSong:
    title: str = ""
    composer: str = ""
    translator: str = ""
    source_info: str = ""
    sections: List[SongSection] = field(default_factory=list)

class EnhancedHuapalaParser:
    """Enhanced parser that handles raw HTML files directly"""
    
    def __init__(self):
        self.title_patterns = [
            r'<font[^>]*size="3"[^>]*>([^<]+)</font>',
            r'<title>([^<]+)</title>',
            r'<h1[^>]*>([^<]+)</h1>',
            r'<h2[^>]*>([^<]+)</h2>'
        ]
        
        self.composer_patterns = [
            r'(?:-\s*)?(?:music\s+by|composed\s+by|by)\s+([^<\n\r]+?)(?:\s*<|$)',
            r'(?:lyrics?\s+by\s+[^,]+,?\s*)?music\s+by\s+([^<\n\r]+?)(?:\s*<|$)',
            r'Words\s+by\s+[^,]+,?\s*(?:music\s+)?by\s+([^<\n\r]+?)(?:\s*<|$)',
            r'<font[^>]*>([^<]+)</font>\s*(?:-|\u2013)',
            r'-\s*([^<\n\r]+?)(?:\s*<br|$)'
        ]
        
        self.translator_patterns = [
            r'(?:translated\s+by|translation\s+by)\s+([^<\n\r]+?)(?:\s*<|$)',
            r'(?:Hawaiian\s+)?[Tt]ext\s+edited\s+by\s+([^<\n\r]+?)(?:\s*<|$)'
        ]
        
    def parse_file(self, file_path: str) -> Tuple[ParsedSong, dict]:
        """Parse a raw HTML file and extract song data"""
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        song = ParsedSong()
        
        # Extract title and composer
        song.title, song.composer = self._extract_title_and_composer(html_content, soup)
        song.translator = self._extract_translator(html_content)
        song.source_info = self._extract_source_info(soup)
        
        # Find and parse the main lyrics table
        lyrics_table = self._find_lyrics_table(soup)
        if lyrics_table:
            song.sections = self._parse_lyrics_table(lyrics_table)
        else:
            # Fallback: try to find lyrics in any table or div structure
            song.sections = self._parse_alternative_structure(soup)
        
        # Generate validation metadata
        validation_result = self._generate_validation_result(song)
        
        return song, validation_result
    
    def _extract_title_and_composer(self, html_content: str, soup: BeautifulSoup) -> Tuple[str, str]:
        """Extract song title and composer from HTML"""
        title = ""
        composer = ""
        
        # Look for title in center tags or font size="3"
        center_tags = soup.find_all('center')
        for center in center_tags:
            # Look for the main title (usually in font size="3")
            title_font = center.find('font', size="3")
            if title_font:
                title_text = title_font.get_text(strip=True)
                if title_text and len(title_text) > 2:  # Reasonable title length
                    title = title_text
                    
                    # Look for composer info in the same center tag
                    # Usually follows the title with a dash or "by"
                    full_text = center.get_text(separator=' ', strip=True)
                    
                    # Try to extract composer from the full text
                    for pattern in self.composer_patterns:
                        match = re.search(pattern, full_text, re.IGNORECASE)
                        if match:
                            composer = match.group(1).strip()
                            break
                    
                    break
        
        # If no title found, try title tag
        if not title:
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)
        
        # Clean up title and composer
        title = self._clean_text(title)
        composer = self._clean_text(composer)
        
        return title, composer
    
    def _extract_translator(self, html_content: str) -> str:
        """Extract translator information"""
        for pattern in self.translator_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return self._clean_text(match.group(1))
        return ""
    
    def _extract_source_info(self, soup: BeautifulSoup) -> str:
        """Extract source information from the bottom of the page"""
        # Look for source info in the last table row or at the bottom
        source_patterns = [
            'source:',
            'recorded by',
            'copyright',
            'composed',
            'mana collection',
            'pandanus club'
        ]
        
        # Check last table rows
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) >= 2:  # Check last row
                last_row = rows[-1]
                text = last_row.get_text(separator=' ', strip=True).lower()
                if any(pattern in text for pattern in source_patterns):
                    return self._clean_text(last_row.get_text(separator=' ', strip=True))
        
        return ""
    
    def _find_lyrics_table(self, soup: BeautifulSoup) -> Optional:
        """Find the main table containing lyrics in 2-column format"""
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            # Look for a table with at least 2 rows and 2 columns
            if len(rows) < 2:
                continue
                
            # Check if any row has 2 cells with substantial text content
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) == 2:
                    cell1_text = cells[0].get_text(strip=True)
                    cell2_text = cells[1].get_text(strip=True)
                    
                    # If both cells have Hawaiian/English text (substantial content)
                    if (len(cell1_text) > 20 and len(cell2_text) > 20 and
                        '<br>' in str(cells[0]) and '<br>' in str(cells[1])):
                        return table
        
        return None
    
    def _parse_lyrics_table(self, table) -> List[SongSection]:
        """Parse the main lyrics table into sections"""
        rows = table.find_all('tr')
        sections = []
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            
            # Skip header rows or rows without 2 columns
            if len(cells) != 2:
                continue
                
            # Skip rows that are clearly metadata (too short)
            cell1_text = cells[0].get_text(strip=True)
            cell2_text = cells[1].get_text(strip=True)
            
            if len(cell1_text) < 20 or len(cell2_text) < 20:
                continue
            
            # Parse this row as lyrics content
            section_data = self._parse_lyrics_cells(cells[0], cells[1])
            if section_data:
                sections.extend(section_data)
        
        return sections
    
    def _parse_lyrics_cells(self, hawaiian_cell, english_cell) -> List[SongSection]:
        """Parse Hawaiian and English cells into song sections"""
        
        # Get HTML content to preserve <br> tags
        hawaiian_html = str(hawaiian_cell)
        english_html = str(english_cell)
        
        # Split by paragraph breaks and <br> tags
        hawaiian_blocks = self._split_into_blocks(hawaiian_html)
        english_blocks = self._split_into_blocks(english_html)
        
        sections = []
        
        # Process each block as a potential section
        max_blocks = max(len(hawaiian_blocks), len(english_blocks))
        
        for i in range(max_blocks):
            h_block = hawaiian_blocks[i] if i < len(hawaiian_blocks) else ""
            e_block = english_blocks[i] if i < len(english_blocks) else ""
            
            if not h_block.strip() and not e_block.strip():
                continue
            
            # Determine section type
            section_type = "verse"
            section_number = len([s for s in sections if s.section_type == "verse"]) + 1
            
            # Check for chorus indicators
            if ("hui:" in h_block.lower() or "chorus:" in e_block.lower() or
                any(indicator in h_block.lower() for indicator in ["hui:", "chorus"])):
                section_type = "chorus"
                section_number = 1
            
            # Create section
            section = SongSection(
                section_type=section_type,
                number=section_number
            )
            
            # Parse lines within this section
            h_lines = self._extract_lines(h_block)
            e_lines = self._extract_lines(e_block)
            
            # Align lines
            max_lines = max(len(h_lines), len(e_lines))
            for j in range(max_lines):
                h_text = h_lines[j] if j < len(h_lines) else ""
                e_text = e_lines[j] if j < len(e_lines) else ""
                
                # Skip empty lines
                if not h_text.strip() and not e_text.strip():
                    continue
                
                line = SongLine(
                    hawaiian_text=h_text.strip(),
                    english_text=e_text.strip(),
                    line_number=len(section.lines) + 1
                )
                section.lines.append(line)
            
            if section.lines:  # Only add sections with content
                sections.append(section)
        
        return sections
    
    def _split_into_blocks(self, html_content: str) -> List[str]:
        """Split HTML content into logical blocks (verses/chorus)"""
        
        # Remove HTML tags but keep <br> as markers
        html_content = re.sub(r'<(?!br\s*/?>)[^>]+>', ' ', html_content)
        
        # Split on double <br> or <p> tags (verse separators)
        blocks = re.split(r'<br\s*/?>[\s\n]*<br\s*/?>|<p[^>]*>|</p>', html_content, flags=re.IGNORECASE)
        
        # Clean up blocks
        cleaned_blocks = []
        for block in blocks:
            block = re.sub(r'<br\s*/?>', '\n', block, flags=re.IGNORECASE)
            block = self._clean_text(block)
            if block.strip():
                cleaned_blocks.append(block)
        
        return cleaned_blocks
    
    def _extract_lines(self, block_text: str) -> List[str]:
        """Extract individual lines from a text block"""
        # Split on line breaks
        lines = re.split(r'\n|<br\s*/?>', block_text, flags=re.IGNORECASE)
        
        # Clean and filter lines
        cleaned_lines = []
        for line in lines:
            line = self._clean_text(line)
            if line.strip() and not self._is_header_line(line):
                cleaned_lines.append(line)
        
        return cleaned_lines
    
    def _is_header_line(self, line: str) -> bool:
        """Check if a line is a header (Hui:, Chorus:, etc.) rather than lyrics"""
        line_lower = line.lower().strip()
        headers = ['hui:', 'chorus:', 'verse', 'bridge:', 'outro:']
        return any(line_lower.startswith(header) for header in headers)
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""
        
        # Remove HTML entities and extra whitespace
        text = re.sub(r'&[a-zA-Z0-9]+;', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove common artifacts
        text = re.sub(r'^[-\s]*', '', text)  # Leading dashes
        text = re.sub(r'[\s]*$', '', text)   # Trailing spaces
        
        return text
    
    def _parse_alternative_structure(self, soup: BeautifulSoup) -> List[SongSection]:
        """Fallback parser for non-standard structures"""
        # This is a simplified fallback - in practice, you'd implement
        # additional parsing strategies here
        return []
    
    def _generate_validation_result(self, song: ParsedSong) -> dict:
        """Generate validation metadata"""
        total_lines = sum(len(section.lines) for section in song.sections)
        
        # Simple quality score based on completeness
        quality_score = 0
        if song.title: quality_score += 20
        if song.composer: quality_score += 20
        if song.sections: quality_score += 30
        if total_lines > 5: quality_score += 20
        if any(section.section_type == "chorus" for section in song.sections): quality_score += 10
        
        return {
            "quality_score": quality_score,
            "total_sections": len(song.sections),
            "total_lines": total_lines,
            "has_chorus": any(section.section_type == "chorus" for section in song.sections),
            "parsing_method": "enhanced_html_parser",
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_jsonb_structure(self, song: ParsedSong) -> dict:
        """Generate the JSONB structure for database storage"""
        sections = []
        
        for i, section in enumerate(song.sections):
            section_data = {
                "id": f"{section.section_type[0]}{section.number}",
                "type": section.section_type,
                "number": section.number,
                "order": i + 1,
                "lines": []
            }
            
            for j, line in enumerate(section.lines):
                line_data = {
                    "id": f"{section_data['id']}.{j+1}",
                    "line_number": j + 1,
                    "hawaiian_text": line.hawaiian_text,
                    "english_text": line.english_text,
                    "is_bilingual": bool(line.hawaiian_text and line.english_text)
                }
                section_data["lines"].append(line_data)
            
            sections.append(section_data)
        
        return {
            "sections": sections,
            "metadata": {
                "total_sections": len(sections),
                "total_lines": sum(len(section["lines"]) for section in sections),
                "has_chorus": any(section["type"] == "chorus" for section in sections),
                "last_updated": datetime.now().isoformat()
            }
        }

def test_parser():
    """Test the enhanced parser on sample files"""
    parser = EnhancedHuapalaParser()
    
    test_files = [
        "data/source_html/E Waianae.txt",
        "data/source_html/Pili Mau Me Oe.txt"
    ]
    
    for file_path in test_files:
        if Path(file_path).exists():
            print(f"\n🔍 Testing: {file_path}")
            try:
                song, validation = parser.parse_file(file_path)
                print(f"   Title: {song.title}")
                print(f"   Composer: {song.composer}")
                print(f"   Sections: {len(song.sections)}")
                print(f"   Quality Score: {validation.get('quality_score', 0)}")
                
                # Show first few lines
                if song.sections:
                    first_section = song.sections[0]
                    print(f"   First section ({first_section.section_type}):")
                    for line in first_section.lines[:2]:
                        print(f"     H: {line.hawaiian_text[:50]}...")
                        print(f"     E: {line.english_text[:50]}...")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_parser()