/* ============================================================
   router/index.js · 路由表
   ------------------------------------------------------------
   静态版靠 13 个 html 文件 + location.href 跳转；
   这里改成一个 SPA，用 vue-router 管地址，不再整页刷新。

   原 pages/recipe-detail.html?id=1  →  /recipes/1
       pages/article-detail.html?id=1 →  /knowledge/1

   meta.nav 控制左侧导航高亮，所以详情页也能高亮父级菜单。
   ============================================================ */
import { createRouter, createWebHistory } from 'vue-router'
import { useAppStore } from '@/stores/app'
import AppShell from '@/components/AppShell.vue'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true, title: '登录 · 膳衡' }
  },
  {
    path: '/',
    component: AppShell,
    children: [
      {
        path: '',
        name: 'home',
        component: () => import('@/views/HomeView.vue'),
        meta: { nav: 'home', title: '首页 · 膳衡' }
      },
      {
        path: 'health',
        name: 'health',
        component: () => import('@/views/HealthView.vue'),
        meta: { nav: 'health', title: '健康档案 · 膳衡' }
      },
      {
        path: 'goal',
        name: 'goal',
        component: () => import('@/views/GoalView.vue'),
        meta: { nav: 'goal', title: '饮食目标 · 膳衡' }
      },
      {
        path: 'record',
        name: 'record',
        component: () => import('@/views/RecordView.vue'),
        meta: { nav: 'record', title: '饮食记录 · 膳衡' }
      },
      {
        path: 'recipes',
        name: 'recipes',
        component: () => import('@/views/RecipesView.vue'),
        meta: { nav: 'recipes', title: '食谱库 · 膳衡' }
      },
      {
        path: 'recipes/:id',
        name: 'recipe-detail',
        component: () => import('@/views/RecipeDetailView.vue'),
        meta: { nav: 'recipes', title: '食谱详情 · 膳衡' }
      },
      {
        path: 'ingredients',
        name: 'ingredients',
        component: () => import('@/views/IngredientsView.vue'),
        meta: { nav: 'ingredients', title: '食材库 · 膳衡' }
      },
      {
        path: 'knowledge',
        name: 'knowledge',
        component: () => import('@/views/KnowledgeView.vue'),
        meta: { nav: 'knowledge', title: '健康知识 · 膳衡' }
      },
      {
        path: 'knowledge/:id',
        name: 'article-detail',
        component: () => import('@/views/ArticleDetailView.vue'),
        meta: { nav: 'knowledge', title: '文章详情 · 膳衡' }
      },
      {
        path: 'assistant',
        name: 'assistant',
        component: () => import('@/views/AssistantView.vue'),
        meta: { nav: 'assistant', title: 'AI 助手 · 膳衡' }
      },
      {
        path: 'account',
        name: 'account',
        component: () => import('@/views/AccountView.vue'),
        meta: { nav: 'account', title: '个人中心 · 膳衡' }
      },
      {
        path: 'admin',
        name: 'admin',
        component: () => import('@/views/AdminView.vue'),
        meta: { nav: 'admin', title: '管理后台 · 膳衡' }
      }
    ]
  },
  // 兜底：地址打错回到首页
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, saved) {
    return saved || { top: 0 }
  }
})

/* 登录守卫：替代静态版 App.boot() 里的 session 检查 */
router.beforeEach((to) => {
  const store = useAppStore()
  if (!to.meta.public && !store.isLoggedIn) return { name: 'login' }
  if (to.name === 'login' && store.isLoggedIn) return { name: 'home' }
})

/* 顺手同步页面标题 */
router.afterEach((to) => {
  if (to.meta.title) document.title = to.meta.title
})

export default router
