#!/usr/bin/env python3
"""
Raw HTML Parser for Huapala Songs (No External Dependencies)

Automatically extracts songs from raw HTML files without requiring cleaned format.
Uses only standard library modules.
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import datetime
import html

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

class RawHtmlParser:
    """Enhanced parser that handles raw HTML files using only standard library"""
    
    def __init__(self):
        self.title_patterns = [
            r'<font[^>]*size=["\']?3["\']?[^>]*>([^<]+)</font>',
            r'<title>([^<]+)</title>',
            r'<h[123][^>]*>([^<]+)</h[123]>'
        ]
        
        self.composer_patterns = [
            r'(?:-\s*)?(?:music\s+by|composed\s+by|by)\s+([^<\n\r]+?)(?:\s*<|$)',
            r'(?:lyrics?\s+by\s+[^,]+,?\s*)?music\s+by\s+([^<\n\r]+?)(?:\s*<|$)',
            r'Words\s+by\s+[^,]+,?\s*(?:music\s+by\s+)?([^<\n\r]+?)(?:\s*<|$)',
            r'-\s*([^<\n\r]+?)(?:\s*<br|$)'
        ]
        
    def parse_file(self, file_path: str) -> Tuple[ParsedSong, dict]:
        """Parse a raw HTML file and extract song data"""
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
        
        song = ParsedSong()
        
        # Extract basic metadata
        song.title, song.composer = self._extract_title_and_composer(html_content)
        song.translator = self._extract_translator(html_content)
        song.source_info = self._extract_source_info(html_content)
        
        # Find and parse the main lyrics table
        song.sections = self._parse_lyrics_table(html_content)
        
        # Generate validation metadata
        validation_result = self._generate_validation_result(song)
        
        return song, validation_result
    
    def _extract_title_and_composer(self, html_content: str) -> Tuple[str, str]:
        """Extract song title and composer from HTML"""
        title = ""
        composer = ""
        
        # Look for title in font size="3"
        for pattern in self.title_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
            if match:
                title = self._clean_text(match.group(1))
                if len(title) > 2:  # Reasonable title length
                    break
        
        # Look for composer in the same area as title
        # Find content around the title
        if title:
            title_pos = html_content.lower().find(title.lower())
            if title_pos > -1:
                # Look in a window around the title
                start = max(0, title_pos - 200)
                end = min(len(html_content), title_pos + len(title) + 300)
                title_area = html_content[start:end]
                
                for pattern in self.composer_patterns:
                    match = re.search(pattern, title_area, re.IGNORECASE)
                    if match:
                        composer = self._clean_text(match.group(1))
                        break
        
        return title, composer
    
    def _extract_translator(self, html_content: str) -> str:
        """Extract translator information"""
        translator_patterns = [
            r'(?:translated\s+by|translation\s+by)\s+([^<\n\r]+?)(?:\s*<|$)',
            r'(?:Hawaiian\s+)?[Tt]ext\s+edited\s+by\s+([^<\n\r]+?)(?:\s*<|$)'
        ]
        
        for pattern in translator_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return self._clean_text(match.group(1))
        return ""
    
    def _extract_source_info(self, html_content: str) -> str:
        """Extract source information"""
        # Look for source info near the end
        source_patterns = [
            r'[Ss]ource:\s*([^<\n\r]+?)(?:\s*<|$)',
            r'[Rr]ecorded\s+by\s+([^<\n\r]+?)(?:\s*<|$)',
            r'[Cc]opyright\s+([^<\n\r]+?)(?:\s*<|$)',
            r'([^<\n\r]*[Pp]andanus\s+[Cc]lub[^<\n\r]*)(?:\s*<|$)',
            r'([^<\n\r]*[Mm]ana\s+[Cc]ollection[^<\n\r]*)(?:\s*<|$)'
        ]
        
        for pattern in source_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return self._clean_text(match.group(1))
        
        return ""
    
    def _parse_lyrics_table(self, html_content: str) -> List[SongSection]:
        """Parse the lyrics table from HTML"""
        
        # Find table with lyrics (2-column structure)
        table_pattern = r'<table[^>]*>(.*?)</table>'
        tables = re.findall(table_pattern, html_content, re.IGNORECASE | re.DOTALL)
        
        for table_content in tables:
            # Find rows with 2 cells containing substantial lyrics
            row_pattern = r'<tr[^>]*>(.*?)</tr>'
            rows = re.findall(row_pattern, table_content, re.IGNORECASE | re.DOTALL)
            
            for row in rows:
                # Find cells
                cell_pattern = r'<td[^>]*>(.*?)</td>'
                cells = re.findall(cell_pattern, row, re.IGNORECASE | re.DOTALL)
                
                if len(cells) == 2:
                    cell1_text = self._strip_html(cells[0])
                    cell2_text = self._strip_html(cells[1])
                    
                    # Check if this looks like lyrics (has line breaks and substantial content)
                    if (len(cell1_text) > 30 and len(cell2_text) > 30 and
                        '<br' in cells[0].lower() and '<br' in cells[1].lower()):
                        
                        # This looks like our lyrics table
                        return self._parse_lyrics_cells(cells[0], cells[1])
        
        return []
    
    def _parse_lyrics_cells(self, hawaiian_html: str, english_html: str) -> List[SongSection]:
        """Parse Hawaiian and English cells into song sections"""
        
        # Extract text with line breaks preserved
        h_text = self._extract_text_with_breaks(hawaiian_html)
        e_text = self._extract_text_with_breaks(english_html)
        
        # Split into lines
        h_lines = [line.strip() for line in h_text.split('\n') if line.strip()]
        e_lines = [line.strip() for line in e_text.split('\n') if line.strip()]
        
        sections = []
        current_section = None
        verse_count = 0
        
        # Process line by line to identify sections
        max_lines = max(len(h_lines), len(e_lines))
        i = 0
        
        while i < max_lines:
            h_line = h_lines[i] if i < len(h_lines) else ""
            e_line = e_lines[i] if i < len(e_lines) else ""
            
            # Skip completely empty lines
            if not h_line and not e_line:
                i += 1
                continue
            
            # Check for section markers (Hui:, Chorus:)
            if self._is_section_header(h_line) or self._is_section_header(e_line):
                # Finalize current section if it exists
                if current_section and current_section.lines:
                    sections.append(current_section)
                
                # Start new chorus section
                current_section = SongSection(
                    section_type="chorus",
                    number=1
                )
                i += 1
                continue
            
            # If no current section, start a new verse
            if not current_section:
                verse_count += 1
                current_section = SongSection(
                    section_type="verse",
                    number=verse_count
                )
            
            # Add line to current section
            line = SongLine(
                hawaiian_text=h_line,
                english_text=e_line,
                line_number=len(current_section.lines) + 1
            )
            current_section.lines.append(line)
            
            # Check if we should end this section (look ahead for breaks)
            if i + 1 < max_lines:
                # Look for natural verse breaks (empty lines in original)
                if self._should_break_section(i, h_lines, e_lines, current_section):
                    if current_section and current_section.lines:
                        sections.append(current_section)
                        current_section = None
            
            i += 1
        
        # Add final section if it exists
        if current_section and current_section.lines:
            sections.append(current_section)
        
        return sections
    
    def _extract_text_with_breaks(self, html: str) -> str:
        """Extract text from HTML while preserving line breaks"""
        # Replace <br> tags with newlines
        text = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
        # Remove other HTML tags
        text = self._strip_html(text)
        return text
    
    def _should_break_section(self, current_idx: int, h_lines: List[str], e_lines: List[str], current_section: SongSection) -> bool:
        """Determine if we should break the current section"""
        # For verses, break after 4 lines (typical verse length)
        if current_section.section_type == "verse" and len(current_section.lines) >= 4:
            return True
        # For chorus, be more flexible - look for actual content breaks
        if current_section.section_type == "chorus" and len(current_section.lines) >= 6:
            return True
        # Could add more sophisticated logic here based on content analysis
        return False
    
    def _split_into_blocks(self, html_content: str) -> List[str]:
        """Split HTML content into logical blocks (verses/chorus)"""
        
        # First normalize <br> tags and preserve them
        content = re.sub(r'<br\s*/?>', '||BR||', html_content, flags=re.IGNORECASE)
        
        # Split on verse boundaries (double <br> or <p> tags indicate verse separation)
        blocks = re.split(r'\|\|BR\|\|\s*\|\|BR\|\||<p[^>]*>|</p>', content, flags=re.IGNORECASE)
        
        # Clean up blocks
        cleaned_blocks = []
        for block in blocks:
            # Convert ||BR|| back to newlines for line separation
            block = re.sub(r'\|\|BR\|\|', '\n', block)
            block = self._strip_html(block)
            block = self._clean_text(block)
            
            if block.strip() and len(block.strip()) > 10:  # Ensure substantial content
                cleaned_blocks.append(block)
        
        return cleaned_blocks
    
    def _extract_lines_from_block(self, block_text: str) -> List[str]:
        """Extract individual lines from a text block"""
        # Split on line breaks (preserved from <br> conversion)
        lines = block_text.split('\n')
        
        # Clean and filter lines
        cleaned_lines = []
        for line in lines:
            line = self._clean_text(line)
            # Skip header-only lines and empty lines
            if line.strip() and not self._is_section_header(line):
                cleaned_lines.append(line)
        
        return cleaned_lines
    
    def _is_section_header(self, line: str) -> bool:
        """Check if a line is just a section header (Hui:, Chorus:, etc.)"""
        line_clean = line.strip().lower()
        headers = ['hui:', 'chorus:', 'verse 1:', 'verse 2:', 'verse 3:', 'bridge:']
        return line_clean in headers or len(line_clean) < 8
    
    def _strip_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        # Remove HTML tags but preserve content
        text = re.sub(r'<[^>]+>', ' ', text)
        # Decode HTML entities
        text = html.unescape(text)
        return text
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove common artifacts
        text = re.sub(r'^[-\s]*', '', text)  # Leading dashes
        text = re.sub(r'[\s\-]*$', '', text)   # Trailing spaces/dashes
        
        return text
    
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
            "parsing_method": "raw_html_parser",
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
    """Test the raw HTML parser on sample files"""
    parser = RawHtmlParser()
    
    test_files = [
        "data/source_html/E Waianae.txt",
        "data/source_html/Pili Mau Me Oe.txt"
    ]
    
    for file_path in test_files:
        if Path(file_path).exists():
            print(f"\n🔍 Testing: {file_path}")
            try:
                song, validation = parser.parse_file(file_path)
                print(f"   Title: '{song.title}'")
                print(f"   Composer: '{song.composer}'")
                print(f"   Translator: '{song.translator}'")
                print(f"   Sections: {len(song.sections)}")
                print(f"   Quality Score: {validation.get('quality_score', 0)}")
                
                # Show sections breakdown
                for i, section in enumerate(song.sections):
                    print(f"   Section {i+1}: {section.section_type} ({len(section.lines)} lines)")
                    if section.lines:
                        first_line = section.lines[0]
                        print(f"      H: {first_line.hawaiian_text[:60]}...")
                        print(f"      E: {first_line.english_text[:60]}...")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    test_parser()