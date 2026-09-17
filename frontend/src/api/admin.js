import axios from '../utils/axios';

const adminApi = {
  getOverview: () => axios.get('/admin/overview')
};

export default adminApi;
