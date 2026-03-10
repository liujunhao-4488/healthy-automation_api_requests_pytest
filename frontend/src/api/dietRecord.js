import axios from '../utils/axios';

const dietRecordApi = {
  submitRecord: (record) => {
    return axios.post('/api/record/submit', record);
  },
  getDietRecords: (startDate, endDate, page, pageSize) => {
    return axios.get('/api/record/list', {
      params: { startDate, endDate, page, pageSize }
    });
  },
  getDietAnalysis: (startDate, endDate) => {
    return axios.get('/api/record/analysis/trend', {
      params: { startDate, endDate }
    });
  },
  getDietSuggestions: () => {
    return axios.get('/api/record/suggestions');
  },
  deleteRecord: (recordId) => {
    return axios.delete(`/api/record/${recordId}`);
  }
};

export default dietRecordApi;