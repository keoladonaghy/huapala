# Huapala - Hawaiian Music Database System

A comprehensive database system for preserving and organizing Hawaiian music (mele) with proper cultural attribution and scholarly rigor.

## Overview

This system separates authoritative/canonical information from source-specific archival data, allowing for proper curation of Hawaiian music while preserving original source materials as-found.

## Database Structure

### Core Tables
- **canonical_mele**: Authoritative song information (single source of truth)
- **title_variations**: Tracks different spellings and alternate names
- **mele_sources**: Source-specific lyrical content and attributions
- **mele_media**: YouTube links and other media associated with songs

### Key Features
- Handles multiple songs with identical titles
- Preserves diacritical marks (ā, ē, ī, ō, ū, ʻ) 
- Supports verse/hui (chorus) structure
- Tracks attribution (composers, translators, editors)
- Links related media content

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Database Setup
Execute the SQL schema in your PostgreSQL database:
```bash
psql -d huapala -f schema.sql
```

### 3. Configure Database Connection
Set environment variables:
```bash
export DB_HOST=your-neon-host.com
export DB_NAME=huapala
export DB_USER=your-username
export DB_PASSWORD=your-password
export DB_PORT=5432
```

## Data Migration

### From JSON to PostgreSQL
```bash
# Dry run (generates reports only)
python migrate_to_postgres.py --dry-run

# Full migration
python migrate_to_postgres.py

# Custom directories
python migrate_to_postgres.py --input-dir data/extracted_json --output-dir reports
```

### Migration Process
1. **Automated**: Extracts and cleans data from JSON files
2. **Manual Review**: Generates CSV reports for curator review
3. **Database Insert**: Populates all tables with proper relationships

## Original Data Processing

### HTML to JSON Extraction
```bash
python extract_mele.py "html_directory/" "output_directory/"
```

### Human-Readable Format
```bash
python format_human_readable.py "json_directory/" "text_output/"
```

## Data Organization

```
data/                     # Proprietary data (gitignored)
├── source_html/         # Original HTML files
├── extracted_json/      # Processed JSON data
├── human_readable/      # Text format for review
└── songbooks/          # Additional source materials
```

## Database Schema

The system uses a hub-and-spoke model centered on `canonical_mele_id`:

- **Canonical entries** establish authoritative information
- **Source entries** preserve original materials as-found
- **Variations** track different spellings and names
- **Media** links recordings and performances

This enables complete song pages showing both scholarly information and archival materials.

## Cultural Considerations

This system is designed with respect for Hawaiian culture:
- Preserves proper Hawaiian language diacriticals
- Maintains attribution to cultural practitioners
- Separates authoritative information from archival preservation
- Supports scholarly research while respecting source materials

## Contributing

This project preserves Hawaiian cultural heritage. Please approach contributions with appropriate cultural sensitivity and respect for the source materials.

## License

Please respect the cultural significance of this material and any existing copyrights on individual songs.