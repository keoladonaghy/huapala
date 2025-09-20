# Huapala Scripts Directory

This directory contains all Python scripts for the Huapala Hawaiian Music Archives project.

## Core Processing Scripts

- **`json_first_processor.py`** - Main processor for HTML-to-JSON-to-Database workflow
- **`batch_processor.py`** - Batch processing and validation of HTML files  
- **`raw_html_parser.py`** - Parser for raw HTML files (handles source_html directory)
- **`enhanced_html_parser.py`** - Enhanced parser with BeautifulSoup support
- **`html_parser_with_validation.py`** - Parser for cleaned HTML files with validation

## Database & Validation Scripts

- **`data_validation_system.py`** - Core validation framework and rules
- **`database_validator.py`** - Database-integrated validation system
- **`migrate_to_postgres.py`** - Database migration utilities
- **`import_people_to_db.py`** - Import people/contributor data to database

## Utility Scripts

- **`export_to_web.py`** - Export data for web interface
- **`extract_mele.py`** - Song extraction utilities
- **`format_human_readable.py`** - Format data for human review

## Testing & Validation

- **`test_validation_integration.py`** - Test validation system integration
- **`check_schema.py`** - Database schema validation
- **`check_canonical_mele_structure.py`** - Check song data structure

## Usage

All scripts should be run from the project root directory:

```bash
# Process raw HTML files
python3 scripts/json_first_processor.py parse data/source_html/

# Import reviewed JSON to database  
python3 scripts/json_first_processor.py import

# Run validation tests
python3 scripts/test_validation_integration.py
```

## Dependencies

Scripts automatically handle imports from the root directory and maintain relationships with:
- `data/` directory (source files, output files)
- Database connections (Neon PostgreSQL)
- Web interface files