# Hawaiian Song Structure Analysis

## Overview
Based on examination of the four most common Hawaiian song structures found in `data/song_forms/`, this document analyzes the patterns and provides guidance for improved HTML parsing and JSON extraction.

## Four Common Hawaiian Song Structures

### 1. Four-Line Strophic (Hula Ku'i Form)
**Example:** E Wai'anae by Kenneth Makuakāne

**Characteristics:**
- 4 verses, each with exactly 4 lines
- No standalone "hui" word
- Consistent stanza pattern: 4 lines + blank line separator
- HTML pattern: 4 lines with single `<br>` + double `<br>` separator
- Word "hui" may appear within text but never as standalone section marker

**Parsing Implications:**
- Detect by: absence of standalone "hui" + consistent 4-line groupings
- Section breaks: double `<br>` or equivalent blank lines
- Line breaks: single `<br>` within verses should be preserved
- Structure type: `"strophic"`

### 2. Two-Line Strophic (Hula Ku'i Form)
**Example:** Haleakala Hula (Kuahiwi Nani) by Alice Nāmakelua

**Characteristics:**
- Multiple verses, each with exactly 2 lines
- No standalone "hui" word
- Consistent stanza pattern: 2 lines + blank line separator
- HTML pattern: 2 lines with single `<br>` + double `<br>` separator
- More compact verse structure than 4-line form

**Parsing Implications:**
- Detect by: absence of standalone "hui" + consistent 2-line groupings
- Requires different verse detection logic than 4-line strophic
- Structure type: `"strophic"`

### 3. Verse-Chorus (A/B Form)
**Example:** Kanaka Waiwai (composer unknown/John Kameaaloha Almeida)

**Characteristics:**
- Clear "Hui:" marker appearing as standalone text
- Verses typically 4-5 lines, chorus typically 4 lines
- Alternating pattern: verse → hui → verse → hui (or variations)
- HTML pattern: "Hui:" appears on its own line followed by chorus content

**Parsing Implications:**
- Detect by: presence of standalone "Hui:" text
- Section identification: everything after "Hui:" until next verse is chorus
- Line 25: `Hui:` appears alone, followed by chorus lines 26-29
- Structure type: `"verse_chorus"`

### 4. Through-Composed
**Example:** Hole Waimea (traditional, composer unknown)

**Characteristics:**
- No regular stanza pattern or repeated sections
- Variable line counts per section (here: 10 lines + 7 lines)
- No standalone "hui" word
- Natural content breaks represent logical flow changes (line 28 shows section break)
- Most free-form structure

**Parsing Implications:**
- Detect by: absence of standalone "hui" + irregular stanza patterns
- Section breaks: maintain natural content breaks (double line breaks) to preserve logical flow changes
- Sections should be unlabeled (no "Verse 1:", "Verse 2:" labels)
- Think of them like four-line strophic sections but without line limits
- Variable verse lengths must be accommodated
- Structure type: `"through_composed"`

## Critical Parsing Insights

### HTML Line Break Handling
All forms mention that HTML creators sometimes insert breaks when lyrics/translations are too long:
- **Problem:** Artificial line breaks in middle of logical lines
- **Solution:** Consolidate broken lines that don't start with capital letters
- **Exception:** Proper nouns (place names, wind names, people names) can appear mid-line with capitals

### Hui Detection Rules
1. **Standalone "hui" or "Hui:"** = verse-chorus structure
2. **"hui" within text only** = strophic or through-composed
3. **No "hui" at all** = strophic or through-composed (differentiate by pattern regularity)

### Section Break Patterns
- **Strophic forms:** Regular blank line separators between consistent verse lengths
- **Verse-chorus:** "Hui:" marker creates section boundary
- **Through-composed:** Content-driven breaks, irregular patterns

## Recommended Parser Improvements

### 1. Enhanced Structure Detection
```python
def detect_song_structure(self, paired_lines):
    # Check for standalone hui first
    if self._has_standalone_hui(paired_lines):
        return "verse_chorus"
    
    # Analyze verse length patterns
    verse_lengths = self._analyze_verse_patterns(paired_lines)
    
    if self._is_regular_pattern(verse_lengths):
        if all(length == 4 for length in verse_lengths):
            return "four_line_strophic"
        elif all(length == 2 for length in verse_lengths):
            return "two_line_strophic"
        else:
            return "strophic"  # regular but not 2 or 4 lines
    else:
        return "through_composed"  # irregular patterns, preserve natural breaks

def create_section_label(self, structure_type, section_type, section_number):
    # Through-composed sections remain unlabeled
    if structure_type == "through_composed":
        return ""  # No labels for through-composed sections
    elif section_type == "chorus":
        return "Hui:"
    else:
        return f"Verse {section_number}:"
```

### 2. Line Consolidation Logic
```python
def consolidate_broken_lines(self, lines):
    # Merge lines that don't start with capitals (except proper nouns)
    # Look for pattern: line ends mid-word or next line doesn't start with capital
    # Be careful with Hawaiian place names, wind names, people names
```

### 3. Section Break Detection
- **Double `<br><br>`** or **blank lines** = section breaks (preserve for all forms)
- **"Hui:" standalone** = chorus section marker
- **Regular patterns** = strophic verses (labeled: "Verse 1:", "Verse 2:")
- **Irregular patterns** = through-composed sections (unlabeled, preserve natural breaks)

### 4. Metadata Enhancement
Add to JSON output:
- `structure_type`: "four_line_strophic" | "two_line_strophic" | "verse_chorus" | "through_composed"
- `verse_length_pattern`: [4,4,4,4] or [2,2,2,2,2] or "irregular"
- `hui_detected`: boolean
- `section_breaks_detected`: count of major structural breaks

## Implementation Priority
1. **Hui detection** (already implemented) ✓
2. **Line consolidation** for broken HTML lines
3. **Verse pattern analysis** for strophic subtype detection
4. **Through-composed handling** for irregular structures

This analysis provides the foundation for more accurate structural parsing of Hawaiian songs across all common forms.