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
        const modal = document.getElementById('songModal');
        const closeBtn = document.querySelector('.close');
        
        // Search functionality
        searchInput.addEventListener('input', (e) => {
            this.filterSongs(e.target.value);
        });
        
        // Modal close events
        closeBtn.addEventListener('click', () => {
            this.closeModal();
        });
        
        window.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeModal();
            }
        });
        
        // Escape key to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
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
                <span class="song-link" onclick="app.showSongDetail('${song.canonical_mele_id}')">
                    ${this.formatFieldPlain(song.canonical_title_hawaiian)}
                </span>
                <span class="composer-info"> - ${this.formatFieldPlain(song.primary_composer)}</span>
            </div>
        `).join('');
    }
    
    async showSongDetail(songId) {
        const song = this.songs.find(s => s.canonical_mele_id === songId);
        if (!song) return;
        
        const detailsContainer = document.getElementById('songDetails');
        detailsContainer.innerHTML = this.renderSongDetail(song);
        
        document.getElementById('songModal').style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
    
    renderSongDetail(song) {
        return `
            <div class="song-header">
                <div class="song-title-main">${this.formatFieldPlain(song.canonical_title_hawaiian)}</div>
                <div class="song-composer-main">${this.formatFieldPlain(song.primary_composer)}</div>
            </div>
            
            <div class="song-content">
                <div class="left-sidebar">
                    ${song.source_file ? `
                        <div class="sidebar-section">
                            <div class="sidebar-title">Source:</div>
                            <div class="sidebar-content">${this.formatFieldPlain(song.source_file)}</div>
                        </div>
                    ` : ''}
                    
                    ${song.translator ? `
                        <div class="sidebar-section">
                            <div class="sidebar-title">Translator:</div>
                            <div class="sidebar-content">${this.formatFieldPlain(song.translator)}</div>
                        </div>
                    ` : ''}
                    
                    ${song.hawaiian_editor ? `
                        <div class="sidebar-section">
                            <div class="sidebar-title">Hawaiian Editor:</div>
                            <div class="sidebar-content">${this.formatFieldPlain(song.hawaiian_editor)}</div>
                        </div>
                    ` : ''}
                    
                    ${song.primary_location ? `
                        <div class="sidebar-section">
                            <div class="sidebar-title">Location:</div>
                            <div class="sidebar-content">${this.formatFieldPlain(song.primary_location)}</div>
                        </div>
                    ` : ''}
                    
                    ${song.youtube_urls && song.youtube_urls.length > 0 ? `
                        <div class="sidebar-section">
                            <div class="sidebar-title">Listen:</div>
                            <div class="sidebar-content">
                                ${song.youtube_urls.map(url => `
                                    <a href="${url}" target="_blank">YouTube</a><br>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
                
                <div class="main-content">
                    ${this.renderLyricsNew(song)}
                    
                    ${song.cultural_significance_notes ? `
                        <div class="cultural-notes">
                            <div class="notes-title">Cultural Significance:</div>
                            ${song.cultural_significance_notes}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    renderLyrics(song) {
        if (!song.verses || song.verses.length === 0) {
            return `
                <div class="detail-section">
                    <h3>Lyrics</h3>
                    <div class="empty-field">No lyrics available</div>
                </div>
            `;
        }
        
        return `
            <div class="detail-section">
                <h3>Hawaiian Lyrics</h3>
                ${song.verses.map(verse => `
                    <div class="lyrics-section">
                        <div class="verse-title">${verse.type === 'hui' ? 'Hui' : `Verse ${verse.order}`}</div>
                        <div class="verse-content hawaiian-text">${verse.hawaiian_text || 'No Hawaiian text available'}</div>
                    </div>
                `).join('')}
            </div>
            
            <div class="detail-section">
                <h3>English Translation</h3>
                ${song.verses.map(verse => `
                    <div class="lyrics-section">
                        <div class="verse-title">${verse.type === 'hui' ? 'Hui (Translation)' : `Verse ${verse.order} (Translation)`}</div>
                        <div class="verse-content english-text">${verse.english_text || 'No translation available'}</div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    formatField(value) {
        return value && value.trim() !== '' ? value : '<span class="empty-field">Not specified</span>';
    }
    
    formatFieldPlain(value) {
        return value && value.trim() !== '' ? value : 'Not specified';
    }
    
    renderLyricsNew(song) {
        if (!song.verses || song.verses.length === 0) {
            return `
                <div class="lyrics-container">
                    <div class="lyrics-title">Lyrics not available</div>
                </div>
            `;
        }
        
        // Combine all Hawaiian text
        const hawaiianText = song.verses.map(verse => verse.hawaiian_text || '').join('\n\n');
        const englishText = song.verses.map(verse => verse.english_text || '').join('\n\n');
        
        return `
            <div class="lyrics-container">
                <div class="lyrics-columns">
                    <div class="lyrics-hawaiian">${hawaiianText}</div>
                    <div class="lyrics-english">${englishText}</div>
                </div>
            </div>
        `;
    }
    
    closeModal() {
        document.getElementById('songModal').style.display = 'none';
        document.body.style.overflow = '';
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