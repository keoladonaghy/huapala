// Configuration for different environments
const Config = {
    // Determine if we're in development or production
    isDevelopment: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',
    
    // API base URL configuration
    getApiBaseUrl() {
        if (this.isDevelopment) {
            // Development - use local server
            return '';
        } else {
            // Production - use static JSON files
            return '';
        }
    },
    
    // Data source configuration
    getDataSource() {
        if (this.isDevelopment) {
            // Development - use API endpoints
            return {
                songs: '/songs',
                songById: (id) => `/songs/${id}`,
                songbooks: (id) => `/songs/${id}/songbooks`
            };
        } else {
            // Production - use static JSON files
            return {
                songs: './data/songs-data.json',
                songById: (id) => `./data/songs-data.json`, // Will filter client-side
                songbooks: (id) => `./data/songbooks-data.json` // Will filter client-side
            };
        }
    }
};

// Export for use in other files
window.Config = Config;