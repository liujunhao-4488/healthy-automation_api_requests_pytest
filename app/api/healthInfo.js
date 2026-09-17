import request from '@/utils/request'

export default {
  getHealthInfo() {
    return request.get('/health/info')
  },
  getHealthHistory() {
    return request.get('/health/history')
  },
  saveHealthInfo(data) {
    return request.post('/health/info', data)
  },
  updateHealthInfo(data) {
    return request.post('/health/info', data)
  }
}
