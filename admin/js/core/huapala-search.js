/**
 * Huapala Search Utilities
 * Shared functions for Hawaiian text normalization and song searching
 */

/**
 * Normalize Hawaiian text for searching by removing diacritics and special characters
 * Handles multiple apostrophe variants that users might input
 * @param {string} text - The text to normalize
 * @returns {string} - Normalized text for searching (lowercase, no diacritics)
 */
function normalizeHawaiianText(text) {
    if (!text) return '';
    return text
        .toLowerCase()
        // Remove all variants of apostrophes/okina
        .replace(/[ʻ'''`]/g, '') // U+02BB, U+2018, U+2019, backtick
        // Normalize macron vowels to regular vowels
        .replace(/[āă]/g, 'a')
        .replace(/[ēĕ]/g, 'e') 
        .replace(/[īĭ]/g, 'i')
        .replace(/[ōŏ]/g, 'o')
        .replace(/[ūŭ]/g, 'u')
        // Keep only letters, numbers, and spaces
        .replace(/[^a-z0-9\s]/g, '')
        // Collapse multiple spaces
        .replace(/\s+/g, ' ')
        .trim();
}

/**
 * Create a reusable search interface component
 * @param {Object} config - Configuration object
 * @param {string} config.containerId - ID of container element
 * @param {string} config.placeholder - Placeholder text for search input
 * @param {Array} config.songs - Array of song objects to search
 * @param {Function} config.onSongClick - Callback when song is clicked
 * @param {Array} config.searchFields - Fields to search in each song object
 * @returns {Object} - Search interface object with methods
 */
function createHuapalaSearch(config) {
    const {
        containerId,
        placeholder = 'Search songs by title or composer...',
        songs = [],
        onSongClick = () => {},
        searchFields = ['canonical_title_hawaiian', 'canonical_title_english', 'primary_composer']
    } = config;

    const container = document.getElementById(containerId);
    if (!container) {
        throw new Error(`Container with ID "${containerId}" not found`);
    }

    let allSongs = [...songs];
    let filteredSongs = [...songs];
    let searchInput;
    let resultsContainer;

    // Create the search interface HTML - matches home page exactly
    function createInterface() {
        container.innerHTML = `
            <div class="huapala-search">
                <div class="search-box">
                    <input type="text" id="searchInput" class="search-input" placeholder="${placeholder}">
                </div>
                <div class="songs-list"></div>
            </div>
        `;

        searchInput = container.querySelector('#searchInput');
        resultsContainer = container.querySelector('.songs-list');

        // Add event listeners
        searchInput.addEventListener('input', (e) => {
            filterSongs(e.target.value);
        });
    }

    // Filter songs based on search term
    function filterSongs(searchTerm) {
        const normalizedTerm = normalizeHawaiianText(searchTerm);
        
        if (!normalizedTerm.trim()) {
            filteredSongs = [...allSongs];
        } else {
            filteredSongs = allSongs.filter(song => {
                return searchFields.some(field => {
                    const fieldValue = song[field];
                    if (!fieldValue) return false;
                    const normalizedValue = normalizeHawaiianText(fieldValue);
                    return normalizedValue.includes(normalizedTerm);
                });
            });
        }
        
        renderResults();
    }

    // Distribute songs across two columns dynamically
    function distributeIntoColumns(songs) {
        const totalSongs = songs.length;
        const col1 = [];
        const col2 = [];
        
        // Distribute songs round-robin style: 1st -> col1, 2nd -> col2, 3rd -> col1, 4th -> col2, etc.
        songs.forEach((song, index) => {
            const columnIndex = index % 2;
            if (columnIndex === 0) {
                col1.push(song);
            } else {
                col2.push(song);
            }
        });
        
        return [col1, col2];
    }

    // Render search results exactly like home page
    function renderResults() {
        if (filteredSongs.length === 0) {
            resultsContainer.innerHTML = '<div class="no-results">No songs found matching your search.</div>';
            return;
        }

        const [col1, col2] = distributeIntoColumns(filteredSongs);
        
        resultsContainer.innerHTML = `
            <div class="search-columns">
                <div class="search-column">
                    ${col1.map(song => `
                        <div class="song-entry">
                            <span class="song-link" data-song-id="${song.canonical_mele_id}">${formatField(song.canonical_title_hawaiian)}</span>
                            <span class="composer-info"> - ${formatField(song.primary_composer)}</span>
                        </div>
                    `).join('')}
                </div>
                <div class="search-column">
                    ${col2.map(song => `
                        <div class="song-entry">
                            <span class="song-link" data-song-id="${song.canonical_mele_id}">${formatField(song.canonical_title_hawaiian)}</span>
                            <span class="composer-info"> - ${formatField(song.primary_composer)}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        // Add click handlers for song links
        resultsContainer.querySelectorAll('.song-link').forEach(element => {
            element.addEventListener('click', (e) => {
                const songId = e.currentTarget.dataset.songId;
                const song = allSongs.find(s => s.canonical_mele_id === songId);
                if (song) {
                    onSongClick(song);
                }
            });
        });
    }

    // Format field for display
    function formatField(value) {
        return value && value.trim() !== '' ? value : 'Not specified';
    }

    // Public API
    const searchInterface = {
        // Initialize the interface
        init() {
            createInterface();
            renderResults();
            return this;
        },

        // Update the songs list
        setSongs(newSongs) {
            allSongs = [...newSongs];
            filteredSongs = [...newSongs];
            if (resultsContainer) {
                renderResults();
            }
            return this;
        },

        // Get current search term
        getSearchTerm() {
            return searchInput ? searchInput.value : '';
        },

        // Set search term programmatically
        setSearchTerm(term) {
            if (searchInput) {
                searchInput.value = term;
                filterSongs(term);
            }
            return this;
        },

        // Get filtered results
        getResults() {
            return [...filteredSongs];
        },

        // Clear search
        clear() {
            if (searchInput) {
                searchInput.value = '';
                filterSongs('');
            }
            return this;
        },

        // Focus search input
        focus() {
            if (searchInput) {
                searchInput.focus();
            }
            return this;
        }
    };

    return searchInterface;
}

// Export for use in other scripts
if (typeof window !== 'undefined') {
    window.normalizeHawaiianText = normalizeHawaiianText;
    window.createHuapalaSearch = createHuapalaSearch;
}