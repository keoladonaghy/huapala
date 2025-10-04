"""
SQLAlchemy models for Huapala Hawaiian Music Database

Models representing the existing Neon PostgreSQL database schema
for use with SQLAdmin admin interface.
"""

import os
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Boolean, Date, ForeignKey, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import ARRAY, UUID

# Database configuration - same as main.py
def get_database_url():
    """Get database URL from environment variables"""
    host = os.getenv('PGHOST', 'ep-young-silence-ad9wue88-pooler.c-2.us-east-1.aws.neon.tech')
    database = os.getenv('PGDATABASE', 'neondb')
    user = os.getenv('PGUSER', 'neondb_owner')
    password = os.getenv('PGPASSWORD')
    port = os.getenv('PGPORT', 5432)
    
    return f"postgresql://{user}:{password}@{host}:{port}/{database}?sslmode=require"

# SQLAlchemy setup
DATABASE_URL = get_database_url()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models based on existing database structure

class CanonicalMele(Base):
    """Canonical songs table - main song repository"""
    __tablename__ = "canonical_mele"
    
    canonical_mele_id = Column(String, primary_key=True)
    canonical_title_hawaiian = Column(String)
    canonical_title_english = Column(String)
    primary_composer = Column(String)
    primary_lyricist = Column(String)
    estimated_composition_date = Column(String)
    cultural_significance_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    mele_sources = relationship("MeleSources", back_populates="canonical_mele")
    mele_media = relationship("MeleMedia", back_populates="canonical_mele")
    
    def __str__(self):
        return f"{self.canonical_title_hawaiian or self.canonical_title_english or self.canonical_mele_id}"

class MeleSources(Base):
    """Song sources and detailed metadata"""
    __tablename__ = "mele_sources"
    
    id = Column(String, primary_key=True)
    canonical_mele_id = Column(String, ForeignKey("canonical_mele.canonical_mele_id"))
    composer = Column(String)
    translator = Column(String)
    hawaiian_editor = Column(String)
    source_file = Column(String)
    source_publication = Column(String)
    copyright_info = Column(Text)
    verses_json = Column(JSON)
    song_type = Column(String)
    structure_type = Column(String)
    primary_location = Column(String)
    island = Column(String)
    themes = Column(String)
    mele_type = Column(String)
    cultural_elements = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    canonical_mele = relationship("CanonicalMele", back_populates="mele_sources")
    verses = relationship("Verses", back_populates="mele_source", cascade="all, delete-orphan")
    processing_metadata = relationship("VerseProcessingMetadata", back_populates="mele_source", uselist=False, cascade="all, delete-orphan")
    
    def __str__(self):
        return f"Source for {self.canonical_mele_id}"

class MeleMedia(Base):
    """Media links (YouTube, etc.) for songs"""
    __tablename__ = "mele_media"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    canonical_mele_id = Column(String, ForeignKey("canonical_mele.canonical_mele_id"))
    url = Column(String)
    media_type = Column(String)
    title = Column(String)
    description = Column(Text)
    # Note: created_at column doesn't exist in the actual database table
    
    # Relationships
    canonical_mele = relationship("CanonicalMele", back_populates="mele_media")
    
    def __str__(self):
        return f"Media: {self.title or self.url}"

class People(Base):
    """People database - composers, lyricists, etc."""
    __tablename__ = "people"
    
    person_id = Column(String, primary_key=True)
    full_name = Column(String)
    display_name = Column(String)
    place_of_birth = Column(String)
    places_of_hawaiian_influence = Column(JSON)  # Array stored as JSON
    primary_influence_location = Column(String)
    hawaiian_speaker = Column(Boolean)
    birth_date = Column(String)  # Stored as string for flexibility
    death_date = Column(String)  # Stored as string for flexibility
    cultural_background = Column(String)
    biographical_notes = Column(Text)
    photograph = Column(String)  # New field for photograph filename
    caption = Column(String)     # New field for photo caption
    roles = Column(JSON)  # Array stored as JSON
    primary_role = Column(String)
    specialties = Column(JSON)  # Array stored as JSON
    active_period_start = Column(Integer)
    active_period_end = Column(Integer)
    notable_works = Column(JSON)  # Array stored as JSON
    awards_honors = Column(JSON)  # Array of objects stored as JSON
    source_references = Column(JSON)  # Object with sources and citations arrays
    verification_status = Column(String)
    last_verified_date = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __str__(self):
        return self.display_name or self.full_name or self.person_id

class SongbookEntries(Base):
    """Songbook entries submitted by users"""
    __tablename__ = "songbook_entries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    printed_song_title = Column(String)
    eng_title_transl = Column(String)
    modern_song_title = Column(String)
    scripped_song_title = Column(String)
    song_title = Column(String)
    songbook_name = Column(String)
    page = Column(Integer)
    pub_year = Column(Integer)
    diacritics = Column(String)
    composer = Column(String)
    additional_information = Column(Text)
    email_address = Column(String)
    canonical_mele_id = Column(String, ForeignKey("canonical_mele.canonical_mele_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __str__(self):
        return self.printed_song_title or f"Entry #{self.id}"

class ValidationSessions(Base):
    """Data validation session tracking"""
    __tablename__ = "validation_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_name = Column(String)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    total_songs = Column(Integer)
    songs_processed = Column(Integer)
    songs_flagged = Column(Integer)
    average_quality_score = Column(String)  # Stored as string in your schema
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __str__(self):
        return f"Validation: {self.session_name}"

# New normalized verse storage tables

class Verses(Base):
    """Individual verses within songs - replaces verses_json structure"""
    __tablename__ = "verses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    mele_source_id = Column(String, ForeignKey("mele_sources.id"), nullable=False)
    verse_id = Column(String, nullable=False)  # e.g., "v1", "chorus1"
    verse_type = Column(String, nullable=False)  # "verse", "chorus", "bridge", etc.
    verse_number = Column(Integer, nullable=True)  # 1, 2, 3, etc.
    verse_order = Column(Integer, nullable=False)  # Display order
    label = Column(String, nullable=True)  # "Verse 1:", "Hui:", etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    mele_source = relationship("MeleSources", back_populates="verses")
    verse_lines = relationship("VerseLines", back_populates="verse", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        {'sqlite_autoincrement': True}
    )
    
    def __str__(self):
        return f"{self.verse_type} {self.verse_number or ''} ({self.verse_id})"

class VerseLines(Base):
    """Individual lines within verses - replaces line-level JSON data"""
    __tablename__ = "verse_lines"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    verse_id = Column(Integer, ForeignKey("verses.id", ondelete="CASCADE"), nullable=False)
    line_id = Column(String, nullable=False)  # e.g., "v1.1", "v1.2"
    line_number = Column(Integer, nullable=False)  # 1, 2, 3, etc.
    hawaiian_text = Column(Text, nullable=True)
    english_text = Column(Text, nullable=True)
    is_bilingual = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    verse = relationship("Verses", back_populates="verse_lines")
    
    def __str__(self):
        return f"Line {self.line_number}: {(self.hawaiian_text or self.english_text or '')[:50]}..."

class VerseProcessingMetadata(Base):
    """Processing metadata for songs - replaces processing_metadata from JSON"""
    __tablename__ = "verse_processing_metadata"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    mele_source_id = Column(String, ForeignKey("mele_sources.id"), nullable=False, unique=True)
    processing_notes = Column(Text, nullable=True)
    validation_status = Column(String, nullable=True)
    last_processed_at = Column(DateTime, nullable=True)
    processor_version = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    mele_source = relationship("MeleSources", back_populates="processing_metadata")
    
    def __str__(self):
        return f"Processing metadata for {self.mele_source_id}"

# Database dependency for FastAPI
def get_database():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()