import axios from '../utils/axios';

const recipeApi = {
  getRecommendations: (userId) => {
    return axios.get(`/api/recommend/recipes`, { params: { userId } });
  },
  getSubstitutes: (ingredient) => {
    return axios.post('/api/recommend/ingredient/substitute', { ingredientName: ingredient });
  },
  getRecipesByGoal: (goalData) => {
    return axios.post('/api/recommend/recipes/by-goal', goalData);
  },
  getTodayRecipes: () => {
    return axios.get('/api/recommend/recipes/today');
  },
  getAllRecipes: () => {
    return axios.get('/api/recipe/list');
  },
  getRecipeDetail: (id) => {
    return axios.get(`/api/recipe/detail/${id}`);
  },
  getCustomRecipes: () => {
    return axios.get('/api/recipe/custom');
  },
  searchRecipes: (keyword) => {
    return axios.get('/api/recipe/search', { params: { keyword } });
  },
  saveRecipe: (recipe) => {
    return axios.post('/api/recipe/save', recipe);
  },
  updateRecipe: (recipe) => {
    return axios.put('/api/recipe/update', recipe);
  },
  deleteRecipe: (id) => {
    return axios.delete(`/api/recipe/delete/${id}`);
  },
  analyzeNutrition: (id) => {
    return axios.get(`/api/recipe/nutrition/${id}`);
  }
};

export default recipeApi;