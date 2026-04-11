import axios from '../utils/axios';

const dietGoalApi = {
  getDietGoal: () => {
    return axios.get('/health/goal');
  },
  saveDietGoal: (dietGoal) => {
    return axios.post('/health/goal', dietGoal);
  },
  updateDietGoal: (dietGoal) => {
    return axios.post('/health/goal', dietGoal);
  }
};

export default dietGoalApi;
