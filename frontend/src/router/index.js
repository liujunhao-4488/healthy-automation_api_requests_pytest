import { createRouter, createWebHistory } from 'vue-router';

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
      {
        path: '',
        redirect: 'health-info'
      },
      {
        path: 'health-info',
        name: 'HealthInfo',
        component: () => import('../views/HealthInfo.vue')
      },
      {
        path: 'diet-goal',
        name: 'DietGoal',
        component: () => import('../views/DietGoal.vue')
      },
      {
        path: 'recipe-recommend',
        name: 'RecipeRecommend',
        component: () => import('../views/RecipeRecommend.vue')
      },
      {
        path: 'ingredient-substitute',
        name: 'IngredientSubstitute',
        component: () => import('../views/IngredientSubstitute.vue')
      },
      {
        path: 'diet-record',
        name: 'DietRecord',
        component: () => import('../views/DietRecord.vue')
      },
      {
        path: 'health-knowledge',
        name: 'HealthKnowledge',
        component: () => import('../views/HealthKnowledge.vue')
      },
      {
        path: 'custom-recipe',
        name: 'CustomRecipe',
        component: () => import('../views/CustomRecipe.vue')
      }
    ]
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
