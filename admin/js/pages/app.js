// Huapala Web App JavaScript
class HuapalaApp {
    constructor() {
        this.songs = [];
        this.searchInterface = null;
        this.init();
    }
    
    init() {
        this.loadSongs();
        this.setupEventListeners();
    }
    
    async loadSongs() {
        try {
            // Use database API for all song data
            const response = await fetch('/songs');
            if (!response.ok) {
                throw new Error(`Failed to load songs data: ${response.status}`);
            }
            const songs = await response.json();
            
            this.songs = songs;
            this.initializeSearch();
            this.hideLoading();
        } catch (error) {
            console.error('Error loading songs:', error);
            this.showError();
        }
    }
    
    initializeSearch() {
        // Create search interface using shared component
        this.searchInterface = createHuapalaSearch({
            containerId: 'mainSearch',
            placeholder: 'Search songs by title or composer...',
            songs: this.songs,
            onSongClick: (song) => {
                // Navigate to song page
                window.location.href = `song.html?id=${song.canonical_mele_id}`;
            },
            searchFields: ['canonical_title_hawaiian', 'canonical_title_english', 'primary_composer', 'primary_location', 'island']
        });
        
        this.searchInterface.init();
        
        // Listen for people icon clicks from search results
        document.addEventListener('peopleIconClick', (e) => {
            const { composer, songId } = e.detail;
            this.showSongModal(composer, songId);
        });
        
        // Modal functionality
        this.setupModalListeners();
    }
    
    setupEventListeners() {
        // Modal functionality only now
        this.setupModalListeners();
        
        // Page info icon functionality
        document.getElementById('pageInfoIcon').addEventListener('click', () => {
            this.showPageInfoModal();
        });
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
        
        // Handle tab switching
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('tab-button')) {
                this.switchTab(e.target.dataset.tab);
            }
        });
        
        // Handle people icon clicks
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('people-icon')) {
                e.preventDefault();
                const composerName = e.target.dataset.composer;
                const songId = e.target.dataset.songId;
                this.showSongModal(composerName, songId);
            }
        });
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
    
    switchTab(tabName) {
        // Remove active class from all tabs and contents
        document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        // Add active class to selected tab and content
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(`${tabName}Tab`).classList.add('active');
    }
    
    async showSongModal(composerName, songId) {
        const modal = document.getElementById('peopleModal');
        const modalTitle = document.getElementById('modalSongTitle');
        const metadataTab = document.getElementById('metadataTab');
        const composerTab = document.getElementById('composerTab');
        
        // Show modal and reset to first tab
        modal.style.display = 'block';
        this.switchTab('metadata');
        
        // Set loading states
        metadataTab.innerHTML = '<div class="modal-loading">Loading song details...</div>';
        composerTab.innerHTML = '<div class="modal-loading">Loading composer details...</div>';
        
        try {
            const API_BASE_URL = window.location.hostname === 'localhost' 
                ? 'http://localhost:8000'
                : 'https://web-production-cde73.up.railway.app';
            
            // Load song data and composer data in parallel
            const [songResponse, personResponse] = await Promise.all([
                fetch(`${API_BASE_URL}/songs/${encodeURIComponent(songId)}`),
                fetch(`${API_BASE_URL}/people/search?name=${encodeURIComponent(composerName)}`)
            ]);
            
            if (songResponse.ok) {
                const song = await songResponse.json();
                modalTitle.textContent = song.canonical_title_hawaiian || song.canonical_title_english || 'Song Details';
                this.renderSongMetadata(song, metadataTab);
            } else {
                metadataTab.innerHTML = '<div class="modal-error">Unable to load song details.</div>';
            }
            
            if (personResponse.ok) {
                const person = await personResponse.json();
                if (person) {
                    this.renderComposerDetails(person, composerTab);
                } else {
                    composerTab.innerHTML = `
                        <div class="modal-error">
                            No detailed information found for "${composerName}".
                            <br><br>
                            This person may not yet be in our biographical database.
                        </div>
                    `;
                }
            } else {
                composerTab.innerHTML = '<div class="modal-error">Unable to load composer details.</div>';
            }
            
        } catch (error) {
            console.error('Error loading modal data:', error);
            metadataTab.innerHTML = '<div class="modal-error">Unable to load song details.</div>';
            composerTab.innerHTML = '<div class="modal-error">Unable to load composer details.</div>';
        }
    }
    
    renderSongMetadata(song, container) {
        const formatArray = (arr) => {
            if (!arr || arr.length === 0) return 'Not specified';
            return Array.isArray(arr) ? arr.join(', ') : arr;
        };
        
        const formatField = (value) => {
            return value && value.trim() !== '' ? value : 'Not specified';
        };
        
        // Build contributors list
        let contributorsHTML = '';
        const contributors = [];
        
        if (song.primary_composer && song.primary_composer !== 'Not specified') {
            contributors.push({ name: song.primary_composer, role: 'Composer' });
        }
        if (song.composer && song.composer !== song.primary_composer && song.composer !== 'Not specified') {
            contributors.push({ name: song.composer, role: 'Additional Composer' });
        }
        if (song.primary_lyricist && song.primary_lyricist !== 'Not specified') {
            contributors.push({ name: song.primary_lyricist, role: 'Lyricist' });
        }
        if (song.translator && song.translator !== 'Not specified') {
            contributors.push({ name: song.translator, role: 'Translator' });
        }
        if (song.hawaiian_editor && song.hawaiian_editor !== 'Not specified') {
            contributors.push({ name: song.hawaiian_editor, role: 'Hawaiian Editor' });
        }
        
        if (contributors.length > 0) {
            contributorsHTML = `
                <div class="metadata-section">
                    <h3>Contributors</h3>
                    <div class="contributors-list">
                        ${contributors.map(c => `
                            <div class="contributor-item">
                                <span class="contributor-name">${c.name}</span>
                                <span class="contributor-role">${c.role}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // Build media links
        let mediaHTML = '';
        if (song.youtube_urls && song.youtube_urls.length > 0) {
            mediaHTML = `
                <div class="metadata-section">
                    <h3>Media Links</h3>
                    <div class="media-links">
                        ${song.youtube_urls.map((url, index) => `
                            <a href="${url}" target="_blank" class="media-link">YouTube ${index + 1}</a>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        container.innerHTML = `
            ${contributorsHTML}
            
            <div class="metadata-section">
                <h3>Publication Information</h3>
                <div class="metadata-field">
                    <span class="metadata-label">Source File:</span>
                    <span class="metadata-value">${formatField(song.source_file)}</span>
                </div>
                <div class="metadata-field">
                    <span class="metadata-label">Publication:</span>
                    <span class="metadata-value">${formatField(song.source_publication)}</span>
                </div>
                <div class="metadata-field">
                    <span class="metadata-label">Copyright:</span>
                    <span class="metadata-value">${formatField(song.copyright_info)}</span>
                </div>
                <div class="metadata-field">
                    <span class="metadata-label">Composition Date:</span>
                    <span class="metadata-value">${formatField(song.estimated_composition_date)}</span>
                </div>
            </div>
            
            <div class="metadata-section">
                <h3>Cultural Context</h3>
                <div class="metadata-field">
                    <span class="metadata-label">Location:</span>
                    <span class="metadata-value">${formatField(song.primary_location)}</span>
                </div>
                <div class="metadata-field">
                    <span class="metadata-label">Island:</span>
                    <span class="metadata-value">${formatField(song.island)}</span>
                </div>
                <div class="metadata-field">
                    <span class="metadata-label">Mele Type:</span>
                    <span class="metadata-value">${formatField(song.mele_type)}</span>
                </div>
                <div class="metadata-field">
                    <span class="metadata-label">Themes:</span>
                    <span class="metadata-value">${formatArray(song.themes)}</span>
                </div>
                <div class="metadata-field">
                    <span class="metadata-label">Cultural Elements:</span>
                    <span class="metadata-value">${formatArray(song.cultural_elements)}</span>
                </div>
                ${song.cultural_significance_notes ? `
                    <div class="metadata-field">
                        <span class="metadata-label">Cultural Notes:</span>
                        <div class="metadata-value" style="margin-top: 4px; line-height: 1.4;">${song.cultural_significance_notes}</div>
                    </div>
                ` : ''}
            </div>
            
            ${mediaHTML}
        `;
    }
    
    renderComposerDetails(person, container) {
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
    
    showPageInfoModal() {
        const modal = document.getElementById('peopleModal');
        const modalTitle = document.getElementById('modalSongTitle');
        const metadataTab = document.getElementById('metadataTab');
        const composerTab = document.getElementById('composerTab');
        
        // Set modal title
        modalTitle.textContent = 'About This Page';
        
        // Show modal and reset to first tab
        modal.style.display = 'block';
        this.switchTab('metadata');
        
        // Set page info content
        metadataTab.innerHTML = `
            <div class="metadata-section">
                <h3>Huapala Hawaiian Music Archives</h3>
                <div class="metadata-field">
                    <span class="metadata-label">Purpose:</span>
                    <span class="metadata-value">Digital archive of Hawaiian music lyrics, composers, and cultural information</span>
                </div>
                <div class="metadata-field">
                    <span class="metadata-label">Total Songs:</span>
                    <span class="metadata-value">${this.songs.length} songs</span>
                </div>
                <div class="metadata-field">
                    <span class="metadata-label">Search Features:</span>
                    <span class="metadata-value">Hawaiian text normalization, composer search, location search</span>
                </div>
                <div class="metadata-field">
                    <span class="metadata-label">Language Support:</span>
                    <span class="metadata-value">Hawaiian and English lyrics with cultural context</span>
                </div>
            </div>
        `;
        
        // Set help/usage info
        composerTab.innerHTML = `
            <div class="person-details">
                <div class="person-field">
                    <span class="person-label">Search Tips:</span>
                    <span class="person-value">Type any Hawaiian or English text. The search ignores diacritical marks and ʻokina.</span>
                </div>
                
                <div class="person-field">
                    <span class="person-label">Examples:</span>
                    <span class="person-value">Try "aloha", "pua", "Charles King", or "Puna"</span>
                </div>
                
                <div class="person-field">
                    <span class="person-label">Results Layout:</span>
                    <span class="person-value">Songs are distributed across three columns for easy browsing</span>
                </div>
                
                <div class="person-field">
                    <span class="person-label">Song Pages:</span>
                    <span class="person-value">Click any song title to view full lyrics with Hawaiian and English text</span>
                </div>
                
                <div class="person-field">
                    <span class="person-label">Cultural Context:</span>
                    <span class="person-value">Many songs include historical and cultural significance notes</span>
                </div>
            </div>
        `;
        
        // Update tab labels for page info
        document.querySelector('[data-tab="metadata"]').textContent = 'About';
        document.querySelector('[data-tab="composer"]').textContent = 'Usage';
    }
}

// Initialize the app
const app = new HuapalaApp();