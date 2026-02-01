import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://smartfin-8hyb.onrender.com';
const AUTH_BASE_URL = import.meta.env.VITE_AUTH_BASE_URL || 'https://smartfin-8hyb.onrender.com';

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
  ,
  // Auth methods
  async register(email, password) {
    try {
      const response = await axios.post(`${AUTH_BASE_URL}/register`, { email, password });
      return response.data;
    } catch (error) {
      console.error('Auth register error:', error);
      throw new Error(error?.response?.data?.message || 'Registration failed');
    }
  },

  async login(email, password) {
    try {
      const response = await axios.post(`${AUTH_BASE_URL}/login`, { email, password });
      const token = response.data?.token;
      if (token) {
        this.setAuthToken(token);
      }
      return response.data;
    } catch (error) {
      console.error('Auth login error:', error);
      throw new Error(error?.response?.data?.message || 'Login failed');
    }
  },

  setAuthToken(token) {
    if (token) {
      localStorage.setItem('sf_token', token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      localStorage.removeItem('sf_token');
      delete axios.defaults.headers.common['Authorization'];
    }
  },

  getStoredToken() {
    return localStorage.getItem('sf_token');
  },
};

export default api;
