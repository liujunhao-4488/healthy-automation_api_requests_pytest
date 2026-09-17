import request from '@/utils/request'

export default {
  getKnowledgeList(pageOrParams, size) {
    if (typeof pageOrParams === 'number') {
      return request.get('/article/list', { page: pageOrParams, pageSize: size })
    }
    return request.get('/article/list', pageOrParams || {})
  },
  getArticleTags() {
    return request.get('/article/tags')
  },
  getRecommendedArticles(params = {}) {
    return request.get('/article/recommend', params)
  },
  getArticleDetail(articleId) {
    return request.get(`/article/detail/${articleId}`)
  },
  likeArticle(articleId) {
    return request.post(`/article/like/${articleId}`)
  },
  cancelLikeArticle(articleId) {
    return request.delete(`/article/like/${articleId}`)
  },
  getArticleLikeStatus(articleId) {
    return request.get(`/article/like/status/${articleId}`)
  },
  collectArticle(articleId) {
    return request.post(`/article/collect/${articleId}`)
  },
  cancelCollectArticle(articleId) {
    return request.delete(`/article/collect/${articleId}`)
  },
  getArticleCollectStatus(articleId) {
    return request.get(`/article/collect/status/${articleId}`)
  },
  getCollectedArticles() {
    return request.get('/article/collect/list')
  },
  getArticleComments(articleId) {
    return request.get(`/article/comment/list/${articleId}`)
  },
  addArticleComment(articleId, payload) {
    return request.post(`/article/comment/${articleId}`, payload)
  },
  deleteArticleComment(commentId) {
    return request.delete(`/article/comment/${commentId}`)
  },
  searchArticles(keyword, page = 1, pageSize = 10) {
    return request.get('/article/search', { keyword, page, pageSize })
  }
}
