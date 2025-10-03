"""
Pydantic models for comprehensive song editing
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MediaType(str, Enum):
    youtube = "youtube"
    audio = "audio"
    video = "video"
    other = "other"


class Island(str, Enum):
    hawaii = "Hawaiʻi"
    maui = "Maui" 
    oahu = "Oʻahu"
    kauai = "Kauaʻi"
    molokai = "Molokaʻi"
    lanai = "Lānaʻi"
    multiple = "Multiple"


class LineModel(BaseModel):
    """Individual line of lyrics"""
    id: str
    line_number: int
    hawaiian_text: Optional[str] = ""
    english_text: Optional[str] = ""
    is_bilingual: bool = True


class VerseModel(BaseModel):
    """Individual verse/chorus/section"""
    id: str
    type: str = "verse"  # verse, chorus, bridge, etc.
    number: int
    order: int
    label: Optional[str] = None
    lines: List[LineModel] = []
    
    @validator('label', always=True)
    def generate_label(cls, v, values):
        if v is None and 'type' in values and 'number' in values:
            return f"{values['type'].title()} {values['number']}:"
        return v


class LyricsModel(BaseModel):
    """Complete lyrics structure"""
    verses: List[VerseModel] = []
    processing_metadata: Optional[Dict[str, Any]] = {}


class MediaLinkModel(BaseModel):
    """Media link (YouTube, audio files, etc.)"""
    id: Optional[int] = None
    url: str
    media_type: MediaType = MediaType.youtube
    title: Optional[str] = ""
    description: Optional[str] = ""


class ComprehensiveSongModel(BaseModel):
    """Complete song data model for editing"""
    # Core identification (top row)
    canonical_mele_id: str
    canonical_title_hawaiian: Optional[str] = ""
    primary_composer: Optional[str] = ""
    
    # Credits & People
    canonical_title_english: Optional[str] = ""
    primary_lyricist: Optional[str] = ""
    composer: Optional[str] = ""  # Source-specific composer
    translator: Optional[str] = ""
    hawaiian_editor: Optional[str] = ""
    estimated_composition_date: Optional[str] = ""
    
    # Publication & Sources
    source_file: Optional[str] = ""
    source_publication: Optional[str] = ""
    copyright_info: Optional[str] = ""
    
    # Cultural & Geographic
    primary_location: Optional[str] = ""
    island: Optional[Island] = None
    themes: Optional[str] = ""
    mele_type: Optional[str] = ""
    cultural_elements: Optional[str] = ""
    cultural_significance_notes: Optional[str] = ""
    
    # Technical & Metadata
    song_type: Optional[str] = ""
    structure_type: Optional[str] = ""
    
    # Lyrics
    lyrics: LyricsModel = Field(default_factory=LyricsModel)
    
    # Media Links
    media_links: List[MediaLinkModel] = []
    
    # System fields (read-only)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @validator('island', pre=True)
    def validate_island(cls, v):
        """Convert empty string to None for island field"""
        if v == "":
            return None
        return v
    
    class Config:
        # Allow arbitrary field names for dynamic form processing
        extra = "allow"


class FormProcessingModel(BaseModel):
    """Model for processing form data with dynamic verse/line fields"""
    # Parse verse_v1_line_1_hawaiian type field names
    verses_data: Dict[str, Dict[str, Dict[str, str]]] = {}
    media_data: Dict[str, Dict[str, str]] = {}
    
    @classmethod
    def parse_form_data(cls, form_data: Dict[str, str]) -> "ComprehensiveSongModel":
        """
        Parse form data into structured song model
        """
        # Extract basic fields
        song_data = {}
        verses_data = {}
        media_data = {}
        
        print(f"DEBUG: Processing {len(form_data)} form fields")
        for field_name, value in form_data.items():
            if field_name.startswith('verse_'):
                print(f"DEBUG: Found verse field: '{field_name}' = '{value[:50]}...' (len={len(value)})")
                # Parse verse_v1_1_line_1_hawaiian or verse_v1_1_label -> verses_data['v1_1']['1']['hawaiian'] = value
                parts = field_name.split('_')
                
                # Handle label fields: verse_v1_1_label
                if len(parts) == 3 and parts[2] == 'label':
                    verse_id = parts[1]
                    # Skip label fields for now - they're handled separately
                    continue
                
                # Handle line fields: verse_v1_1_line_1_hawaiian
                elif len(parts) >= 5:
                    verse_id = parts[1]
                    
                    # Find the "line" part and line number
                    line_index = None
                    for i, part in enumerate(parts):
                        if part == "line":
                            line_index = i
                            break
                    
                    if line_index is None or line_index + 1 >= len(parts):
                        print(f"Warning: No 'line' found in field format '{field_name}', skipping")
                        continue
                    
                    line_num = parts[line_index + 1]
                    text_type = parts[line_index + 2] if line_index + 2 < len(parts) else None
                    
                    if text_type not in ['hawaiian', 'english']:
                        print(f"Warning: Invalid text type '{text_type}' in field '{field_name}', skipping")
                        continue
                    
                    # Validate that line_num is actually a number
                    try:
                        int(line_num)  # Just test if it's convertible
                    except ValueError:
                        print(f"Warning: Invalid line number '{line_num}' in field '{field_name}', skipping")
                        continue
                    
                    if verse_id not in verses_data:
                        verses_data[verse_id] = {}
                    if line_num not in verses_data[verse_id]:
                        verses_data[verse_id][line_num] = {}
                    
                    verses_data[verse_id][line_num][text_type] = value
                else:
                    print(f"Warning: Malformed verse field name '{field_name}', expected format 'verse_ID_line_NUM_TYPE'")
                    
            elif field_name.startswith('media_'):
                # Parse media_new_1_url -> media_data['new_1']['url'] = value
                parts = field_name.split('_', 2)
                if len(parts) >= 3:
                    media_id = parts[1] + '_' + parts[2].split('_')[0]  # 'new_1' or '123'
                    field_type = '_'.join(parts[2].split('_')[1:])  # 'url', 'type', 'title', 'description'
                    
                    if media_id not in media_data:
                        media_data[media_id] = {}
                    
                    media_data[media_id][field_type] = value
            else:
                # Regular field
                song_data[field_name] = value
        
        # Convert verses_data to LyricsModel
        verses = []
        for verse_id, verse_lines in verses_data.items():
            # Extract verse number from verse_id (e.g., 'v1' -> 1, 'v1_1' -> 1)
            if verse_id.startswith('v'):
                # Handle both old format (v1) and new format (v1_1)
                verse_part = verse_id[1:].split('_')[0]
                verse_num = int(verse_part)
            else:
                verse_num = 1
            
            lines = []
            for line_num, line_data in verse_lines.items():
                # Handle line_num parsing safely
                try:
                    line_number = int(line_num)
                except ValueError:
                    # If line_num isn't a number, skip this line or use default
                    print(f"Warning: Invalid line number '{line_num}' for verse '{verse_id}', skipping")
                    continue
                    
                lines.append(LineModel(
                    id=f"{verse_id}.{line_number}",
                    line_number=line_number,
                    hawaiian_text=line_data.get('hawaiian', ''),
                    english_text=line_data.get('english', ''),
                    is_bilingual=True
                ))
            
            # Sort lines by line number
            lines.sort(key=lambda x: x.line_number)
            
            verses.append(VerseModel(
                id=verse_id,
                type="verse",  # Could be enhanced to detect type from form
                number=verse_num,
                order=verse_num,
                lines=lines
            ))
        
        # Sort verses by number
        verses.sort(key=lambda x: x.number)
        
        # Fix verse orders to be unique sequential numbers
        for i, verse in enumerate(verses):
            verse.order = i + 1  # 1, 2, 3, 4...
        
        song_data['lyrics'] = LyricsModel(verses=verses)
        
        # Convert media_data to MediaLinkModel list
        media_links = []
        for media_id, media_fields in media_data.items():
            if media_fields.get('url'):  # Only include if URL is provided
                media_links.append(MediaLinkModel(
                    id=int(media_id) if media_id.isdigit() else None,
                    url=media_fields['url'],
                    media_type=MediaType(media_fields.get('type', 'youtube')),
                    title=media_fields.get('title', ''),
                    description=media_fields.get('description', '')
                ))
        
        song_data['media_links'] = media_links
        
        return ComprehensiveSongModel(**song_data)


class ValidationResult(BaseModel):
    """Result of song data validation"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    corrected_fields: Dict[str, str] = {}


class BackupMetadata(BaseModel):
    """Metadata for song backups"""
    song_id: str
    backup_timestamp: datetime
    backup_path: str
    user_action: str  # "manual", "auto_save", "before_edit"
    changes_summary: Optional[str] = None


def validate_song_data(song: ComprehensiveSongModel) -> ValidationResult:
    """
    Validate comprehensive song data
    """
    result = ValidationResult(is_valid=True)
    
    # Required field checks
    if not song.canonical_mele_id:
        result.errors.append("Song ID (canonical_mele_id) is required")
    
    if not song.canonical_title_hawaiian and not song.canonical_title_english:
        result.errors.append("At least one title (Hawaiian or English) is required")
    
    # Lyrics validation
    if song.lyrics.verses:
        for verse in song.lyrics.verses:
            if not verse.lines:
                result.warnings.append(f"Verse {verse.number} has no lyrics lines")
            
            for line in verse.lines:
                if not line.hawaiian_text and not line.english_text:
                    result.warnings.append(f"Verse {verse.number}, line {line.line_number} is empty")
    
    # Media link validation
    for i, media in enumerate(song.media_links):
        if not media.url.startswith(('http://', 'https://')):
            result.errors.append(f"Media link {i+1}: Invalid URL format")
        
        if media.media_type == MediaType.youtube:
            if 'youtube.com' not in media.url and 'youtu.be' not in media.url:
                result.warnings.append(f"Media link {i+1}: URL doesn't appear to be YouTube")
    
    # Date format validation
    if song.estimated_composition_date:
        # Allow flexible date formats like "1890", "circa 1920", "1920-1925"
        if not any(char.isdigit() for char in song.estimated_composition_date):
            result.warnings.append("Composition date should include a year or date")
    
    result.is_valid = len(result.errors) == 0
    return result


def create_backup_filename(song_id: str, action: str = "manual") -> str:
    """Generate backup filename with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"backup_{song_id}_{action}_{timestamp}.json"