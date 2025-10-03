// Settings Module - Reusable settings functionality
class HuapalaSettings {
    constructor() {
        this.defaultFontSize = 14;
        this.init();
    }

    init() {
        // Load saved settings from localStorage
        this.loadSettings();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Apply current settings
        this.applySettings();
    }

    setupEventListeners() {
        // Settings icon click
        const settingsIcon = document.getElementById('settingsIcon');
        console.log('Settings icon found:', settingsIcon);
        if (settingsIcon) {
            settingsIcon.addEventListener('click', () => {
                console.log('Settings icon clicked!');
                this.openSettingsModal();
            });
        }

        // Settings modal close
        const closeSettingsModal = document.getElementById('closeSettingsModal');
        if (closeSettingsModal) {
            closeSettingsModal.addEventListener('click', () => this.closeSettingsModal());
        }

        // Click outside modal to close
        const settingsModal = document.getElementById('settingsModal');
        if (settingsModal) {
            settingsModal.addEventListener('click', (e) => {
                if (e.target === settingsModal) {
                    this.closeSettingsModal();
                }
            });
        }

        // Font size visual selector changes
        const fontSizeOptions = document.querySelectorAll('.font-size-option-visual');
        fontSizeOptions.forEach(option => {
            option.addEventListener('click', (e) => {
                const size = parseInt(e.currentTarget.getAttribute('data-size'));
                this.setFontSize(size);
            });
        });
    }

    openSettingsModal() {
        console.log('Opening settings modal...');
        const modal = document.getElementById('settingsModal');
        console.log('Settings modal found:', modal);
        if (modal) {
            modal.style.display = 'block';
            console.log('Modal display set to block');
        }
    }

    closeSettingsModal() {
        const modal = document.getElementById('settingsModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    loadSettings() {
        // Load font size from localStorage
        const savedFontSize = localStorage.getItem('huapala-font-size');
        this.fontSize = savedFontSize ? parseInt(savedFontSize) : this.defaultFontSize;
        
        // Update visual selector
        this.updateVisualSelector();
    }

    setFontSize(size) {
        this.fontSize = size;
        localStorage.setItem('huapala-font-size', size.toString());
        this.updateVisualSelector();
        this.applyFontSize();
    }

    updateVisualSelector() {
        // Remove active class from all options
        const allOptions = document.querySelectorAll('.font-size-option-visual');
        allOptions.forEach(option => option.classList.remove('active'));
        
        // Add active class to selected option
        const selectedOption = document.querySelector(`[data-size="${this.fontSize}"]`);
        if (selectedOption) {
            selectedOption.classList.add('active');
        }
    }

    applyFontSize() {
        // Apply font size to main content areas
        const elementsToUpdate = [
            '.song-entry',
            '.song-link',
            '.composer-info',
            '.loading',
            '.error',
            '#searchInput',
            '.verse-column',  // Add verse content
            '.hawaiian-verse',
            '.english-verse'
        ];

        elementsToUpdate.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                element.style.fontSize = `${this.fontSize}px`;
            });
        });

        // Also update any dynamically loaded content
        document.documentElement.style.setProperty('--base-font-size', `${this.fontSize}px`);
    }

    applySettings() {
        this.applyFontSize();
    }
}

// Initialize settings when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.huapalaSettings = new HuapalaSettings();
});