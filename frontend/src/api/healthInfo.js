import axios from '../utils/axios';

const healthInfoApi = {
  getHealthInfo: () => {
    return axios.get('/api/health/info');
  },
  saveHealthInfo: (healthInfo) => {
    return axios.post('/api/health/info', healthInfo);
  },
  updateHealthInfo: (healthInfo) => {
    return axios.put('/api/health/info', healthInfo);
  }
};

export default healthInfoApi;