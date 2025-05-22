import axios from 'axios';

import { ROUTES } from '@/constants/routeConstants';
import authStore from '@/store/authStore';

const apiBaseUrl = '/api';

const API_TIMEOUT = import.meta.env.VITE_API_TIMEOUT_IN_SECONDS
  ? import.meta.env.VITE_API_TIMEOUT_IN_SECONDS * 1000
  : 10000;

// Create an instance of axios
const apiClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: API_TIMEOUT,
  headers: {
    Accept: 'application/json',
  },
});

// Helper to parse Zustand auth storage
const getAuthToken = () => {
  const authStorage = localStorage.getItem('auth-storage');
  if (authStorage) {
    try {
      const parsedStorage = JSON.parse(authStorage);
      return parsedStorage.state?.token || null;
    } catch (e) {
      console.error('Error parsing auth storage:', e);
      return null;
    }
  }
  return null;
};

// Request interceptor to add auth token to headers
apiClient.interceptors.request.use(
  (config) => {
    const token = getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors globally
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    console.error('API error:', error);
    // Network error handling
    if (!error.response) {
      return Promise.reject(new Error('Network error - please check your connection'));
    }

    const status = error.response?.status;

    // Handle unauthorized
    if (status === 401 && authStore.getState().is_token_active) {
      authStore.getState().logout();
      window.location.replace(ROUTES.AUTH.LOGIN);
      return Promise.reject(error);
    }

    // Set error message based on status
    error.message =
      error.response?.data?.detail || error.response?.data?.message || 'An error occurred';

    return Promise.reject(error);
  }
);

// API methods
const api = {
  get: (url, config = {}) => apiClient.get(url, config),
  post: (url, data, config = {}) => apiClient.post(url, data, config),
  put: (url, data, config = {}) => apiClient.put(url, data, config),
  delete: (url, config = {}) => apiClient.delete(url, config),
  patch: (url, data, config = {}) => apiClient.patch(url, data, config),
};

export default api;
