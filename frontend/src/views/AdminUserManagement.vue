<template>
  <div class="admin-users-page">
    <section class="hero-card">
      <div>
        <p class="eyebrow">User Management</p>
        <h2>用户管理</h2>
        <p class="hero-copy">查看系统用户列表，并对普通账号执行启用或禁用操作。</p>
      </div>
      <el-button class="refresh-button" @click="loadUsers" :loading="loading">刷新列表</el-button>
    </section>

    <el-card class="table-card" shadow="never">
      <div class="toolbar">
        <el-input
          v-model="keyword"
          placeholder="搜索用户名、邮箱或手机号"
          clearable
          class="search-input"
        />
      </div>

      <el-table :data="filteredUsers" v-loading="loading" stripe>
        <el-table-column label="头像" width="90">
          <template #default="{ row }">
            <el-avatar :size="42" :src="row.avatar || ''">
              {{ (row.username || 'U').trim().charAt(0).toUpperCase() }}
            </el-avatar>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="email" label="邮箱" min-width="200" />
        <el-table-column prop="phone" label="手机号" min-width="140" />
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'warning' : 'info'" effect="plain">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.status === 0 ? 'danger' : 'success'" effect="plain">
              {{ row.status === 0 ? '已禁用' : '正常' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="注册时间" min-width="140">
          <template #default="{ row }">
            {{ formatDate(row.createTime) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.role !== 'admin'"
              :type="row.status === 0 ? 'success' : 'danger'"
              plain
              size="small"
              :loading="updatingUserId === row.userId"
              @click="toggleStatus(row)"
            >
              {{ row.status === 0 ? '启用账号' : '禁用账号' }}
            </el-button>
            <el-tag v-else type="warning" effect="plain">不可禁用</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import userApi from '../api/user';

const loading = ref(false);
const keyword = ref('');
const users = ref([]);
const updatingUserId = ref(null);

const filteredUsers = computed(() => {
  const query = keyword.value.trim().toLowerCase();
  if (!query) {
    return users.value;
  }

  return users.value.filter((user) =>
    [user.username, user.email, user.phone].some((field) => (field || '').toLowerCase().includes(query))
  );
});

const formatDate = (value) => {
  if (!value) {
    return '--';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '--';
  }
  return date.toLocaleDateString('zh-CN');
};

const loadUsers = async () => {
  loading.value = true;
  try {
    const response = await userApi.getAdminUsers();
    if (response.code === 200 && Array.isArray(response.data)) {
      users.value = response.data;
      return;
    }
    ElMessage.error(response.message || '获取用户列表失败');
  } catch (error) {
    ElMessage.error(error.message || '获取用户列表失败');
  } finally {
    loading.value = false;
  }
};

const toggleStatus = async (row) => {
  const nextStatus = row.status === 0 ? 1 : 0;
  const actionText = nextStatus === 0 ? '启用' : '禁用';

  try {
    await ElMessageBox.confirm(`确定要${actionText}账号“${row.username}”吗？`, `${actionText}确认`, {
      type: 'warning'
    });
  } catch (error) {
    return;
  }

  updatingUserId.value = row.userId;
  try {
    const response = await userApi.updateUserStatus(row.userId, nextStatus);
    if (response.code === 200 && response.data) {
      users.value = users.value.map((item) => (item.userId === row.userId ? response.data : item));
      ElMessage.success(`账号已${actionText}`);
      return;
    }
    ElMessage.error(response.message || `${actionText}失败`);
  } catch (error) {
    ElMessage.error(error.message || `${actionText}失败`);
  } finally {
    updatingUserId.value = null;
  }
};

onMounted(() => {
  loadUsers();
});
</script>

<style scoped>
.admin-users-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.hero-card {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 20px;
  padding: 26px 28px;
  border-radius: 24px;
  background:
    radial-gradient(circle at top left, rgba(196, 226, 210, 0.35), transparent 42%),
    linear-gradient(135deg, #f9fffb 0%, #edf7ef 100%);
  border: 1px solid #dcecdf;
}

.eyebrow {
  margin: 0 0 10px;
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #6f8f72;
}

.hero-card h2 {
  margin: 0;
  font-size: 30px;
  color: #334235;
}

.hero-copy {
  margin: 12px 0 0;
  color: #68796b;
  line-height: 1.7;
}

.refresh-button {
  border-color: #cfe0d2;
  color: #46614a;
  background: #f4fbf5;
}

.table-card {
  border: 1px solid #e4ecdf;
  border-radius: 24px;
}

.toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}

.search-input {
  width: 320px;
}

@media (max-width: 768px) {
  .hero-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .search-input {
    width: 100%;
  }
}
</style>
