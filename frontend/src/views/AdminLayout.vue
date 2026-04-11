<template>
  <div class="admin-layout">
    <aside class="sidebar">
      <div class="brand">
        <p class="brand-tag">ADMIN CONSOLE</p>
        <h2>后台管理中心</h2>
      </div>

      <el-menu :default-active="activeMenu" router class="admin-menu">
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

      <div class="sidebar-actions">
        <el-button text @click="goUserSide">进入用户端</el-button>
        <el-button type="danger" plain @click="logout">退出登录</el-button>
      </div>
    </aside>

    <main class="content">
      <section class="page-shell">
        <router-view />
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Bell, Collection, DataBoard, Files, Reading, User } from '@element-plus/icons-vue';
import { useUserStore } from '../stores/user';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

const activeMenu = computed(() => route.path);

const goUserSide = () => {
  router.push('/dashboard/health-info');
};

const logout = () => {
  userStore.logout();
  ElMessage.success('已退出登录');
  router.push('/login');
};
</script>

<style scoped>
.admin-layout {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 260px 1fr;
  background: #eff4ef;
}

.sidebar {
  display: flex;
  flex-direction: column;
  padding: 28px 18px;
  background: linear-gradient(180deg, #21382c 0%, #2d4a38 100%);
  color: #f5fbf6;
}

.brand {
  margin-bottom: 24px;
}

.brand-tag {
  margin: 0 0 8px;
  font-size: 12px;
  letter-spacing: 0.12em;
  color: rgba(245, 251, 246, 0.6);
}

.brand h2 {
  margin: 0;
  font-size: 24px;
}

:deep(.admin-menu) {
  border-right: none;
  background: transparent;
}

:deep(.admin-menu .el-menu-item) {
  margin-bottom: 8px;
  border-radius: 14px;
  color: rgba(245, 251, 246, 0.74);
}

:deep(.admin-menu .el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

:deep(.admin-menu .el-menu-item.is-active) {
  background: #7ba088;
  color: #fff;
}

.sidebar-actions {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sidebar-actions :deep(.el-button) {
  justify-content: flex-start;
}

.content {
  padding: 24px;
}

.page-shell {
  min-height: calc(100vh - 48px);
}

@media (max-width: 900px) {
  .admin-layout {
    grid-template-columns: 1fr;
  }

  .sidebar {
    padding-bottom: 16px;
  }
}
</style>
