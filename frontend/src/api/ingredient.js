import axios from '../utils/axios';

const ingredientApi = {
  getAllIngredients: () => axios.get('/ingredient/list'),
  getIngredientDetail: (id) => axios.get(`/ingredient/detail/${id}`),
  getIngredientsByCategory: (category) => axios.get(`/ingredient/category/${category}`),
  searchIngredients: (keyword) => axios.get('/ingredient/search', { params: { keyword } }),
  saveIngredient: (ingredient) => axios.post('/ingredient/save', ingredient),
  updateIngredient: (ingredient) => axios.put('/ingredient/update', ingredient),
  deleteIngredient: (id) => axios.delete(`/ingredient/delete/${id}`),
  calculateNutrition: (payload) => axios.post('/ingredient/nutrition', payload)
};

export default ingredientApi;
