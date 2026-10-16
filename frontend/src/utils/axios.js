import axios from 'axios';
import { clearPersistedAuth, isTokenExpired } from '../stores/user';

// 导出出来是为了让 api 层里那条"不走 axios"的 SSE 请求也能用同一个 baseURL ——
// 否则它得自己再抄一份 import.meta.env，两边一旦不一致就会变成很难查的怪问题。
export const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api';

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
