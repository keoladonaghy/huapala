# API Reference - Lovable Admin System

## 🎯 Overview
This document outlines the API endpoints and data operations available to the Lovable admin system.

## 🔗 Neon Data API Endpoints

### Base Configuration
```javascript
const NEON_API_BASE = 'https://[your-project].neon.tech/api/v1'
const API_KEY = process.env.NEON_API_KEY
```

### Songbook Entries Operations

#### List Songbook Entries
```http
GET /songbook_entries
```

**Query Parameters:**
- `limit` - Number of records (default: 20, max: 100)
- `offset` - Pagination offset
- `order` - Sort order (e.g., `id.asc`, `pub_year.desc`)
- `songbook_name` - Filter by songbook name
- `pub_year` - Filter by publication year (supports `gte`, `lte`)
- `composer` - Filter by composer (supports `ilike` for partial matches)

**Example:**
```javascript
// Get recent entries from a specific songbook
GET /songbook_entries?songbook_name=eq.Hawaiian Songs Collection&order=created_at.desc&limit=50
```

#### Get Single Entry
```http
GET /songbook_entries?id=eq.123
```

#### Create New Entry
```http
POST /songbook_entries
Content-Type: application/json

{
  "printed_song_title": "Aloha ʻOe",
  "songbook_name": "Hawaiian Songs Collection",
  "page": 45,
  "pub_year": 1985,
  "composer": "Queen Liliʻuokalani",
  "diacritics": "Yes",
  "additional_information": "Traditional Hawaiian farewell song"
}
```

#### Update Entry
```http
PATCH /songbook_entries?id=eq.123
Content-Type: application/json

{
  "page": 46,
  "additional_information": "Updated page reference"
}
```

#### Delete Entry
```http
DELETE /songbook_entries?id=eq.123
```

### Reference Data (Read-Only)

#### Get Songs for Reference
```http
GET /canonical_mele?select=canonical_mele_id,canonical_title_hawaiian,primary_composer&limit=1000
```

#### Get People for Reference  
```http
GET /people?select=person_id,name,roles&limit=1000
```

## 🚂 Railway API Integration

For operations beyond simple CRUD, proxy to Railway API:

### Complex Search
```javascript
const searchSongs = async (query) => {
  const response = await fetch(`${RAILWAY_API_URL}/search?q=${encodeURIComponent(query)}`);
  return response.json();
};
```

### Link Song to Songbook Entry
```javascript
const linkSongToEntry = async (songId, entryId) => {
  const response = await fetch(`${RAILWAY_API_URL}/link-song-songbook`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      canonical_mele_id: songId, 
      songbook_entry_id: entryId 
    })
  });
  return response.json();
};
```

## 📊 Common Query Patterns

### Pagination
```javascript
const getPaginatedEntries = async (page = 0, pageSize = 20) => {
  const offset = page * pageSize;
  return fetch(`/songbook_entries?limit=${pageSize}&offset=${offset}&order=id.asc`);
};
```

### Search and Filter
```javascript
// Search by title (case-insensitive)
const searchByTitle = (searchTerm) => {
  return fetch(`/songbook_entries?printed_song_title=ilike.*${searchTerm}*`);
};

// Filter by year range
const filterByYearRange = (startYear, endYear) => {
  return fetch(`/songbook_entries?pub_year=gte.${startYear}&pub_year=lte.${endYear}`);
};

// Filter by songbook
const filterBySongbook = (songbookName) => {
  return fetch(`/songbook_entries?songbook_name=eq.${encodeURIComponent(songbookName)}`);
};
```

### Aggregation
```javascript
// Count entries by songbook
const getSongbookCounts = () => {
  return fetch('/songbook_entries?select=songbook_name,count(*)&group_by=songbook_name');
};

// Get unique songbooks
const getUniqueSongbooks = () => {
  return fetch('/songbook_entries?select=songbook_name&group_by=songbook_name&order=songbook_name.asc');
};
```

## 🔒 Security & Validation

### Input Validation
```javascript
const validateEntry = (entry) => {
  const errors = [];
  
  if (!entry.songbook_name) {
    errors.push('Songbook name is required');
  }
  
  if (entry.pub_year && (entry.pub_year < 1800 || entry.pub_year > 2100)) {
    errors.push('Publication year must be between 1800 and 2100');
  }
  
  if (entry.page && entry.page < 1) {
    errors.push('Page number must be positive');
  }
  
  if (entry.email_address && !isValidEmail(entry.email_address)) {
    errors.push('Invalid email format');
  }
  
  if (entry.diacritics && !['Yes', 'No', 'Inconsistent', 'Unknown'].includes(entry.diacritics)) {
    errors.push('Invalid diacritics value');
  }
  
  return errors;
};
```

### Rate Limiting
```javascript
// Implement request queuing for bulk operations
const requestQueue = [];
const processQueue = async () => {
  while (requestQueue.length > 0) {
    const request = requestQueue.shift();
    await request();
    await new Promise(resolve => setTimeout(resolve, 100)); // 100ms delay
  }
};
```

## 🐛 Error Handling

### Standard Error Responses
```javascript
const handleApiError = (error) => {
  if (error.status === 400) {
    return 'Invalid request data';
  } else if (error.status === 401) {
    return 'Authentication required';
  } else if (error.status === 403) {
    return 'Access denied';
  } else if (error.status === 404) {
    return 'Record not found';
  } else if (error.status === 409) {
    return 'Conflict - record already exists';
  } else if (error.status >= 500) {
    return 'Server error - please try again';
  }
  return 'Unknown error occurred';
};
```

### Retry Logic
```javascript
const withRetry = async (apiCall, maxRetries = 3) => {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await apiCall();
    } catch (error) {
      if (attempt === maxRetries || error.status < 500) {
        throw error;
      }
      await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
    }
  }
};
```

## 📝 Usage Examples

### Complete CRUD Example
```javascript
// Create a new songbook entry
const createEntry = async (entryData) => {
  try {
    const errors = validateEntry(entryData);
    if (errors.length > 0) {
      throw new Error(errors.join(', '));
    }
    
    const response = await fetch('/songbook_entries', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(entryData)
    });
    
    if (!response.ok) {
      throw new Error(handleApiError(response));
    }
    
    return response.json();
  } catch (error) {
    console.error('Failed to create entry:', error);
    throw error;
  }
};

// Update an existing entry
const updateEntry = async (id, updates) => {
  const response = await fetch(`/songbook_entries?id=eq.${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates)
  });
  
  return response.json();
};

// Delete an entry
const deleteEntry = async (id) => {
  const response = await fetch(`/songbook_entries?id=eq.${id}`, {
    method: 'DELETE'
  });
  
  return response.ok;
};
```

This API reference provides everything needed to build efficient database maintenance interfaces while respecting the system boundaries defined in the coordination guide.