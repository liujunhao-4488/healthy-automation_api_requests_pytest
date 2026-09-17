import { createRouter, createWebHistory } from 'vue-router';
import { clearPersistedAuth, isHealthProfileComplete, isTokenExpired } from '../stores/user';

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue')
  },
  {
    path: '/health-info-basic',
    name: 'HealthInfoBasic',
    component: () => import('../views/HealthInfoBasic.vue')
  },
  {
    path: '/health-info-detail',
    name: 'HealthInfoDetail',
    component: () => import('../views/HealthInfoDetail.vue')
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    children: [
      { path: '', redirect: 'health-info' },
      { path: 'health-info', name: 'HealthInfo', component: () => import('../views/HealthInfo.vue') },
      { path: 'health-info/edit', name: 'HealthInfoEdit', component: () => import('../views/HealthInfoEdit.vue') },
      { path: 'profile', name: 'ProfileCenter', component: () => import('../views/ProfileCenter.vue') },
      { path: 'collected-articles', name: 'CollectedArticles', component: () => import('../views/CollectedArticles.vue') },
      { path: 'collected-recipes', name: 'CollectedRecipes', component: () => import('../views/CollectedRecipes.vue') },
      { path: 'diet-goal', name: 'DietGoal', component: () => import('../views/DietGoal.vue') },
      { path: 'diet-goal/edit', name: 'DietGoalEdit', component: () => import('../views/DietGoalEdit.vue') },
      { path: 'recipe-recommend', name: 'RecipeRecommend', component: () => import('../views/RecipeRecommend.vue') },
      { path: 'ingredient-substitute', name: 'IngredientSubstitute', component: () => import('../views/IngredientSubstitute.vue') },
      { path: 'diet-record', name: 'DietRecord', component: () => import('../views/DietRecord.vue') },
      { path: 'notifications', name: 'NotificationCenter', component: () => import('../views/NotificationCenter.vue') },
      { path: 'health-knowledge', name: 'HealthKnowledge', component: () => import('../views/HealthKnowledge.vue') },
      { path: 'health-knowledge/:id', name: 'ArticleDetail', component: () => import('../views/ArticleDetail.vue') },
      { path: 'custom-recipe', name: 'CustomRecipe', component: () => import('../views/CustomRecipe.vue') }
    ]
  },
  {
    path: '/admin',
    name: 'AdminLayout',
    component: () => import('../views/AdminLayout.vue'),
    children: [
      { path: '', redirect: 'overview' },
      { path: 'overview', name: 'AdminOverview', component: () => import('../views/AdminOverview.vue') },
      { path: 'users', name: 'AdminUsers', component: () => import('../views/AdminUserManagement.vue') },
      { path: 'ingredients', name: 'AdminIngredients', component: () => import('../views/IngredientLibrary.vue') },
      { path: 'recipes', name: 'AdminRecipes', component: () => import('../views/AdminRecipeLibrary.vue') },
      { path: 'articles', name: 'AdminArticles', component: () => import('../views/AdminArticleLibrary.vue') },
      { path: 'notifications', name: 'AdminNotifications', component: () => import('../views/AdminNotificationCenter.vue') }
    ]
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, from, next) => {
  const raw = localStorage.getItem('health-user');
  const rawToken = localStorage.getItem('token');
  const token = isTokenExpired(rawToken) ? '' : rawToken;
  let persisted = null;

  if (rawToken && !token) {
    clearPersistedAuth();
  }

  try {
    persisted = raw ? JSON.parse(raw) : null;
  } catch (error) {
    persisted = null;
  }

  const role = persisted?.role || 'user';
  const hasCompletedProfile = isHealthProfileComplete(persisted?.healthInfo);

  if ((to.path.startsWith('/dashboard') || to.path.startsWith('/admin')) && !token) {
    next('/login');
    return;
  }

  if (to.path.startsWith('/admin') && role !== 'admin') {
    next('/dashboard/health-info');
    return;
  }

  if (role === 'admin' && (to.path === '/health-info-basic' || to.path === '/health-info-detail')) {
    next('/admin/overview');
    return;
  }

  if ((to.path === '/health-info-basic' || to.path === '/health-info-detail') && hasCompletedProfile) {
    next('/dashboard/health-info');
    return;
  }

  if (to.path === '/dashboard/ingredient-library') {
    next('/dashboard/ingredient-substitute');
    return;
  }

  next();
});

export default router;
