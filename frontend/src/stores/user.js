import { defineStore } from 'pinia';

export const useUserStore = defineStore('user', {
  state: () => ({
    userId: null,
    username: '',
    token: '',
    healthInfo: null,
    dietGoal: null
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    hasHealthInfo: (state) => !!state.healthInfo,
    hasDietGoal: (state) => !!state.dietGoal
  },
  actions: {
    setUser(user) {
      this.userId = user.userId;
      this.username = user.username;
      this.token = user.token;
      localStorage.setItem('token', user.token);
    },
    setHealthInfo(info) {
      this.healthInfo = info;
    },
    setDietGoal(goal) {
      this.dietGoal = goal;
    },
    logout() {
      this.userId = null;
      this.username = '';
      this.token = '';
      this.healthInfo = null;
      this.dietGoal = null;
      localStorage.removeItem('token');
    }
  }
});