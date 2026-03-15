import axios from '../utils/axios';

const recipeApi = {
  getRecommendations: (userId) => {
    return axios.get(`/recommend/recipes`, { params: { userId } });
  },
  getSubstitutes: (ingredient) => {
    return axios.post('/recommend/ingredient/substitute', { ingredientName: ingredient });
  },
  getRecipesByGoal: (goalData) => {
    return axios.post('/recommend/recipes/by-goal', goalData);
  },
  getTodayRecipes: () => {
    return axios.get('/recommend/recipes/today');
  },
  getAllRecipes: () => {
    return axios.get('/recipe/list');
  },
  getRecipeDetail: (id) => {
    return axios.get(`/recipe/detail/${id}`);
  },
  getCustomRecipes: () => {
    return axios.get('/recipe/custom');
  },
  searchRecipes: (keyword) => {
    return axios.get('/recipe/search', { params: { keyword } });
  },
  saveRecipe: (recipe) => {
    return axios.post('/recipe/save', recipe);
  },
  updateRecipe: (recipe) => {
    return axios.put('/recipe/update', recipe);
  },
  deleteRecipe: (id) => {
    return axios.delete(`/recipe/delete/${id}`);
  },
  analyzeNutrition: (id) => {
    return axios.get(`/recipe/nutrition/${id}`);
  }
};

export default recipeApi;