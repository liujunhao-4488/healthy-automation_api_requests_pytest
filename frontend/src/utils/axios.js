import axios from 'axios';
import { clearPersistedAuth, isTokenExpired } from '../stores/user';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api';

const service = axios.create({
  baseURL: apiBaseUrl,
  timeout: 10000
});

service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');

    if (token) {
      if (isTokenExpired(token)) {
        clearPersistedAuth();
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
        return Promise.reject(new Error('Login expired, please sign in again.'));
      }

      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

service.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      clearPersistedAuth();
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }

    const backendError = error.response?.data;
    if (backendError?.message) {
      return Promise.reject(new Error(backendError.message));
    }

    return Promise.reject(error);
  }
);

export default service;
