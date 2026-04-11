import axios from '../utils/axios';

const recipeApi = {
  getRecommendations: (params = {}) => {
    return axios.get('/recommend/recipes', { params });
  },
  getSubstitutes: (payload) => {
    const prompt = typeof payload === 'string' ? payload : payload?.prompt;
    const rawPrompt = typeof payload === 'object' && payload ? (payload.rawPrompt || payload.prompt) : prompt;
    return axios.post('/recommend/ingredient/substitute', {
      ...(typeof payload === 'object' && payload ? payload : {}),
      ingredientName: rawPrompt,
      prompt
    }, {
      timeout: 60000
    });
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
  collectRecipe: (id) => {
    return axios.post(`/recipe/collect/${id}`);
  },
  cancelCollectRecipe: (id) => {
    return axios.delete(`/recipe/collect/${id}`);
  },
  getRecipeCollectStatus: (id) => {
    return axios.get(`/recipe/collect/status/${id}`);
  },
  getCollectedRecipes: () => {
    return axios.get('/recipe/collect/list');
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
