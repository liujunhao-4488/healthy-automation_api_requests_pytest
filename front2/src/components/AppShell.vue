<script setup>
/* ============================================================
   AppShell.vue · 应用外壳
   ------------------------------------------------------------
   静态版把「顶部移动条 + 左侧导航 + 用户区」抄在每个 html 里，
   现在抽成一处：所有登录后的页面都套在这个布局里。

   左侧导航的高亮不再手动加 .is-active，而是看路由的 meta.nav，
   所以详情页（/recipes/1）也能让「食谱库」保持高亮。
   ============================================================ */
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { recipesApi } from '@/services/api'
import { confirmDialog } from '@/composables/useConfirm'
import SvgIcon from './SvgIcon.vue'

const route = useRoute()
const router = useRouter()
const store = useAppStore()

/** 移动端抽屉是否打开 */
const menuOpen = ref(false)

/**
 * 登录后同步一次「我收藏了哪些食谱」。
 * 收藏的真源在后端（/recipe/collect/list），本地 recipeCollectIds 只是页面用的缓存。
 * 放在 AppShell 里而不是每个页面各自拉，是因为所有登录后页面都套这层壳，一次覆盖全站。
 */
onMounted(async () => {
  if (!store.isLoggedIn) return
  const res = await recipesApi.collected()
  if (res.code === 200) store.setCollectIds(res.data.map((r) => r.id))
})

/** 导航分组，照抄静态版结构 */
const navGroups = [
  {
    label: '我的健康',
    items: [
      { nav: 'home', to: '/', icon: 'home', text: '首页' },
      { nav: 'health', to: '/health', icon: 'heart-pulse', text: '健康档案' },
      { nav: 'goal', to: '/goal', icon: 'target', text: '饮食目标' },
      { nav: 'record', to: '/record', icon: 'notebook', text: '饮食记录' }
    ]
  },
  {
    label: '内容与工具',
    items: [
      { nav: 'recipes', to: '/recipes', icon: 'book-open', text: '食谱库' },
      { nav: 'ingredients', to: '/ingredients', icon: 'apple', text: '食材库' },
      { nav: 'knowledge', to: '/knowledge', icon: 'news', text: '健康知识' },
      { nav: 'assistant', to: '/assistant', icon: 'sparkles', text: 'AI 助手' }
    ]
  },
  {
    label: '账户',
    items: [
      { nav: 'account', to: '/account', icon: 'user', text: '个人中心', badge: true },
      { nav: 'admin', to: '/admin', icon: 'settings', text: '管理后台' }
    ]
  }
]

const avatarText = computed(() => (store.displayName || '用')[0])
const roleText = computed(() => (store.isAdmin ? '管理员 · 平台运营' : '普通用户'))

const isActive = (item) => route.meta.nav === item.nav

async function onLogout() {
  const ok = await confirmDialog('退出后需要重新登录，未提交的记录草稿将保留在本机。', {
    title: '退出登录',
    okText: '退出',
    danger: true
  })
  if (!ok) return
  store.logout()
  router.push('/login')
}

function closeMenu() {
  menuOpen.value = false
}
</script>

<template>
  <!-- 移动端顶栏 -->
  <header class="mobile-bar">
    <span class="brand-mark">
      <SvgIcon name="leaf" :stroke-width="1.6" />
    </span>
    <span class="brand-text">
      <strong>膳衡</strong>
      <small>SHANHENG</small>
    </span>
    <button class="mobile-menu-btn" aria-label="打开菜单" @click="menuOpen = true">
      <SvgIcon name="menu" />
    </button>
  </header>

  <!-- 左侧导航 -->
  <aside class="app-nav" :class="{ 'is-open': menuOpen }">
    <RouterLink class="brand" to="/" @click="closeMenu">
      <span class="brand-mark">
        <SvgIcon name="leaf" :stroke-width="1.6" />
      </span>
      <span class="brand-text">
        <strong>膳衡</strong>
        <small>SHANHENG · 健康饮食</small>
      </span>
    </RouterLink>

    <template v-for="group in navGroups" :key="group.label">
      <p class="nav-label">{{ group.label }}</p>
      <RouterLink
        v-for="item in group.items"
        :key="item.nav"
        class="nav-item"
        :class="{ 'is-active': isActive(item) }"
        :to="item.to"
        @click="closeMenu"
      >
        <SvgIcon :name="item.icon" />
        <span>{{ item.text }}</span>
        <span v-if="item.badge" class="nav-badge" :style="{ display: store.unreadCount ? 'grid' : 'none' }">
          {{ store.unreadCount }}
        </span>
      </RouterLink>
    </template>

    <div class="nav-user">
      <span class="nav-avatar">{{ avatarText }}</span>
      <span class="grow">
        <span class="nav-user-name">{{ store.displayName }}</span>
        <span class="nav-user-role">{{ roleText }}</span>
      </span>
      <button class="nav-logout" title="退出登录" @click="onLogout">
        <SvgIcon name="logout" />
      </button>
    </div>
  </aside>

  <!-- 移动端遮罩 -->
  <div class="nav-scrim" :class="{ 'is-open': menuOpen }" @click="closeMenu" />

  <main class="app-content">
    <div class="page-shell">
      <RouterView />
    </div>
  </main>
</template>
