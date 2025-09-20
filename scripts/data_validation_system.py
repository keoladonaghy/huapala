#!/usr/bin/env python3
"""
Huapala Data Validation and Logging System

A comprehensive system for validating HTML parsing, tracking data quality issues,
and flagging content that requires manual review.
"""

import json
import logging
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any

class EnumEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles enum values"""
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)

class IssueType(Enum):
    """Types of data quality issues that can be detected"""
    # Line alignment issues
    LINE_COUNT_MISMATCH = "line_count_mismatch"
    MISSING_TRANSLATION = "missing_translation"
    STRUCTURAL_MISMATCH = "structural_mismatch"
    
    # Attribution issues  
    NO_COMPOSER = "no_composer"
    NO_LYRICIST = "no_lyricist"
    NO_TRANSLATOR = "no_translator"
    UNCLEAR_ATTRIBUTION = "unclear_attribution"
    
    # Content quality issues
    UNIDENTIFIABLE_TEXT = "unidentifiable_text"
    MALFORMED_HTML = "malformed_html"
    ENCODING_ISSUES = "encoding_issues"
    MISSING_VERSE_MARKERS = "missing_verse_markers"
    
    # Structural issues
    NO_VERSE_CHORUS_STRUCTURE = "no_verse_chorus_structure"
    INCOMPLETE_LYRICS = "incomplete_lyrics"
    UNUSUAL_FORMATTING = "unusual_formatting"
    
    # Data integrity issues
    DUPLICATE_CONTENT = "duplicate_content"
    EMPTY_REQUIRED_FIELD = "empty_required_field"
    INVALID_CHARACTERS = "invalid_characters"

class IssueSeverity(Enum):
    """Severity levels for issues"""
    LOW = "low"           # Cosmetic issues, doesn't affect functionality
    MEDIUM = "medium"     # May affect display quality
    HIGH = "high"         # Likely affects user experience  
    CRITICAL = "critical" # Prevents proper processing

@dataclass
class ValidationIssue:
    """Individual validation issue"""
    issue_type: IssueType
    severity: IssueSeverity
    description: str
    location: str  # Where in the file/content the issue occurs
    raw_content: Optional[str] = None  # The problematic content
    suggested_action: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass 
class SongValidationResult:
    """Complete validation result for a song"""
    song_id: str
    song_title: str
    source_file: str
    
    # Parsed content
    hawaiian_lines: List[str]
    english_lines: List[str]
    verse_structure: List[Dict]  # verse/chorus breakdown
    
    # Attribution data
    composer: Optional[str] = None
    lyricist: Optional[str] = None
    translator: Optional[str] = None
    
    # Quality metrics
    data_quality_score: float = 0.0  # 0-100 scale
    manual_review_required: bool = False
    processing_status: str = "pending"  # pending, processed, flagged, failed
    
    # Issue tracking
    validation_issues: List[ValidationIssue] = None
    stray_text: List[str] = None  # Unidentifiable content
    processing_notes: str = ""
    
    def __post_init__(self):
        if self.validation_issues is None:
            self.validation_issues = []
        if self.stray_text is None:
            self.stray_text = []

class HuapalaValidator:
    """Main validation and logging system"""
    
    def __init__(self, log_file: str = "huapala_validation.log"):
        self.log_file = log_file
        self.setup_logging()
        self.validation_results: List[SongValidationResult] = []
        
    def setup_logging(self):
        """Configure logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def validate_song(self, song_data: Dict) -> SongValidationResult:
        """Validate a single song and return comprehensive results"""
        result = SongValidationResult(
            song_id=song_data.get('id', 'unknown'),
            song_title=song_data.get('title', 'Unknown Title'),
            source_file=song_data.get('source_file', 'unknown'),
            hawaiian_lines=[],
            english_lines=[],
            verse_structure=[]
        )
        
        # Validate attribution
        self._validate_attribution(song_data, result)
        
        # Validate line structure
        self._validate_line_structure(song_data, result)
        
        # Validate content quality
        self._validate_content_quality(song_data, result)
        
        # Calculate quality score
        result.data_quality_score = self._calculate_quality_score(result)
        
        # Determine if manual review is needed
        result.manual_review_required = self._requires_manual_review(result)
        
        self.validation_results.append(result)
        return result
    
    def _validate_attribution(self, song_data: Dict, result: SongValidationResult):
        """Validate composer, lyricist, translator information"""
        
        # Check for missing composer
        composer = song_data.get('composer', '').strip()
        if not composer:
            result.validation_issues.append(ValidationIssue(
                issue_type=IssueType.NO_COMPOSER,
                severity=IssueSeverity.HIGH,
                description="No composer credited for this song",
                location="attribution section"
            ))
        else:
            result.composer = composer
            
        # Check for missing lyricist
        lyricist = song_data.get('lyricist', '').strip()
        if not lyricist:
            result.validation_issues.append(ValidationIssue(
                issue_type=IssueType.NO_LYRICIST,
                severity=IssueSeverity.MEDIUM,
                description="No lyricist credited for this song",
                location="attribution section"
            ))
        else:
            result.lyricist = lyricist
            
        # Check for missing translator
        translator = song_data.get('translator', '').strip()
        if not translator and song_data.get('has_english_translation', False):
            result.validation_issues.append(ValidationIssue(
                issue_type=IssueType.NO_TRANSLATOR,
                severity=IssueSeverity.MEDIUM,
                description="Song has English translation but no translator credited",
                location="attribution section"
            ))
        else:
            result.translator = translator
    
    def _validate_line_structure(self, song_data: Dict, result: SongValidationResult):
        """Validate Hawaiian/English line alignment and structure"""
        
        hawaiian_lines = song_data.get('hawaiian_lines', [])
        english_lines = song_data.get('english_lines', [])
        
        result.hawaiian_lines = hawaiian_lines
        result.english_lines = english_lines
        
        # Check for line count mismatch
        if len(hawaiian_lines) != len(english_lines):
            result.validation_issues.append(ValidationIssue(
                issue_type=IssueType.LINE_COUNT_MISMATCH,
                severity=IssueSeverity.HIGH,
                description=f"Hawaiian lines ({len(hawaiian_lines)}) don't match English lines ({len(english_lines)})",
                location="lyrics section",
                suggested_action="Manual review required to align translations"
            ))
        
        # Check for missing translation
        if hawaiian_lines and not english_lines:
            result.validation_issues.append(ValidationIssue(
                issue_type=IssueType.MISSING_TRANSLATION,
                severity=IssueSeverity.MEDIUM,
                description="Song has Hawaiian lyrics but no English translation",
                location="lyrics section"
            ))
            
        # Check for verse/chorus structure
        if not song_data.get('has_verse_structure', False):
            result.validation_issues.append(ValidationIssue(
                issue_type=IssueType.NO_VERSE_CHORUS_STRUCTURE,
                severity=IssueSeverity.MEDIUM,
                description="Unable to identify clear verse/chorus structure",
                location="lyrics section"
            ))
    
    def _validate_content_quality(self, song_data: Dict, result: SongValidationResult):
        """Validate content quality and identify stray text"""
        
        # Check for stray/unidentifiable text
        stray_text = song_data.get('stray_text', [])
        if stray_text:
            result.stray_text = stray_text
            result.validation_issues.append(ValidationIssue(
                issue_type=IssueType.UNIDENTIFIABLE_TEXT,
                severity=IssueSeverity.MEDIUM,
                description=f"Found {len(stray_text)} segments of unidentifiable text",
                location="various",
                raw_content=str(stray_text)[:200],  # First 200 chars
                suggested_action="Manual review to categorize or discard"
            ))
        
        # Check for encoding issues
        all_text = ' '.join(result.hawaiian_lines + result.english_lines)
        if any(ord(c) > 65535 for c in all_text):  # Non-BMP characters
            result.validation_issues.append(ValidationIssue(
                issue_type=IssueType.ENCODING_ISSUES,
                severity=IssueSeverity.LOW,
                description="Contains unusual Unicode characters",
                location="lyrics content"
            ))
    
    def _calculate_quality_score(self, result: SongValidationResult) -> float:
        """Calculate data quality score (0-100)"""
        score = 100.0
        
        for issue in result.validation_issues:
            if issue.severity == IssueSeverity.CRITICAL:
                score -= 25
            elif issue.severity == IssueSeverity.HIGH:
                score -= 15
            elif issue.severity == IssueSeverity.MEDIUM:
                score -= 8
            elif issue.severity == IssueSeverity.LOW:
                score -= 3
                
        return max(0.0, score)
    
    def _requires_manual_review(self, result: SongValidationResult) -> bool:
        """Determine if song requires manual review"""
        critical_issues = [i for i in result.validation_issues 
                          if i.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH]]
        
        return (
            len(critical_issues) > 0 or
            result.data_quality_score < 70 or
            len(result.stray_text) > 0 or
            len(result.validation_issues) > 5
        )
    
    def generate_report(self, output_file: str = "validation_report.json"):
        """Generate comprehensive validation report"""
        report = {
            "generation_timestamp": datetime.now().isoformat(),
            "total_songs_processed": len(self.validation_results),
            "summary": self._generate_summary(),
            "songs_requiring_review": [
                asdict(r) for r in self.validation_results 
                if r.manual_review_required
            ],
            "issue_breakdown": self._generate_issue_breakdown(),
            "all_results": [asdict(r) for r in self.validation_results]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, cls=EnumEncoder)
            
        self.logger.info(f"Validation report generated: {output_file}")
        return report
    
    def _generate_summary(self) -> Dict:
        """Generate summary statistics"""
        total = len(self.validation_results)
        if total == 0:
            return {}
            
        requiring_review = sum(1 for r in self.validation_results if r.manual_review_required)
        avg_quality = sum(r.data_quality_score for r in self.validation_results) / total
        
        return {
            "total_songs": total,
            "songs_requiring_manual_review": requiring_review,
            "percentage_requiring_review": round((requiring_review / total) * 100, 1),
            "average_quality_score": round(avg_quality, 1),
            "songs_with_stray_text": sum(1 for r in self.validation_results if r.stray_text)
        }
    
    def _generate_issue_breakdown(self) -> Dict:
        """Generate breakdown of issues by type"""
        issue_counts = {}
        for result in self.validation_results:
            for issue in result.validation_issues:
                issue_type = issue.issue_type.value
                if issue_type not in issue_counts:
                    issue_counts[issue_type] = 0
                issue_counts[issue_type] += 1
        
        return dict(sorted(issue_counts.items(), key=lambda x: x[1], reverse=True))

# Example usage
if __name__ == "__main__":
    validator = HuapalaValidator()
    
    # Example song data for testing
    example_song = {
        'id': 'test_song_1',
        'title': 'Test Song',
        'source_file': 'test.html',
        'composer': 'John K. Almeida',
        'lyricist': '',  # Missing - will be flagged
        'translator': 'Test Translator',
        'hawaiian_lines': ['Line 1', 'Line 2', 'Line 3'],
        'english_lines': ['English 1', 'English 2'],  # Mismatch - will be flagged
        'has_verse_structure': True,
        'stray_text': ['Some unidentifiable text']  # Will be flagged
    }
    
    result = validator.validate_song(example_song)
    report = validator.generate_report()
    
    print(f"Processed song with quality score: {result.data_quality_score}")
    print(f"Manual review required: {result.manual_review_required}")
    print(f"Issues found: {len(result.validation_issues)}")