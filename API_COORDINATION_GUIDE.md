# Huapala Hawaiian Music Database - API Coordination Guide

## 🎯 System Architecture Overview

This document defines the coordination between two API systems for the Huapala Hawaiian Music Archives:

- **Railway API (Claude Code)** - Complex operations, business logic, and data processing
- **Neon Data API (Lovable AI)** - Simple CRUD operations and frontend data management

## 🏗️ Current System Status

### Database Infrastructure
- **Database**: Neon PostgreSQL
- **Primary API**: Railway (web-production-cde73.up.railway.app)
- **Frontend**: GitHub Pages (keoladonaghy.github.io/huapala)

### Tables Overview
```sql
-- Main song database
canonical_mele (primary song records with metadata)
mele_sources (source files and verses_json)
people (contributors, composers, translators)

-- Songbook index (2,109 entries)
songbook_entries (Hawaiian songbook indexes across multiple publications)
```

---

## 🚂 Railway API (Claude Code) - Complex Operations

**Primary Role**: Data processing, business logic, and complex queries

### ✅ Assigned Responsibilities

#### **Song Data Management**
- Song parsing and import (HTML → JSON → Database)
- Song validation and quality scoring
- Canonical song CRUD operations (`canonical_mele` table)
- Song verse/lyrics management (complex JSON structures)
- Song-to-songbook linking and relationship management

#### **Advanced Search & Discovery**
- Full-text search across multiple tables
- Complex song searches with metadata filtering
- People/contributor searches with role-based filtering
- Advanced filtering (by decade, location, composer, diacritics)
- Search result ranking and relevance scoring

#### **Data Processing Workflows**
- Batch processing and import scripts
- Data validation and cleanup operations
- Foreign key relationship management
- Business logic validation
- File processing and HTML parsing

#### **Analytics & Reporting**
- Song collection statistics and dashboards
- Composer/contributor analytics
- Data quality reports and validation summaries
- Cross-reference analysis between tables

### 🔗 Current API Endpoints
```
GET  /songs                    # Search songs with complex filtering
GET  /songs/{id}              # Get single song with full metadata
GET  /people                  # Search contributors with role filtering
GET  /people/{id}             # Get person details with song relationships
```

---

## 🔗 Neon Data API (Lovable AI) - Simple CRUD Operations

**Primary Role**: Frontend data management and simple database operations

### ✅ Assigned Responsibilities

#### **Songbook Entries Management**
- CREATE: Add new songbook entries
- READ: Fetch songbook entries (simple queries)
- UPDATE: Edit songbook entry details (title, page, composer, etc.)
- DELETE: Remove songbook entries
- LIST: Paginated songbook browsing

#### **Simple Filtering & Sorting**
- Filter by single columns (songbook_name, pub_year, page, etc.)
- Basic sorting operations
- Simple pagination with LIMIT/OFFSET
- Basic text searches within single fields

#### **UI Data Operations**
- Form data submission and validation
- Simple lookups for dropdowns and selectors
- Basic required field and data type validation
- Real-time form updates and autosave

#### **Read-Only Display Data**
- Songbook browsing interfaces
- Entry detail views and simple listings
- Basic statistics (counts, totals by category)
- Simple data export operations

### 🎯 Target Table: `songbook_entries`

**Primary focus on the songbook index table with these fields:**
```sql
id                     (Primary key)
printed_song_title     (Song title as printed)
eng_title_transl      (English translation)
modern_song_title     (Standardized title)
songbook_name         (Publication name)
page                  (Page number)
pub_year              (Publication year)
composer              (Song composer)
diacritics            (Yes/No/Inconsistent/Unknown)
additional_information (Notes and details)
email_address         (Contributor contact)
canonical_mele_id     (Foreign key - manage via Railway API)
```

---

## 🚫 Boundary Rules - What Goes Where

### ❌ Railway API Required When:
- **Multi-table joins** are needed
- **Complex WHERE clauses** with multiple conditions
- **Data validation** beyond basic type checking
- **Foreign key operations** (linking songs to songbooks)
- **Business logic** needs to be applied
- **File uploads** or processing workflows
- **Full-text search** across multiple fields/tables
- **Complex aggregations** or analytics

### ✅ Neon Data API Appropriate When:
- **Single table** operations only
- **Simple filters** on one or two columns
- **Basic CRUD** with no complex validation
- **UI-driven** real-time operations
- **Form submissions** with standard validation
- **Simple counting** or basic aggregation
- **Direct user interactions** with clear data boundaries

---

## 📋 Implementation Examples

### **Songbook Entry Management**

#### ✅ Neon Data API Operations
```javascript
// Add new songbook entry
POST /songbook_entries
{
  "printed_song_title": "Aloha ʻOe",
  "songbook_name": "Hawaiian Songs Collection",
  "page": 45,
  "pub_year": 1985,
  "composer": "Queen Liliʻuokalani"
}

// Update entry details
PATCH /songbook_entries/123
{
  "page": 46,
  "additional_information": "Updated page reference"
}

// Simple filtering
GET /songbook_entries?songbook_name=Hawaiian Songs Collection&limit=20

// Basic search within songbook
GET /songbook_entries?printed_song_title=ilike.*Aloha*
```

#### ❌ Railway API Operations
```javascript
// Link songbook entry to canonical song (complex validation)
POST /link-song-songbook
{
  "songbook_entry_id": 123,
  "canonical_mele_id": "aloha_oe_canonical"
}

// Search across songs and songbook entries
GET /search?q=Aloha Oe&include_songbooks=true

// Complex analytics
GET /analytics/songbook-coverage
```

### **Search Operations**

#### ✅ Neon Data API - Simple Searches
```javascript
// Filter by publication year
GET /songbook_entries?pub_year=gte.1950&pub_year=lte.2000

// Sort by page number
GET /songbook_entries?order=page.asc

// Count entries by songbook
GET /songbook_entries?select=songbook_name,count(*)&group_by=songbook_name
```

#### ❌ Railway API - Complex Searches
```javascript
// Full-text search across multiple tables
GET /search?q=Hawaiian love song&type=comprehensive

// Find songs with songbook references
GET /songs/with-songbook-entries

// Advanced filtering with relationships
GET /songs?composer=Queen Liliuokalani&has_songbook_entry=true
```

---

## 🛠️ Technical Coordination

### **Connection Management**
- **Concurrent Access**: Both APIs can safely access Neon PostgreSQL simultaneously
- **Connection Pooling**: PostgreSQL handles multiple connections efficiently
- **Transaction Isolation**: Each API operates independently with ACID compliance

### **Data Consistency**
- **Foreign Keys**: Neon Data API should NOT directly modify `canonical_mele_id`
- **Validation**: Railway API handles complex validation; Neon API does basic validation
- **Schema Changes**: Coordinate any table structure modifications

### **Error Handling**
```javascript
// Recommended error boundary pattern
const apiCall = async (operation, data) => {
  try {
    if (COMPLEX_OPERATIONS.includes(operation)) {
      return await railwayAPI(operation, data);
    } else {
      return await neonDataAPI(operation, data);
    }
  } catch (error) {
    // Log errors with API source for debugging
    console.error(`Error in ${error.api}: ${error.message}`);
    throw error;
  }
};
```

---

## 🎯 Recommended Implementation Phases

### **Phase 1: Read-Only Operations (Recommended Start)**
1. Enable Neon Data API access
2. Test simple SELECT queries for songbook browsing
3. Verify no conflicts with Railway API
4. Implement basic songbook entry display interfaces

### **Phase 2: Simple CRUD Operations**
1. Add songbook entry creation forms
2. Implement edit/update functionality
3. Test concurrent read/write operations
4. Monitor database performance and connection usage

### **Phase 3: Advanced UI Features**
1. Complex filtering and sorting interfaces
2. Bulk operations (where appropriate)
3. Real-time updates and autosave
4. Integration with Railway API for linking operations

---

## 📊 Operation Reference Matrix

| Operation | API Choice | Reason | Example |
|-----------|------------|--------|---------|
| Add songbook entry | Neon Data API | Simple INSERT | Form submission |
| Search songs by title | Railway API | Multi-table + ranking | Main search bar |
| Edit entry page number | Neon Data API | Simple UPDATE | Inline editing |
| Link song to songbook | Railway API | Foreign key validation | Admin workflow |
| Browse songbook list | Neon Data API | Simple SELECT + pagination | Songbook gallery |
| Import song from HTML | Railway API | Complex processing | Batch import |
| Filter by publication year | Neon Data API | Simple WHERE clause | Year selector |
| Song analytics dashboard | Railway API | Complex aggregation | Statistics page |
| Delete songbook entry | Neon Data API | Simple DELETE | Admin removal |
| Validate song data | Railway API | Business logic | Data quality check |

---

## 🔒 Security Considerations

### **Neon Data API Access**
- Use Row Level Security (RLS) if implementing user authentication
- Restrict API access to specific tables (`songbook_entries` primarily)
- Implement rate limiting to prevent abuse
- Use environment variables for API credentials

### **Railway API Protection**
- Maintain CORS configuration for GitHub Pages domain
- Keep complex business logic server-side
- Validate all inputs before database operations
- Log API usage for monitoring

---

## 📞 Support & Coordination

### **When to Use Railway API (Claude Code)**
- Complex operations requiring business logic
- Multi-table operations and joins
- Data import and processing workflows
- Advanced search and analytics
- Foreign key relationship management

### **When to Use Neon Data API (Lovable)**
- Simple form submissions and updates
- Basic filtering and display operations
- Real-time UI interactions
- Single-table CRUD operations
- Simple user interface data management

### **Coordination Points**
- Schema changes must be communicated to both systems
- Foreign key operations should remain with Railway API
- Complex validation logic stays server-side
- Simple UI operations can use direct database access

---

## 🚀 Getting Started

1. **Enable Neon Data API** in your Neon console
2. **Test read operations** first with simple songbook queries
3. **Implement basic CRUD** for songbook entries
4. **Coordinate with Railway API** for any linking operations
5. **Monitor performance** and connection usage
6. **Document any issues** or edge cases discovered

This hybrid approach maximizes development efficiency while maintaining data integrity and system performance.

---

*Last Updated: September 2025*  
*Prepared for Lovable AI Integration*