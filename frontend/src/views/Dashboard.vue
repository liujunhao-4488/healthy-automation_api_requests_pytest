<template>
  <div class="dashboard-container">
    <el-container style="height: 100%;">
      <!-- 侧边栏 -->
      <el-aside width="200px" class="sidebar">
        <div class="logo">
          <h2>健康饮食</h2>
        </div>
        <el-menu
          :default-active="activeMenu"
          class="el-menu-vertical-demo"
          router
          @select="handleMenuSelect"
          background-color="#409EFF"
          text-color="#fff"
          active-text-color="#fff"
        >
          <!-- 健康信息 -->
          <el-menu-item index="/dashboard/health-info">
            <el-icon><UserFilled /></el-icon>
            <template #title>健康信息</template>
          </el-menu-item>
          <!-- 饮食目标 -->
          <el-menu-item index="/dashboard/diet-goal">
            <el-icon><BellFilled /></el-icon>
            <template #title>饮食目标</template>
          </el-menu-item>
          <!-- 食谱推荐 -->
          <el-menu-item index="/dashboard/recipe-recommend">
            <el-icon><StarFilled /></el-icon>
            <template #title>食谱推荐</template>
          </el-menu-item>
          <!-- 食材替代 -->
          <el-menu-item index="/dashboard/ingredient-substitute">
            <el-icon><Refresh /></el-icon>
            <template #title>食材替代</template>
          </el-menu-item>
          <!-- 自定义食谱 -->
          <el-menu-item index="/dashboard/custom-recipe">
            <el-icon><Edit /></el-icon>
            <template #title>自定义食谱</template>
          </el-menu-item>
          <!-- 饮食记录 -->
          <el-menu-item index="/dashboard/diet-record">
            <el-icon><Notebook /></el-icon>
            <template #title>饮食记录</template>
          </el-menu-item>
          <!-- 健康知识 -->
          <el-menu-item index="/dashboard/health-knowledge">
            <el-icon><Reading /></el-icon>
            <template #title>健康知识</template>
          </el-menu-item>
          <!-- 退出登录：增加index，避免选中状态异常 -->
          <el-menu-item index="/logout" @click="logout">
            <el-icon><SwitchButton /></el-icon>
            <template #title>退出登录</template>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-container style="height: 100%;">
        <el-header class="header">
          <div class="user-info">
            <span>欢迎，{{ username }}</span>
          </div>
        </el-header>
        <el-main class="main-content">
          <router-view></router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useUserStore } from '../stores/user';
import { ElMessage } from 'element-plus';
// 导入Element Plus图标（确认所有图标都存在）
import { 
  UserFilled, BellFilled, StarFilled, 
  Refresh, Notebook, Reading, SwitchButton, Edit 
} from '@element-plus/icons-vue';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

// 计算属性：获取用户名（增加空值兜底）
const username = computed(() => userStore.username || '用户');
// 计算属性：当前激活的菜单（匹配路由路径）
const activeMenu = computed(() => route.path);

// 菜单选中事件
const handleMenuSelect = (key, keyPath) => {
  console.log('选中菜单：', key, keyPath);
  // 排除退出登录的index，避免路由跳转
  if (key !== '/logout') {
    router.push(key);
  }
};

// 退出登录逻辑
const logout = () => {
  try {
    userStore.logout();
    ElMessage.success('退出登录成功');
    router.push('/login');
  } catch (error) {
    ElMessage.error('退出登录失败：' + error.message);
  }
};

// 挂载时检查登录状态
onMounted(() => {
  if (!userStore.isLoggedIn) {
    router.push('/login');
    ElMessage.warning('请先登录');
  }
});
</script>

<style scoped>
/* 容器样式：确保100%高度 */
.dashboard-container {
  height: 100vh;
  width: 100%;
  overflow: hidden;
}

/* 侧边栏样式 */
.sidebar {
  height: 100%;
  background-color: #409EFF !important;
}

.logo {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.logo h2 {
  margin: 0;
  color: #fff;
  font-size: 18px;
  font-weight: 600;
}

/* 菜单样式优化 */
:deep(.el-menu-vertical-demo) {
  border-right: none !important;
}

:deep(.el-menu-item) {
  color: rgba(255, 255, 255, 0.9) !important;
  height: 50px !important;
  line-height: 50px !important;
}

:deep(.el-menu-item:hover) {
  background-color: rgba(255, 255, 255, 0.1) !important;
}

:deep(.el-menu-item.is-active) {
  background-color: rgba(255, 255, 255, 0.2) !important;
  color: #fff !important;
}

/* 头部样式 */
.header {
  background-color: #fff;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 0 20px;
  height: 60px !important;
}

.user-info {
  font-size: 14px;
  color: #333;
}

/* 主内容区样式 */
.main-content {
  padding: 20px;
  background-color: #f5f5f5;
  height: calc(100% - 60px) !important;
  overflow-y: auto;
}
</style>