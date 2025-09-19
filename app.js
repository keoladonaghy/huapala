// Huapala Web App JavaScript
class HuapalaApp {
    constructor() {
        this.songs = [];
        this.filteredSongs = [];
        this.init();
    }
    
    init() {
        this.loadSongs();
        this.setupEventListeners();
    }
    
    async loadSongs() {
        try {
            // Use Railway-hosted API that connects to Neon PostgreSQL
            const API_BASE_URL = window.location.hostname === 'localhost' 
                ? 'http://localhost:8000'  // Local development
                : 'https://web-production-cde73.up.railway.app';  // Production Railway API
            
            const response = await fetch(`${API_BASE_URL}/songs`);
            if (!response.ok) {
                throw new Error(`Failed to load songs data: ${response.status}`);
            }
            
            this.songs = await response.json();
            this.filteredSongs = [...this.songs];
            this.renderSongs();
            this.hideLoading();
        } catch (error) {
            console.error('Error loading songs:', error);
            this.showError();
        }
    }
    
    setupEventListeners() {
        const searchInput = document.getElementById('searchInput');
        
        // Search functionality
        searchInput.addEventListener('input', (e) => {
            this.filterSongs(e.target.value);
        });
    }
    
    filterSongs(searchTerm) {
        const term = searchTerm.toLowerCase();
        this.filteredSongs = this.songs.filter(song => 
            song.canonical_title_hawaiian?.toLowerCase().includes(term) ||
            song.canonical_title_english?.toLowerCase().includes(term) ||
            song.primary_composer?.toLowerCase().includes(term) ||
            song.primary_location?.toLowerCase().includes(term) ||
            song.island?.toLowerCase().includes(term)
        );
        this.renderSongs();
    }
    
    renderSongs() {
        const container = document.getElementById('songsContainer');
        container.style.display = 'block';
        
        if (this.filteredSongs.length === 0) {
            container.innerHTML = '<div class="error">No songs found matching your search.</div>';
            return;
        }
        
        container.innerHTML = this.filteredSongs.map(song => `
            <div class="song-entry">
                <a href="song.html?id=${song.canonical_mele_id}" class="song-link">
                    ${this.formatFieldPlain(song.canonical_title_hawaiian)}
                </a>
                <span class="composer-info"> - ${this.formatFieldPlain(song.primary_composer)}</span>
            </div>
        `).join('');
    }
    
    
    formatField(value) {
        return value && value.trim() !== '' ? value : '<span class="empty-field">Not specified</span>';
    }
    
    formatFieldPlain(value) {
        return value && value.trim() !== '' ? value : 'Not specified';
    }
    
    hideLoading() {
        document.getElementById('loadingMessage').style.display = 'none';
    }
    
    showError() {
        document.getElementById('loadingMessage').style.display = 'none';
        document.getElementById('errorMessage').style.display = 'block';
    }
}

// Initialize the app
const app = new HuapalaApp();