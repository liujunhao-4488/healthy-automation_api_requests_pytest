<template>
  <div class="app-shell">
    <!-- 侧边栏：与用户端 Dashboard 使用同一套 app-* 结构与样式 -->
    <aside class="app-sidebar">
      <div class="app-brand">
        <span class="app-brand__tag">Admin Console</span>
        <h2 class="app-brand__title">后台管理中心</h2>
      </div>

      <el-menu :default-active="activeMenu" router class="app-nav">
        <el-menu-item index="/admin/overview">
          <el-icon><DataBoard /></el-icon>
          <span>后台总览</span>
        </el-menu-item>
        <el-menu-item index="/admin/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/ingredients">
          <el-icon><Collection /></el-icon>
          <span>食材库管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/recipes">
          <el-icon><Files /></el-icon>
          <span>食谱库管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/articles">
          <el-icon><Reading /></el-icon>
          <span>健康文章管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/notifications">
          <el-icon><Bell /></el-icon>
          <span>系统通知</span>
        </el-menu-item>
      </el-menu>
    </aside>

    <!-- 右侧主体：顶栏 + 内容区 -->
    <div class="app-body">
      <header class="app-header">
        <span class="app-header__title">{{ currentTitle }}</span>

        <div class="app-header__actions">
          <el-dropdown trigger="hover" class="app-header__dropdown" @command="handleUserCommand">
            <div class="app-user">
              <el-avatar :size="32" :src="userStore.avatar || ''">
                {{ adminAvatarFallback }}
              </el-avatar>
              <div class="app-user__meta">
                <span class="app-user__name">{{ userStore.username || '管理员' }}</span>
                <span class="app-user__sub">{{ userStore.email || '管理员' }}</span>
              </div>
              <el-icon class="app-user__arrow"><ArrowDown /></el-icon>
            </div>

            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="app-main">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import {
  ArrowDown,
  Bell,
  Collection,
  DataBoard,
  Files,
  Reading,
  SwitchButton,
  User
} from '@element-plus/icons-vue';
import { useUserStore } from '../stores/user';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

const activeMenu = computed(() => route.path);
const adminAvatarFallback = computed(() =>
  (userStore.username || 'A').trim().charAt(0).toUpperCase()
);

// 顶栏标题跟随当前路由，替代原来"顶栏左侧一片空白"的观感
const MENU_TITLES = {
  '/admin/overview': '后台总览',
  '/admin/users': '用户管理',
  '/admin/ingredients': '食材库管理',
  '/admin/recipes': '食谱库管理',
  '/admin/articles': '健康文章管理',
  '/admin/notifications': '系统通知'
};

const currentTitle = computed(() => MENU_TITLES[route.path] || '后台管理中心');

const logout = () => {
  userStore.logout();
  ElMessage.success('已退出登录');
  router.push('/login');
};

const handleUserCommand = (command) => {
  if (command === 'logout') {
    logout();
  }
};
</script>

<!-- 外壳样式见 src/styles/admin.css（与 Dashboard 共用一套视觉规范） -->
