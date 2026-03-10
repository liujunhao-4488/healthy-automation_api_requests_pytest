import axios from 'axios';

// 创建axios实例
const service = axios.create({
  baseURL: '',
  timeout: 10000
});

// 请求拦截器
service.interceptors.request.use(
  config => {
    // 从localStorage获取token
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    console.error('请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
service.interceptors.response.use(
  response => {
    return response.data;
  },
  error => {
    console.error('响应错误:', error);
    // 处理401未授权错误
    if (error.response) {
      if (error.response.status === 401) {
        window.location.href = '/login';
      }
      // 返回后端错误信息
      const backendError = error.response.data;
      if (backendError && backendError.message) {
        return Promise.reject(new Error(backendError.message));
      }
    }
    return Promise.reject(error);
  }
);

export default service;