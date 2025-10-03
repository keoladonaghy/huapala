// API integration layer for Huapala database
const API_BASE_URL = import.meta.env.VITE_RAILWAY_API_URL || 'http://localhost:8000';

export interface SongbookEntry {
  id?: number;
  timestamp?: string;
  printed_song_title: string;
  eng_title_transl?: string;
  modern_song_title?: string;
  scripped_song_title?: string;
  song_title?: string;
  songbook_name: string;
  page?: number;
  pub_year?: number;
  diacritics?: 'Yes' | 'No' | 'Inconsistent' | 'Unknown';
  composer?: string;
  additional_information?: string;
  email_address?: string;
  canonical_mele_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ReferenceSong {
  canonical_mele_id: string;
  canonical_title_hawaiian: string;
  canonical_title_english?: string;
  primary_composer: string;
}

export interface ReferencePerson {
  person_id: string;
  name: string;
  roles: string[];
}

class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = 'ApiError';
  }
}

// Generic API request handler
async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultHeaders = {
    'Content-Type': 'application/json',
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new ApiError(`API Error: ${response.status} ${response.statusText} - ${errorText}`, response.status);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

// Songbook Entries API
export const songbookApi = {
  // Get all songbook entries with optional filters
  async getEntries(params?: {
    limit?: number;
    offset?: number;
    songbook_name?: string;
    composer?: string;
    pub_year_min?: number;
    pub_year_max?: number;
    search?: string;
  }): Promise<SongbookEntry[]> {
    const searchParams = new URLSearchParams();
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }

    const query = searchParams.toString();
    return apiRequest<SongbookEntry[]>(`/api/songbook-entries${query ? `?${query}` : ''}`);
  },

  // Get single songbook entry by ID
  async getEntry(id: number): Promise<SongbookEntry> {
    return apiRequest<SongbookEntry>(`/api/songbook-entries/${id}`);
  },

  // Create new songbook entry
  async createEntry(entry: Omit<SongbookEntry, 'id' | 'created_at' | 'updated_at'>): Promise<SongbookEntry> {
    return apiRequest<SongbookEntry>('/api/songbook-entries', {
      method: 'POST',
      body: JSON.stringify(entry),
    });
  },

  // Update existing songbook entry
  async updateEntry(id: number, entry: Partial<SongbookEntry>): Promise<SongbookEntry> {
    return apiRequest<SongbookEntry>(`/api/songbook-entries/${id}`, {
      method: 'PUT',
      body: JSON.stringify(entry),
    });
  },

  // Delete songbook entry
  async deleteEntry(id: number): Promise<void> {
    return apiRequest<void>(`/api/songbook-entries/${id}`, {
      method: 'DELETE',
    });
  },

  // Get unique songbook names for dropdown
  async getSongbookNames(): Promise<string[]> {
    return apiRequest<string[]>('/api/songbook-names');
  },

  // Get entry statistics
  async getStats(): Promise<{
    total_entries: number;
    unique_songbooks: number;
    unique_composers: number;
    entries_with_pages: number;
    entries_by_decade: Array<{ decade: string; count: number }>;
  }> {
    return apiRequest('/api/songbook-stats');
  },
};

// Reference Data API (read-only)
export const referenceApi = {
  // Get canonical songs for linking/reference
  async getSongs(params?: {
    limit?: number;
    search?: string;
  }): Promise<ReferenceSong[]> {
    const searchParams = new URLSearchParams();
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }

    const query = searchParams.toString();
    return apiRequest<ReferenceSong[]>(`/api/canonical-mele${query ? `?${query}` : ''}`);
  },

  // Get people for composer/contributor reference
  async getPeople(params?: {
    limit?: number;
    search?: string;
    role?: string;
  }): Promise<ReferencePerson[]> {
    const searchParams = new URLSearchParams();
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }

    const query = searchParams.toString();
    return apiRequest<ReferencePerson[]>(`/api/people${query ? `?${query}` : ''}`);
  },
};

// Complex Operations API (Railway API coordination)
export const complexApi = {
  // Link a songbook entry to a canonical song
  async linkEntryToSong(entryId: number, songId: string): Promise<void> {
    return apiRequest<void>('/api/link-entry-song', {
      method: 'POST',
      body: JSON.stringify({
        entry_id: entryId,
        canonical_mele_id: songId,
      }),
    });
  },

  // Search across multiple tables
  async globalSearch(query: string): Promise<{
    songbook_entries: SongbookEntry[];
    canonical_songs: ReferenceSong[];
    people: ReferencePerson[];
  }> {
    return apiRequest(`/api/search?q=${encodeURIComponent(query)}`);
  },

  // Validate songbook entry data
  async validateEntry(entry: Partial<SongbookEntry>): Promise<{
    valid: boolean;
    errors: string[];
    warnings: string[];
  }> {
    return apiRequest('/api/validate-entry', {
      method: 'POST',
      body: JSON.stringify(entry),
    });
  },
};

// Export all APIs
export const api = {
  songbook: songbookApi,
  reference: referenceApi,
  complex: complexApi,
};

export default api;