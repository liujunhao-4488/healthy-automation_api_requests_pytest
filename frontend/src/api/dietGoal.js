import axios from '../utils/axios';

const dietGoalApi = {
  getDietGoal: (userId) => {
    return axios.get(`/health/goal`);
  },
  saveDietGoal: (dietGoal) => {
    return axios.post('/health/goal', dietGoal);
  },
  updateDietGoal: (dietGoal) => {
    return axios.put('/health/goal', dietGoal);
  }
};

export default dietGoalApi;