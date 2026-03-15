import axios from '../utils/axios';

const healthKnowledgeApi = {
  getKnowledgeList: (page, size) => {
    return axios.get('/article/list', { params: { page, size } });
  },
  getRecommendedArticles: (articleCount) => {
    return axios.post('/article/recommend', { articleCount });
  },
  getArticleDetail: (articleId) => {
    return axios.get(`/article/detail/${articleId}`);
  },
  searchArticles: (keyword) => {
    return axios.get('/article/search', { params: { keyword } });
  }
};

export default healthKnowledgeApi;