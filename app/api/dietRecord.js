import request from '@/utils/request'

export default {
  submitRecord(data) {
    return request.post('/record/submit', data)
  },
  getDietRecords(startDate, endDate, page, pageSize) {
    return request.get('/record/list', { startDate, endDate, page, pageSize })
  },
  getDietAnalysis(startDate, endDate) {
    return request.get('/record/analysis/trend', { startDate, endDate })
  },
  getDietSuggestions() {
    return request.get('/record/suggestions')
  },
  deleteRecord(id) {
    return request.delete(`/record/${id}`)
  }
}
