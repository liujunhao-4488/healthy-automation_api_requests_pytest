import axios from '../utils/axios';

const healthInfoApi = {
  getHealthInfo: () => {
    return axios.get('/health/info');
  },
  saveHealthInfo: (healthInfo) => {
    return axios.post('/health/info', healthInfo);
  },
  updateHealthInfo: (healthInfo) => {
    return axios.put('/health/info', healthInfo);
  }
};

export default healthInfoApi;