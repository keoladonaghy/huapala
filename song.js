// Song Page JavaScript
class SongPage {
    constructor() {
        this.song = null;
        this.init();
    }
    
    init() {
        this.loadSong();
    }
    
    async loadSong() {
        try {
            // Get song ID from URL parameters
            const urlParams = new URLSearchParams(window.location.search);
            const songId = urlParams.get('id');
            
            if (!songId) {
                throw new Error('No song ID provided');
            }
            
            // Use Railway-hosted API
            const API_BASE_URL = window.location.hostname === 'localhost' 
                ? 'http://localhost:8000'  // Local development
                : 'https://web-production-cde73.up.railway.app';  // Production Railway API
            
            const response = await fetch(`${API_BASE_URL}/songs/${songId}`);
            if (!response.ok) {
                throw new Error(`Failed to load song: ${response.status}`);
            }
            
            this.song = await response.json();
            this.renderSong();
            this.hideLoading();
        } catch (error) {
            console.error('Error loading song:', error);
            this.showError();
        }
    }
    
    renderSong() {
        // Update page title
        document.title = `${this.formatField(this.song.canonical_title_hawaiian)} - Huapala`;
        
        // Render song header
        document.getElementById('songTitle').textContent = this.formatField(this.song.canonical_title_hawaiian);
        document.getElementById('songComposer').textContent = this.formatField(this.song.primary_composer);
        
        // Render sidebar
        this.renderSidebar();
        
        // Render lyrics table
        this.renderLyricsTable();
        
        // Render cultural notes if available
        if (this.song.cultural_significance_notes) {
            document.getElementById('culturalNotes').style.display = 'block';
            document.getElementById('notesContent').textContent = this.song.cultural_significance_notes;
        }
        
        document.getElementById('songContent').style.display = 'block';
    }
    
    renderSidebar() {
        const sidebarContent = document.getElementById('sidebarContent');
        let sidebarHTML = '';
        
        if (this.song.source_file) {
            sidebarHTML += `
                <div class="sidebar-section">
                    <div class="sidebar-title">Source:</div>
                    <div class="sidebar-content">${this.formatField(this.song.source_file)}</div>
                </div>
            `;
        }
        
        if (this.song.translator) {
            sidebarHTML += `
                <div class="sidebar-section">
                    <div class="sidebar-title">Translator:</div>
                    <div class="sidebar-content">${this.formatField(this.song.translator)}</div>
                </div>
            `;
        }
        
        if (this.song.hawaiian_editor) {
            sidebarHTML += `
                <div class="sidebar-section">
                    <div class="sidebar-title">Hawaiian Editor:</div>
                    <div class="sidebar-content">${this.formatField(this.song.hawaiian_editor)}</div>
                </div>
            `;
        }
        
        if (this.song.primary_location) {
            sidebarHTML += `
                <div class="sidebar-section">
                    <div class="sidebar-title">Location:</div>
                    <div class="sidebar-content">${this.formatField(this.song.primary_location)}</div>
                </div>
            `;
        }
        
        if (this.song.island) {
            sidebarHTML += `
                <div class="sidebar-section">
                    <div class="sidebar-title">Island:</div>
                    <div class="sidebar-content">${this.formatField(this.song.island)}</div>
                </div>
            `;
        }
        
        if (this.song.youtube_urls && this.song.youtube_urls.length > 0) {
            sidebarHTML += `
                <div class="sidebar-section">
                    <div class="sidebar-title">Listen:</div>
                    <div class="sidebar-content">
                        ${this.song.youtube_urls.map(url => `
                            <a href="${url}" target="_blank">YouTube</a><br>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        sidebarContent.innerHTML = sidebarHTML;
    }
    
    renderLyricsTable() {
        const lyricsTable = document.getElementById('lyricsTable');
        
        console.log('Song verses data:', this.song.verses); // Debug log
        
        if (!this.song.verses || this.song.verses.length === 0) {
            lyricsTable.innerHTML = `
                <tr>
                    <td colspan="2" style="text-align: center; color: #666; font-style: italic;">
                        No lyrics available
                    </td>
                </tr>
            `;
            return;
        }
        
        // Create table rows for each verse
        let tableHTML = '';
        
        this.song.verses.forEach((verse, index) => {
            console.log(`Verse ${index}:`, verse); // Debug log
            
            const hawaiianText = verse.hawaiian_text || '';
            const englishText = verse.english_text || '';
            
            // Try multiple line break formats and add manual breaks based on capital letters
            let hawaiianFormatted = hawaiianText
                .replace(/\r\n/g, '<br>')
                .replace(/\n/g, '<br>')
                .replace(/\r/g, '<br>');
            
            let englishFormatted = englishText
                .replace(/\r\n/g, '<br>')
                .replace(/\n/g, '<br>')
                .replace(/\r/g, '<br>');
            
            // If no <br> tags yet, try to break on capital letters (likely new lines)
            if (!hawaiianFormatted.includes('<br>') && hawaiianText.length > 50) {
                // Break before capital letters that start new phrases/lines
                hawaiianFormatted = hawaiianText.replace(/([a-z])\s+([A-ZĀĒĪŌŪ])/g, '$1<br>$2');
            }
            
            if (!englishFormatted.includes('<br>') && englishText.length > 50) {
                // Break before capital letters that start new phrases/lines
                englishFormatted = englishText.replace(/([a-z])\s+([A-Z])/g, '$1<br>$2');
            }
            
            // Add verse/chorus label if available
            let verseLabel = '';
            if (verse.type && verse.order) {
                verseLabel = verse.type === 'hui' ? 'Hui:' : `Verse ${verse.order}:`;
            }
            
            console.log(`Hawaiian formatted: "${hawaiianFormatted}"`); // Debug log
            console.log(`English formatted: "${englishFormatted}"`); // Debug log
            
            tableHTML += `
                <tr>
                    <td class="hawaiian-lyrics">
                        ${verseLabel ? `<strong>${verseLabel}</strong><br>` : ''}
                        ${hawaiianFormatted}
                    </td>
                    <td class="english-lyrics">
                        ${verseLabel ? `<strong>${verseLabel}</strong><br>` : ''}
                        ${englishFormatted}
                    </td>
                </tr>
            `;
            
            // Add spacing between verses
            if (index < this.song.verses.length - 1) {
                tableHTML += `
                    <tr>
                        <td colspan="2" style="height: 15px;"></td>
                    </tr>
                `;
            }
        });
        
        console.log('Generated table HTML:', tableHTML); // Debug log
        lyricsTable.innerHTML = tableHTML;
    }
    
    formatField(value) {
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

// Initialize the song page
const songPage = new SongPage();