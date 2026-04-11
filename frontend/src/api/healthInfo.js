import axios from '../utils/axios';

const healthInfoApi = {
  getHealthInfo: () => axios.get('/health/info'),
  getHealthHistory: () => axios.get('/health/history'),
  saveHealthInfo: (healthInfo) => axios.post('/health/info', healthInfo),
  updateHealthInfo: (healthInfo) => axios.post('/health/info', healthInfo)
};

export default healthInfoApi;
