import axios from '../utils/axios';

const healthKnowledgeApi = {
  getKnowledgeList: (pageOrParams, size) => {
    if (typeof pageOrParams === 'number') {
      return axios.get('/article/list', { params: { page: pageOrParams, pageSize: size } });
    }
    return axios.get('/article/list', { params: pageOrParams || {} });
  },
  getArticleTags: () => {
    return axios.get('/article/tags');
  },
  getRecommendedArticles: (limit) => {
    return axios.get('/article/recommend', { params: { limit } });
  },
  getArticleDetail: (articleId) => {
    return axios.get(`/article/detail/${articleId}`);
  },
  likeArticle: (articleId) => {
    return axios.post(`/article/like/${articleId}`);
  },
  cancelLikeArticle: (articleId) => {
    return axios.delete(`/article/like/${articleId}`);
  },
  getArticleLikeStatus: (articleId) => {
    return axios.get(`/article/like/status/${articleId}`);
  },
  collectArticle: (articleId) => {
    return axios.post(`/article/collect/${articleId}`);
  },
  cancelCollectArticle: (articleId) => {
    return axios.delete(`/article/collect/${articleId}`);
  },
  getArticleCollectStatus: (articleId) => {
    return axios.get(`/article/collect/status/${articleId}`);
  },
  getCollectedArticles: () => {
    return axios.get('/article/collect/list');
  },
  getArticleComments: (articleId) => {
    return axios.get(`/article/comment/list/${articleId}`);
  },
  addArticleComment: (articleId, payload) => {
    return axios.post(`/article/comment/${articleId}`, payload);
  },
  deleteArticleComment: (commentId) => {
    return axios.delete(`/article/comment/${commentId}`);
  },
  getArticleCollectStats: () => {
    return axios.get('/article/admin/collect-stats');
  },
  saveArticle: (article) => {
    return axios.post('/article/save', article);
  },
  publishArticle: (article) => {
    return axios.post('/article/publish', article);
  },
  updateArticle: (article) => {
    return axios.put('/article/update', article);
  },
  deleteArticle: (articleId) => {
    return axios.delete(`/article/delete/${articleId}`);
  },
  searchArticles: (keyword, page = 1, pageSize = 10) => {
    return axios.get('/article/search', { params: { keyword, page, pageSize } });
  }
};

export default healthKnowledgeApi;
