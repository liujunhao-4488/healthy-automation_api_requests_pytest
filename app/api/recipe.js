import request from '@/utils/request'

export default {
  getRecommendations(params = {}) {
    return request.get('/recommend/recipes', params)
  },
  getRecipesByGoal(data) {
    return request.post('/recommend/recipes/by-goal', data)
  },
  getTodayRecipes() {
    return request.get('/recommend/recipes/today')
  },
  getAllRecipes() {
    return request.get('/recipe/list')
  },
  getRecipeDetail(id) {
    return request.get(`/recipe/detail/${id}`)
  },
  collectRecipe(id) {
    return request.post(`/recipe/collect/${id}`)
  },
  cancelCollectRecipe(id) {
    return request.delete(`/recipe/collect/${id}`)
  },
  getRecipeCollectStatus(id) {
    return request.get(`/recipe/collect/status/${id}`)
  },
  getCollectedRecipes() {
    return request.get('/recipe/collect/list')
  },
  getCustomRecipes() {
    return request.get('/recipe/custom')
  },
  searchRecipes(keyword) {
    return request.get('/recipe/search', { keyword })
  },
  saveRecipe(data) {
    return request.post('/recipe/save', data)
  },
  updateRecipe(data) {
    return request.put('/recipe/update', data)
  },
  deleteRecipe(id) {
    return request.delete(`/recipe/delete/${id}`)
  },
  analyzeNutrition(id) {
    return request.get(`/recipe/nutrition/${id}`)
  }
}
