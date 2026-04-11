import axios from '../utils/axios';

const userApi = {
  getProfile: () => axios.get('/user/profile'),
  updateProfile: (profile) => axios.put('/user/profile', profile),
  getDietPreference: () => axios.get('/user/diet-preference'),
  updateDietPreference: (preference) => axios.put('/user/diet-preference', preference),
  getAdminUsers: () => axios.get('/user/admin/list'),
  updateUserStatus: (userId, status) =>
    axios.put(`/user/admin/${userId}/status`, null, {
      params: { status }
    })
};

export default userApi;
