// Configuration for frontend
// Switch between local and deployed backend

const CONFIG = {
    // For local development
    LOCAL_BACKEND: 'http://localhost:5000',

    // For deployment - you'll need to deploy backend separately
    // Options: Railway, Render, PythonAnywhere, Heroku
    PRODUCTION_BACKEND: 'https://your-backend-url.com',

    // Auto-detect environment
    isLocal: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',

    // Get the correct backend URL
    getBackendUrl() {
        return this.isLocal ? this.LOCAL_BACKEND : this.PRODUCTION_BACKEND;
    }
};

// Export for use in other files
window.CONFIG = CONFIG;
