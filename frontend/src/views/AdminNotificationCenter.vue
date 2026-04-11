<template>
  <div class="admin-page">
    <div class="page-top">
      <div>
        <h2>系统通知管理</h2>
        <p>向全部用户或指定用户发布系统通知，用于饮食提醒、活动公告和消息推送。</p>
      </div>
    </div>

    <el-card class="editor-card">
      <el-form :model="form" label-width="100px">
        <div class="grid-two">
          <el-form-item label="通知类型">
            <el-select v-model="form.type">
              <el-option label="系统通知" value="system" />
              <el-option label="饮食提醒" value="diet_reminder" />
              <el-option label="文章推荐" value="article_recommend" />
              <el-option label="风险提醒" value="warning" />
            </el-select>
          </el-form-item>
          <el-form-item label="目标用户">
            <el-select v-model="form.userId" clearable placeholder="留空则发送给全部正常用户">
              <el-option
                v-for="user in users"
                :key="user.userId"
                :label="`${user.username} (${user.email})`"
                :value="user.userId"
              />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="通知标题">
          <el-input v-model="form.title" maxlength="100" />
        </el-form-item>
        <el-form-item label="通知内容">
          <el-input v-model="form.content" type="textarea" :rows="5" maxlength="500" show-word-limit />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="submitNotification">发布通知</el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import notificationApi from '../api/notification';
import userApi from '../api/user';

const submitting = ref(false);
const users = ref([]);

const createForm = () => ({
  type: 'system',
  userId: null,
  title: '',
  content: ''
});

const form = reactive(createForm());

const loadUsers = async () => {
  try {
    const response = await userApi.getAdminUsers();
    users.value = response.code === 200 && Array.isArray(response.data) ? response.data.filter((item) => item.status === 1) : [];
  } catch (error) {
    ElMessage.error(error.message || '加载用户列表失败');
  }
};

const resetForm = () => {
  Object.assign(form, createForm());
};

const submitNotification = async () => {
  if (!form.title.trim() || !form.content.trim()) {
    ElMessage.warning('请先填写通知标题和内容');
    return;
  }

  submitting.value = true;
  try {
    const response = await notificationApi.publishNotification({
      type: form.type,
      userId: form.userId,
      title: form.title.trim(),
      content: form.content.trim()
    });
    if (response.code === 200) {
      ElMessage.success(`通知发布成功，已发送 ${response.data} 条`);
      resetForm();
      return;
    }
    ElMessage.error(response.message || '通知发布失败');
  } catch (error) {
    ElMessage.error(error.message || '通知发布失败');
  } finally {
    submitting.value = false;
  }
};

onMounted(() => {
  loadUsers();
});
</script>

<style scoped>
.admin-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.page-top h2 {
  margin: 0 0 8px;
}

.page-top p {
  margin: 0;
  color: #73887b;
}

.editor-card {
  border-radius: 22px;
}

.grid-two {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 900px) {
  .grid-two {
    grid-template-columns: 1fr;
  }
}
</style>
