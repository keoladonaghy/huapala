#!/usr/bin/env python3

import os
import sys
sys.path.append('.')

from database import SessionLocal, Verses, VerseLines

try:
    # Use the same database connection as the app
    db = SessionLocal()

    print("=== CHECKING ADIOS KE ALOHA CHORUS LINES ===")
    print()

    # Query for chorus lines using SQLAlchemy
    chorus_lines = db.query(VerseLines).join(Verses).filter(
        Verses.mele_source_id == 'adios_ke_aloha_canonical_source',
        Verses.verse_type == 'chorus'
    ).order_by(Verses.verse_order, VerseLines.line_number).all()

    if chorus_lines:
        print(f"Found {len(chorus_lines)} chorus lines:")
        print()
        for line in chorus_lines:
            verse = db.query(Verses).filter(Verses.id == line.verse_id).first()
            # Check for dashes after 'w'
            has_dash = 'w-' in line.english_text.lower() if line.english_text else False
            dash_indicator = " *** HAS DASH ***" if has_dash else ""
            print(f"Line {line.line_number}: {line.english_text}{dash_indicator}")
        print()
    else:
        print("No chorus lines found!")

    # Also check first few verse lines to compare
    print("=== CHECKING FIRST VERSE LINES ===")
    print()

    verse_lines = db.query(VerseLines).join(Verses).filter(
        Verses.mele_source_id == 'adios_ke_aloha_canonical_source',
        Verses.verse_type == 'verse'
    ).order_by(Verses.verse_order, VerseLines.line_number).limit(5).all()

    if verse_lines:
        for line in verse_lines:
            has_dash = 'w-' in line.english_text.lower() if line.english_text else False
            dash_indicator = " *** HAS DASH ***" if has_dash else ""
            print(f"Verse Line {line.line_number}: {line.english_text}{dash_indicator}")
    else:
        print("No verse lines found!")

finally:
    db.close()