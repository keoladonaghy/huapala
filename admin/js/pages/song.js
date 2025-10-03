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
            
            // Fetch song directly from database API
            const response = await fetch(`/songs/${songId}`);
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error(`Song with ID "${songId}" not found`);
                }
                throw new Error(`Failed to load song data: ${response.status}`);
            }
            this.song = await response.json();
            
            console.log('DEBUG: Song loaded from database API:', this.song);
            
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
        
        
        // Render lyrics in new flexible layout
        this.renderLyrics();
        
        // Render cultural notes if available
        if (this.song.cultural_significance_notes) {
            document.getElementById('culturalNotes').style.display = 'block';
            document.getElementById('notesContent').textContent = this.song.cultural_significance_notes;
        }
        
        document.getElementById('songContent').style.display = 'block';
    }
    
    
    renderLyrics() {
        const lyricsContainer = document.getElementById('songLyrics');
        const isPrintVersion = window.location.pathname.includes('song-print.html');
        
        // Check print format parameter
        const urlParams = new URLSearchParams(window.location.search);
        const printFormat = urlParams.get('format') || 'with-translation';
        const isLyricsOnly = printFormat === 'lyrics-only';
        
        console.log('Song verses data:', this.song.verses); // Debug log
        console.log('Print version:', isPrintVersion, 'Format:', printFormat); // Debug log
        
        if (!this.song.verses || this.song.verses.length === 0) {
            lyricsContainer.innerHTML = `
                <div style="text-align: center; color: #666; font-style: italic; padding: 40px;">
                    No lyrics available
                </div>
            `;
            return;
        }
        
        // Create verse containers for each verse
        let lyricsHTML = '';
        
        this.song.verses.forEach((verse, index) => {
            console.log(`Verse ${index}:`, verse); // Debug log
            
            let hawaiianLines = [];
            let englishLines = [];
            
            // Handle new format with lines array
            if (verse.lines && Array.isArray(verse.lines)) {
                hawaiianLines = verse.lines.map(line => line.hawaiian_text || '').filter(text => text.trim());
                englishLines = verse.lines.map(line => line.english_text || '').filter(text => text.trim());
            }
            // Fallback to old format
            else {
                const hawaiianText = verse.hawaiian_text || '';
                const englishText = verse.english_text || '';
                
                // Split by line breaks
                hawaiianLines = hawaiianText
                    .replace(/\r\n/g, '\n')
                    .replace(/\r/g, '\n')
                    .split('\n')
                    .filter(line => line.trim());
                
                englishLines = englishText
                    .replace(/\r\n/g, '\n')
                    .replace(/\r/g, '\n')
                    .split('\n')
                    .filter(line => line.trim());
                
                // If no line breaks found, apply intelligent breaking for Hawaiian songs
                if (hawaiianLines.length === 1 && hawaiianText.length > 50) {
                    const reformatted = this.reconstructHawaiianLines(hawaiianText);
                    hawaiianLines = reformatted.split('<br>').filter(line => line.trim());
                }
                
                if (englishLines.length === 1 && englishText.length > 50) {
                    const reformatted = this.reconstructEnglishLines(englishText);
                    englishLines = reformatted.split('<br>').filter(line => line.trim());
                }
            }
            
            // Only show label for chorus/hui sections
            let verseLabel = '';
            if (verse.type && (verse.type === 'chorus' || verse.type === 'hui')) {
                verseLabel = 'Hui:';
            }
            
            console.log(`Verse ${index} - Hawaiian lines:`, hawaiianLines); // Debug log
            console.log(`Verse ${index} - English lines:`, englishLines); // Debug log
            
            if (isPrintVersion) {
                // Print version
                lyricsHTML += `<div class="verse-container">`;
                if (verseLabel) {
                    lyricsHTML += `<div class="verse-label">${verseLabel}</div>`;
                }
                
                if (isLyricsOnly) {
                    // Lyrics only - single column, large font
                    hawaiianLines.forEach(line => {
                        lyricsHTML += `<div class="hawaiian-only-line">${line}</div>`;
                    });
                } else {
                    // With translation - paired layout
                    const maxLines = Math.max(hawaiianLines.length, englishLines.length);
                    for (let i = 0; i < maxLines; i++) {
                        const hawaiianLine = hawaiianLines[i] || '';
                        const englishLine = englishLines[i] || '';
                        lyricsHTML += `
                            <div class="line-pair">
                                <div class="hawaiian-line">${hawaiianLine}</div>
                                <div class="english-line">${englishLine}</div>
                            </div>
                        `;
                    }
                }
                lyricsHTML += `</div>`;
            } else {
                // Regular version: original layout
                let hawaiianHTML = '';
                if (verseLabel) {
                    hawaiianHTML += `<div class="verse-label">${verseLabel}</div>`;
                }
                hawaiianLines.forEach(line => {
                    hawaiianHTML += `<div class="verse-line">${line}</div>`;
                });
                
                let englishHTML = '';
                if (verseLabel) {
                    englishHTML += `<div class="verse-label">${verseLabel}</div>`;
                }
                englishLines.forEach(line => {
                    englishHTML += `<div class="verse-line">${line}</div>`;
                });
                
                lyricsHTML += `
                    <div class="verse-container">
                        <div class="verse-column hawaiian-verse">
                            ${hawaiianHTML}
                        </div>
                        <div class="verse-column english-verse">
                            ${englishHTML}
                        </div>
                    </div>
                `;
            }
        });
        
        console.log('Generated lyrics HTML:', lyricsHTML); // Debug log
        lyricsContainer.innerHTML = lyricsHTML;
    }
    
    formatField(value) {
        return value && value.trim() !== '' ? value : 'Not specified';
    }
    
    reconstructHawaiianLines(text) {
        // More conservative approach - only break at clear verse boundaries
        let formatted = text
            // Break before common verse/line starters (not names)
            .replace(/([ai])\s+(ʻE\s)/g, '$1<br>$2')  // "aku ai ʻE"
            .replace(/([ai])\s+(Pane\s)/g, '$1<br>$2')  // "waiwai Pane"
            .replace(/([ai])\s+(I\s[klhmp])/g, '$1<br>$2')  // "ai I loaʻa" but not "ai I Haku"
            .replace(/([ai])\s+(Me\s[k])/g, '$1<br>$2')  // "ai Me ke" but not "Me Haku"
            // Break after question marks (end of questions)
            .replace(/(\?)\s+([A-ZĀĒĪŌŪ])/g, '$1<br>$2')
            // Very specific patterns only
            .replace(/(waiwai)\s+(Pane)/g, '$1<br>$2')
            .replace(/(mau)\s+(Minamina)/g, '$1<br>$2')
            .replace(/(hune)\s+(Huli)/g, '$1<br>$2')
            .replace(/(ʻōpio)\s+(ʻAʻole)/g, '$1<br>$2');
        
        return formatted;
    }
    
    reconstructEnglishLines(text) {
        // Based on English translation patterns
        let formatted = text
            // Break before capital letters that start new sentences/lines
            .replace(/([a-z])\s+([A-Z][a-z])/g, '$1<br>$2')
            // Break before quotes (common in songs) - using single quotes to avoid regex issues
            .replace(/([a-z])\s+(['"])/g, '$1<br>$2')
            // Break before "To" at start of lines
            .replace(/([a-z])\s+(To\s)/g, '$1<br>$2');
        
        return formatted;
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

// Modal functionality for song pages
class SongModalManager {
    constructor() {
        this.setupModalListeners();
    }
    
    setupModalListeners() {
        const modal = document.getElementById('songModal');
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
        
        // Page info icon functionality
        const pageInfoIcon = document.getElementById('pageInfoIcon');
        if (pageInfoIcon) {
            pageInfoIcon.addEventListener('click', () => {
                this.showSongModal();
            });
        }
        
        // Print icon functionality
        const printIcon = document.getElementById('printIcon');
        if (printIcon) {
            printIcon.addEventListener('click', () => {
                this.openPrintVersion();
            });
        }
        
        // Print dialog functionality
        this.setupPrintDialogListeners();
    }
    
    switchTab(tabName) {
        // Remove active class from all tabs and contents
        document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        // Add active class to selected tab and content
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(`${tabName}Tab`).classList.add('active');
    }
    
    showSongModal() {
        if (!songPage.song) {
            alert('Song data not yet loaded. Please wait for the song to finish loading.');
            return;
        }
        
        const modal = document.getElementById('songModal');
        const modalTitle = document.getElementById('modalSongTitle');
        const metadataTab = document.getElementById('metadataTab');
        const composerTab = document.getElementById('composerTab');
        
        // Set modal title
        modalTitle.textContent = songPage.song.canonical_title_hawaiian || songPage.song.canonical_title_english || 'Song Details';
        
        // Show modal and reset to first tab
        modal.style.display = 'block';
        this.switchTab('metadata');
        
        // Render song metadata
        this.renderSongMetadata(songPage.song, metadataTab);
        
        // Try to load composer info if available
        if (songPage.song.primary_composer) {
            this.loadComposerInfo(songPage.song.primary_composer, composerTab);
        } else {
            composerTab.innerHTML = '<div class="modal-loading">No composer information available.</div>';
        }
    }
    
    renderSongMetadata(song, container) {
        const formatField = (value) => {
            return value && value.trim() !== '' ? value : 'Not specified';
        };
        
        container.innerHTML = `
            <div class="metadata-section">
                <h3>Song Information</h3>
                <div class="metadata-field">
                    <span class="metadata-label">Hawaiian Title:</span>
                    <span class="metadata-value">${formatField(song.canonical_title_hawaiian)}</span>
                </div>
                <div class="metadata-field">
                    <span class="metadata-label">English Title:</span>
                    <span class="metadata-value">${formatField(song.canonical_title_english)}</span>
                </div>
                <div class="metadata-field">
                    <span class="metadata-label">Composer:</span>
                    <span class="metadata-value">${formatField(song.primary_composer)}</span>
                </div>
                <div class="metadata-field">
                    <span class="metadata-label">Lyricist:</span>
                    <span class="metadata-value">${formatField(song.primary_lyricist)}</span>
                </div>
                <div class="metadata-field">
                    <span class="metadata-label">Translator:</span>
                    <span class="metadata-value">${formatField(song.translator)}</span>
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
                    <span class="metadata-label">Song Type:</span>
                    <span class="metadata-value">${formatField(song.song_type)}</span>
                </div>
                <div class="metadata-field">
                    <span class="metadata-label">Structure:</span>
                    <span class="metadata-value">${formatField(song.structure_type)}</span>
                </div>
                ${song.cultural_significance_notes ? `
                    <div class="metadata-field">
                        <span class="metadata-label">Cultural Notes:</span>
                        <div class="metadata-value" style="margin-top: 4px; line-height: 1.4;">${song.cultural_significance_notes}</div>
                    </div>
                ` : ''}
            </div>
            
            <div class="metadata-section">
                <h3>Source Information</h3>
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
            </div>
        `;
    }
    
    async loadComposerInfo(composerName, container) {
        container.innerHTML = '<div class="modal-loading">Loading composer details...</div>';
        
        try {
            // For now, show a simple message since we don't have API access in static mode
            container.innerHTML = `
                <div class="metadata-field">
                    <span class="metadata-label">Composer:</span>
                    <span class="metadata-value">${composerName}</span>
                </div>
                <div class="metadata-field">
                    <span class="metadata-label">Note:</span>
                    <span class="metadata-value">Detailed biographical information would be available when connected to the full database.</span>
                </div>
            `;
        } catch (error) {
            container.innerHTML = '<div class="modal-error">Unable to load composer details.</div>';
        }
    }
    
    openPrintVersion() {
        // Show print options dialog
        const printModal = document.getElementById('printModal');
        if (printModal) {
            printModal.style.display = 'block';
        }
    }
    
    setupPrintDialogListeners() {
        const printModal = document.getElementById('printModal');
        const closePrintModal = document.getElementById('closePrintModal');
        const cancelPrint = document.getElementById('cancelPrint');
        const printLyricsOnly = document.getElementById('printLyricsOnly');
        const printWithTranslation = document.getElementById('printWithTranslation');
        
        // Close modal handlers
        [closePrintModal, cancelPrint].forEach(btn => {
            if (btn) {
                btn.addEventListener('click', () => {
                    printModal.style.display = 'none';
                });
            }
        });
        
        // Click outside modal to close
        if (printModal) {
            printModal.addEventListener('click', (e) => {
                if (e.target === printModal) {
                    printModal.style.display = 'none';
                }
            });
        }
        
        // Print button handlers
        if (printLyricsOnly) {
            printLyricsOnly.addEventListener('click', () => {
                this.handlePrintChoice('lyrics-only');
            });
        }
        
        if (printWithTranslation) {
            printWithTranslation.addEventListener('click', () => {
                this.handlePrintChoice('with-translation');
            });
        }
    }
    
    handlePrintChoice(format) {
        // Get current song ID from URL
        const urlParams = new URLSearchParams(window.location.search);
        const songId = urlParams.get('id');
        
        if (songId) {
            // Close the dialog
            const printModal = document.getElementById('printModal');
            if (printModal) {
                printModal.style.display = 'none';
            }
            
            // Open print version with format parameter
            const printUrl = `song-print.html?id=${songId}&format=${format}`;
            window.open(printUrl, '_blank');
        } else {
            alert('Unable to open print version - no song ID found.');
        }
    }
}

// Initialize modal manager
const modalManager = new SongModalManager();