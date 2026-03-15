import axios from '../utils/axios';

const dietRecordApi = {
  submitRecord: (record) => {
    return axios.post('/record/submit', record);
  },
  getDietRecords: (startDate, endDate, page, pageSize) => {
    return axios.get('/record/list', {
      params: { startDate, endDate, page, pageSize }
    });
  },
  getDietAnalysis: (startDate, endDate) => {
    return axios.get('/record/analysis/trend', {
      params: { startDate, endDate }
    });
  },
  getDietSuggestions: () => {
    return axios.get('/record/suggestions');
  },
  deleteRecord: (recordId) => {
    return axios.delete(`/record/${recordId}`);
  }
};

export default dietRecordApi;