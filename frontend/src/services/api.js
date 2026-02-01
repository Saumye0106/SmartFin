import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000';

const api = {
  async predict(financialData) {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/predict`, financialData);
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw new Error('Failed to get prediction. Make sure the backend is running.');
    }
  },

  async whatIf(currentData, modifiedData) {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/whatif`, {
        current: currentData,
        modified: modifiedData
      });
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw new Error('Failed to run simulation.');
    }
  },

  async getModelInfo() {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/model-info`);
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw new Error('Failed to get model info.');
    }
  }
};

export default api;
