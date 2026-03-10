import axios from '../utils/axios';

const healthKnowledgeApi = {
  getKnowledgeList: (page, size) => {
    return axios.get('/api/article/list', { params: { page, size } });
  },
  getRecommendedArticles: (articleCount) => {
    return axios.post('/api/article/recommend', { articleCount });
  },
  getArticleDetail: (articleId) => {
    return axios.get(`/api/article/detail/${articleId}`);
  },
  searchArticles: (keyword) => {
    return axios.get('/api/article/search', { params: { keyword } });
  }
};

export default healthKnowledgeApi;