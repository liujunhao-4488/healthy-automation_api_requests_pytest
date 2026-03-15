import axios from '../utils/axios';

const authApi = {
  register: (userData) => {
    return axios.post('/auth/register', userData);
  },
  login: (userData) => {
    return axios.post('/auth/login', userData);
  }
};

export default authApi;