<script setup>
/* ============================================================
   AdminShell.vue · 运营后台外壳
   ------------------------------------------------------------
   和用户端的 AppShell 完全独立：
     · 只挂在 /admin 路由下，不读取用户端会话
     · 左侧导航是运营功能，不出现健康档案、饮食记录等用户页面
     · 退出只清后台会话，不影响同一浏览器里的用户端登录
   ============================================================ */
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { confirmDialog } from '@/composables/useConfirm'
import SvgIcon from './SvgIcon.vue'

const route = useRoute()
const router = useRouter()
const store = useAppStore()

const menuOpen = ref(false)

/** 后台导航对应 AdminView 内部的 tab，用 query 保持地址与选中态一致 */
const navItems = [
  { key: 'users', to: '/admin?tab=users', icon: 'users', text: '用户管理' },
  { key: 'recipe', to: '/admin?tab=recipe', icon: 'book-open', text: '食谱管理' },
  { key: 'article', to: '/admin?tab=article', icon: 'news', text: '文章管理' },
  { key: 'ingredient', to: '/admin?tab=ingredient', icon: 'apple', text: '食材管理' }
]

const currentTab = computed(() => route.query.tab || 'users')
const adminInitial = computed(() => (store.adminName || '管')[0])

async function onLogout() {
  const ok = await confirmDialog('退出后需要重新登录后台，用户端的登录状态不受影响。', {
    title: '退出后台',
    okText: '退出',
    danger: true
  })
  if (!ok) return
  store.adminLogout()
  router.push('/admin/login')
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
      <small>运营后台</small>
    </span>
    <button class="mobile-menu-btn" aria-label="打开菜单" @click="menuOpen = true">
      <SvgIcon name="menu" />
    </button>
  </header>

  <!-- 后台导航 -->
  <aside class="app-nav" :class="{ 'is-open': menuOpen }">
    <RouterLink class="brand" to="/admin" @click="closeMenu">
      <span class="brand-mark">
        <SvgIcon name="leaf" :stroke-width="1.6" />
      </span>
      <span class="brand-text">
        <strong>膳衡</strong>
        <small>SHANHENG · 运营后台</small>
      </span>
    </RouterLink>

    <p class="nav-label">运营管理</p>
    <RouterLink
      v-for="item in navItems"
      :key="item.key"
      class="nav-item"
      :class="{ 'is-active': currentTab === item.key }"
      :to="item.to"
      @click="closeMenu"
    >
      <SvgIcon :name="item.icon" />
      <span>{{ item.text }}</span>
    </RouterLink>

    <div class="nav-user">
      <span class="nav-avatar">{{ adminInitial }}</span>
      <span class="grow">
        <span class="nav-user-name">{{ store.adminName }}</span>
        <span class="nav-user-role">管理员 · 仅后台权限</span>
      </span>
      <button class="nav-logout" title="退出后台" @click="onLogout">
        <SvgIcon name="logout" />
      </button>
    </div>
  </aside>

  <!-- 移动端遮罩 -->
  <div class="nav-scrim" :class="{ 'is-open': menuOpen }" @click="closeMenu" />

  <main class="app-content">
    <RouterView />
  </main>
</template>
