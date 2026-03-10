import axios from '../utils/axios';

const dietGoalApi = {
  getDietGoal: (userId) => {
    return axios.get(`/api/health/goal`);
  },
  saveDietGoal: (dietGoal) => {
    return axios.post('/api/health/goal', dietGoal);
  },
  updateDietGoal: (dietGoal) => {
    return axios.put('/api/health/goal', dietGoal);
  }
};

export default dietGoalApi;