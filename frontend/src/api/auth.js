import axios from '../utils/axios';

const authApi = {
  register: (userData) => {
    return axios.post('/api/auth/register', userData);
  },
  login: (userData) => {
    return axios.post('/api/auth/login', userData);
  }
};

export default authApi;