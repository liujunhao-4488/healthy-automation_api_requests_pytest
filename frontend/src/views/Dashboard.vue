<template>
  <div class="dashboard-container">
    <el-container style="height: 100%;">
      <el-aside width="220px" class="sidebar">
        <div class="logo">
          <h2>健康饮食</h2>
        </div>

        <el-menu :default-active="activeMenu" class="menu" router @select="handleMenuSelect">
          <el-menu-item index="/dashboard/health-info">
            <el-icon><UserFilled /></el-icon>
            <template #title>健康信息</template>
          </el-menu-item>
          <el-menu-item index="/dashboard/profile">
            <el-icon><User /></el-icon>
            <template #title>个人中心</template>
          </el-menu-item>
          <el-menu-item index="/dashboard/diet-goal">
            <el-icon><BellFilled /></el-icon>
            <template #title>饮食目标</template>
          </el-menu-item>
          <el-menu-item index="/dashboard/recipe-recommend">
            <el-icon><StarFilled /></el-icon>
            <template #title>食谱推荐</template>
          </el-menu-item>
          <el-menu-item index="/dashboard/ingredient-substitute">
            <el-icon><Refresh /></el-icon>
            <template #title>食材小助手</template>
          </el-menu-item>
          <el-menu-item index="/dashboard/custom-recipe">
            <el-icon><Edit /></el-icon>
            <template #title>自定义食谱</template>
          </el-menu-item>
          <el-menu-item index="/dashboard/diet-record">
            <el-icon><Notebook /></el-icon>
            <template #title>饮食记录</template>
          </el-menu-item>
          <el-menu-item index="/dashboard/health-knowledge">
            <el-icon><Reading /></el-icon>
            <template #title>健康知识</template>
          </el-menu-item>
          <el-menu-item index="/logout" @click="logout">
            <el-icon><SwitchButton /></el-icon>
            <template #title>退出登录</template>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container style="height: 100%;">
        <el-header class="header">
          <button class="notification-trigger" type="button" @click="router.push('/dashboard/notifications')">
            <el-badge :value="unreadNotificationCount" :hidden="unreadNotificationCount === 0" :max="99">
              <el-icon :size="18"><Bell /></el-icon>
            </el-badge>
          </button>

          <div class="header-user" @click="router.push('/dashboard/profile')">
            <el-avatar :size="36" :src="avatarSrc">{{ avatarFallback }}</el-avatar>
            <div class="header-user-copy">
              <strong>{{ username }}</strong>
              <span>{{ userStore.email || '未设置邮箱' }}</span>
            </div>
          </div>
        </el-header>

        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import {
  Bell,
  BellFilled,
  Edit,
  Notebook,
  Reading,
  Refresh,
  StarFilled,
  SwitchButton,
  User,
  UserFilled
} from '@element-plus/icons-vue';
import { useUserStore } from '../stores/user';
import notificationApi from '../api/notification';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();
const unreadNotificationCount = ref(0);

const username = computed(() => userStore.username || '用户');
const avatarSrc = computed(() => userStore.avatar || '');
const avatarFallback = computed(() => (userStore.username || 'U').trim().charAt(0).toUpperCase());

const activeMenu = computed(() => {
  if (route.path.startsWith('/dashboard/health-info')) {
    return '/dashboard/health-info';
  }

  if (
    route.path.startsWith('/dashboard/profile') ||
    route.path.startsWith('/dashboard/notifications') ||
    route.path.startsWith('/dashboard/collected-articles') ||
    route.path.startsWith('/dashboard/collected-recipes')
  ) {
    return '/dashboard/profile';
  }

  if (route.path.startsWith('/dashboard/diet-goal')) {
    return '/dashboard/diet-goal';
  }

  return route.path;
});

const handleMenuSelect = (key) => {
  if (key !== '/logout') {
    router.push(key);
  }
};

const loadUnreadNotificationCount = async () => {
  if (!userStore.isLoggedIn) {
    unreadNotificationCount.value = 0;
    return;
  }

  try {
    const response = await notificationApi.getNotifications();
    const notifications = response.code === 200 && Array.isArray(response.data) ? response.data : [];
    unreadNotificationCount.value = notifications.filter((item) => !item.isRead).length;
  } catch (error) {
    unreadNotificationCount.value = 0;
  }
};

const logout = () => {
  userStore.logout();
  unreadNotificationCount.value = 0;
  ElMessage.success('退出登录成功');
  router.push('/login');
};

onMounted(() => {
  if (!userStore.isLoggedIn) {
    router.push('/login');
    ElMessage.warning('请先登录');
    return;
  }

  loadUnreadNotificationCount();
});

watch(
  () => route.fullPath,
  () => {
    if (route.path.startsWith('/dashboard')) {
      loadUnreadNotificationCount();
    }
  }
);
</script>

<style scoped>
.dashboard-container {
  height: 100vh;
  width: 100%;
  overflow: hidden;
}

.sidebar {
  height: 100%;
  background-color: #3d4a3e !important;
}

.logo {
  padding: 24px 20px;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo h2 {
  margin: 0;
  color: #f7faf8;
  font-family: 'Noto Serif SC', serif;
  font-size: 18px;
  font-weight: 500;
  letter-spacing: 2px;
}

:deep(.menu) {
  border-right: none !important;
  background-color: transparent !important;
}

:deep(.el-menu-item) {
  color: rgba(247, 250, 248, 0.7) !important;
  height: 48px !important;
  line-height: 48px !important;
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 14px;
  margin: 4px 8px;
  border-radius: 4px;
  transition: all 0.25s ease;
}

:deep(.el-menu-item:hover) {
  background-color: rgba(123, 160, 136, 0.3) !important;
  color: #f7faf8 !important;
}

:deep(.el-menu-item.is-active) {
  background-color: #7ba088 !important;
  color: #fff !important;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e8f0ea;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
  padding: 0 24px;
  height: 56px !important;
}

.notification-trigger {
  width: 40px;
  height: 40px;
  border: 1px solid #dfe8df;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #f8fbf8;
  color: #4a5f50;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-right: 2px;
}

.notification-trigger:hover {
  border-color: #a6c3ab;
  background: #eef7f0;
  box-shadow: 0 10px 22px rgba(80, 108, 86, 0.08);
}

.header-user {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.header-user-copy {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  line-height: 1.3;
}

.header-user-copy strong {
  color: #425248;
  font-size: 14px;
}

.header-user-copy span {
  color: #8a988d;
  font-size: 12px;
}

.main-content {
  padding: 8px 24px 24px;
  background-color: #f7faf8;
  height: calc(100% - 56px) !important;
  overflow-y: auto;
}
</style>
