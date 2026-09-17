import request from '@/utils/request'

export default {
  getDietGoal() {
    return request.get('/health/goal')
  },
  saveDietGoal(data) {
    return request.post('/health/goal', data)
  },
  updateDietGoal(data) {
    return request.post('/health/goal', data)
  }
}
