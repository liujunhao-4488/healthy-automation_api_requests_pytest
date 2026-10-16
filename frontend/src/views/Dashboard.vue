<template>
  <div class="app-shell">
    <!-- 侧边栏：与后台管理端共用同一套 app-* 结构 -->
    <aside class="app-sidebar">
      <div class="app-brand">
        <span class="app-brand__tag">Health Diet</span>
        <h2 class="app-brand__title">健康饮食</h2>
      </div>

      <el-menu :default-active="activeMenu" class="app-nav" router @select="handleMenuSelect">
        <el-menu-item index="/dashboard/health-info">
          <el-icon><UserFilled /></el-icon>
          <template #title>健康信息</template>
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
          <template #title>饮食健康助手</template>
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
          <el-icon><ChatDotRound /></el-icon>
          <template #title>交流论坛</template>
        </el-menu-item>
      </el-menu>
    </aside>

    <!-- 右侧主体：顶栏 + 内容区 -->
    <div class="app-body">
      <header class="app-header">
        <span class="app-header__title">{{ headerTitle }}</span>

        <div class="app-header__actions">
          <button
            class="app-icon-btn"
            type="button"
            aria-label="消息通知"
            @click="router.push('/dashboard/notifications')"
          >
            <el-badge
              :value="unreadNotificationCount"
              :hidden="unreadNotificationCount === 0"
              :max="99"
            >
              <el-icon :size="18"><Bell /></el-icon>
            </el-badge>
          </button>

          <el-dropdown trigger="hover" class="app-header__dropdown" @command="handleUserCommand">
            <div class="app-user">
              <el-avatar :size="32" :src="avatarSrc">{{ avatarFallback }}</el-avatar>
              <div class="app-user__meta">
                <span class="app-user__name">{{ username }}</span>
                <span class="app-user__sub">{{ userStore.email || '未设置邮箱' }}</span>
              </div>
              <el-icon class="app-user__arrow"><ArrowDown /></el-icon>
            </div>

            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>个人中心
                </el-dropdown-item>
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
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import {
  ArrowDown,
  Bell,
  BellFilled,
  ChatDotRound,
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

// 顶栏标题跟随当前路由（按前缀匹配，子页面也能命中）
const TITLE_RULES = [
  ['/dashboard/health-info', '健康信息'],
  ['/dashboard/profile', '个人中心'],
  ['/dashboard/collected-articles', '收藏文章'],
  ['/dashboard/collected-recipes', '收藏食谱'],
  ['/dashboard/diet-goal', '饮食目标'],
  ['/dashboard/recipe-recommend', '食谱推荐'],
  ['/dashboard/ingredient-substitute', '饮食健康助手'],
  ['/dashboard/custom-recipe', '自定义食谱'],
  ['/dashboard/diet-record', '饮食记录'],
  ['/dashboard/notifications', '消息通知'],
  ['/dashboard/health-knowledge', '交流论坛']
];

const headerTitle = computed(() => {
  const matched = TITLE_RULES.find(([prefix]) => route.path.startsWith(prefix));
  return matched ? matched[1] : '健康饮食';
});

const activeMenu = computed(() => {
  if (route.path.startsWith('/dashboard/health-info')) {
    return '/dashboard/health-info';
  }

  if (route.path.startsWith('/dashboard/diet-goal')) {
    return '/dashboard/diet-goal';
  }

  return route.path;
});

const handleMenuSelect = (key) => {
  router.push(key);
};

const handleUserCommand = (command) => {
  if (command === 'profile') {
    router.push('/dashboard/profile');
  } else if (command === 'logout') {
    logout();
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

<!-- 外壳样式见 src/styles/admin.css（与后台管理端共用一套视觉规范） -->
