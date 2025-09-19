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
        
        // Modal functionality
        this.setupModalListeners();
    }
    
    setupModalListeners() {
        const modal = document.getElementById('peopleModal');
        const closeBtn = document.getElementById('closeModal');
        
        // Close modal when clicking X
        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
        
        // Close modal when clicking outside
        window.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
        
        // Handle people icon clicks
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('people-icon')) {
                e.preventDefault();
                const composerName = e.target.dataset.composer;
                this.showPersonModal(composerName);
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
                <a href="song.html?id=${song.canonical_mele_id}" class="song-link">
                    ${this.formatFieldPlain(song.canonical_title_hawaiian)}
                </a>
                <span class="composer-info"> - ${this.formatFieldPlain(song.primary_composer)}</span>
                ${song.primary_composer && song.primary_composer.trim() !== '' && song.primary_composer !== 'Not specified' ? 
                    `<span class="people-icon" data-composer="${song.primary_composer}" title="View composer details">🔍</span>` : 
                    ''
                }
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
    
    async showPersonModal(composerName) {
        const modal = document.getElementById('peopleModal');
        const modalContent = document.getElementById('modalContent');
        const modalTitle = document.getElementById('modalPersonName');
        
        // Show modal with loading state
        modal.style.display = 'block';
        modalTitle.textContent = composerName;
        modalContent.innerHTML = '<div class="modal-loading">Loading person details...</div>';
        
        try {
            const API_BASE_URL = window.location.hostname === 'localhost' 
                ? 'http://localhost:8000'
                : 'https://web-production-cde73.up.railway.app';
            
            // Search for person by name
            const response = await fetch(`${API_BASE_URL}/people/search?name=${encodeURIComponent(composerName)}`);
            
            if (!response.ok) {
                throw new Error(`Failed to load person data: ${response.status}`);
            }
            
            const person = await response.json();
            
            if (!person) {
                modalContent.innerHTML = `
                    <div class="modal-error">
                        No detailed information found for "${composerName}".
                        <br><br>
                        This person may not yet be in our biographical database.
                    </div>
                `;
                return;
            }
            
            this.renderPersonDetails(person, modalContent);
            
        } catch (error) {
            console.error('Error loading person details:', error);
            modalContent.innerHTML = `
                <div class="modal-error">
                    Unable to load biographical information for "${composerName}".
                    <br><br>
                    Please try again later.
                </div>
            `;
        }
    }
    
    renderPersonDetails(person, container) {
        const photoHTML = person.photo_url ? 
            `<img src="${person.photo_url}" alt="${person.full_name}" class="person-photo">` : '';
        
        const formatDate = (dateStr) => {
            if (!dateStr) return 'Unknown';
            // Handle different date formats
            if (dateStr.includes('-')) {
                const date = new Date(dateStr);
                return date.toLocaleDateString('en-US', { 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                });
            }
            return dateStr; // Return as-is if it's already formatted
        };
        
        const formatArray = (arr) => {
            if (!arr || arr.length === 0) return 'Not specified';
            return arr.join(', ');
        };
        
        const rolesDisplay = person.roles ? person.roles.join(', ') : 'Not specified';
        const worksDisplay = person.notable_works ? person.notable_works.join(', ') : 'Not specified';
        
        container.innerHTML = `
            ${photoHTML}
            <div class="person-details">
                <div class="person-field">
                    <span class="person-label">Birth Date:</span>
                    <span class="person-value">${formatDate(person.birth_date)}</span>
                </div>
                
                <div class="person-field">
                    <span class="person-label">Death Date:</span>
                    <span class="person-value">${formatDate(person.death_date)}</span>
                </div>
                
                <div class="person-field">
                    <span class="person-label">Place of Birth:</span>
                    <span class="person-value">${person.place_of_birth || 'Not specified'}</span>
                </div>
                
                <div class="person-field">
                    <span class="person-label">Hawaiian Language Influence:</span>
                    <span class="person-value">${person.primary_influence_location || 'Not specified'}</span>
                </div>
                
                <div class="person-field">
                    <span class="person-label">Cultural Background:</span>
                    <span class="person-value">${person.cultural_background || 'Not specified'}</span>
                </div>
                
                <div class="person-field">
                    <span class="person-label">Roles:</span>
                    <span class="person-value">${rolesDisplay}</span>
                </div>
                
                <div class="person-field">
                    <span class="person-label">Notable Works:</span>
                    <span class="person-value">${worksDisplay}</span>
                </div>
                
                <div class="person-field">
                    <span class="person-label">Hawaiian Speaker:</span>
                    <span class="person-value">${person.hawaiian_speaker === true ? 'Yes' : person.hawaiian_speaker === false ? 'No' : 'Unknown'}</span>
                </div>
                
                ${person.biographical_notes ? `
                    <div class="biographical-notes">
                        <div class="person-label">Biographical Notes:</div>
                        <div class="person-value">${person.biographical_notes}</div>
                    </div>
                ` : ''}
            </div>
        `;
    }
}

// Initialize the app
const app = new HuapalaApp();