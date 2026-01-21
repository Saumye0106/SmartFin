// API Service Module
// Get backend URL from config (supports local and deployed)
const API_BASE_URL = window.CONFIG ? window.CONFIG.getBackendUrl() : 'http://localhost:5000';

const API = {
    // Predict financial health score
    async predict(financialData) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/predict`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(financialData)
            });

            if (!response.ok) {
                throw new Error('Prediction request failed');
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    // What-if simulation
    async whatIf(currentData, modifiedData) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/whatif`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    current: currentData,
                    modified: modifiedData
                })
            });

            if (!response.ok) {
                throw new Error('What-if request failed');
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    // Get model info
    async getModelInfo() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/model-info`);

            if (!response.ok) {
                throw new Error('Model info request failed');
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }
};
