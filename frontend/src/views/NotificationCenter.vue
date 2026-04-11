<template>
  <div class="notification-page">
    <section class="page-hero">
      <div>
        <p class="eyebrow">MESSAGE CENTER</p>
        <h2>消息中心</h2>
        <p>集中查看饮食提醒、系统通知和推荐消息。</p>
      </div>
      <div class="hero-actions">
        <el-button plain @click="loadNotifications">刷新消息</el-button>
        <el-button type="primary" :disabled="!unreadCount" @click="markAllAsRead">全部标记已读</el-button>
      </div>
    </section>

    <div class="summary-row">
      <div class="summary-card accent-green">
        <span>消息总数</span>
        <strong>{{ notifications.length }}</strong>
      </div>
      <div class="summary-card accent-rose">
        <span>未读消息</span>
        <strong>{{ unreadCount }}</strong>
      </div>
    </div>

    <el-card class="list-card" shadow="never">
      <template #header>
        <div class="section-head">
          <span>全部消息</span>
          <el-tag type="danger" effect="plain">{{ unreadCount }} 条未读</el-tag>
        </div>
      </template>

      <div v-if="notifications.length" class="notification-list">
        <div
          v-for="item in notifications"
          :key="item.id"
          class="notification-row"
          :class="{ unread: !item.isRead }"
        >
          <div class="notification-copy">
            <div class="notification-top">
              <strong>{{ item.title }}</strong>
              <el-tag size="small" :type="item.isRead ? 'info' : 'danger'" effect="plain">
                {{ item.isRead ? '已读' : '未读' }}
              </el-tag>
            </div>
            <p>{{ item.content }}</p>
            <span>{{ formatDateTime(item.createTime || item.sendTime) }}</span>
          </div>
          <div class="notification-actions">
            <el-button v-if="!item.isRead" text type="primary" @click="markNotificationRead(item)">
              标记已读
            </el-button>
            <el-button text type="danger" @click="deleteNotification(item)">
              删除
            </el-button>
          </div>
        </div>
      </div>

      <el-empty v-else description="暂时没有消息提醒" />
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import notificationApi from '../api/notification';

const notifications = ref([]);

const unreadCount = computed(() => notifications.value.filter((item) => !item.isRead).length);

const formatDateTime = (value) => {
  if (!value) {
    return '--';
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '--' : date.toLocaleString('zh-CN');
};

const loadNotifications = async () => {
  try {
    const response = await notificationApi.getNotifications();
    notifications.value = response.code === 200 && Array.isArray(response.data) ? response.data : [];
  } catch (error) {
    ElMessage.error(error.message || '获取消息失败');
  }
};

const markNotificationRead = async (item) => {
  try {
    const response = await notificationApi.markAsRead(item.id);
    if (response.code === 200) {
      item.isRead = 1;
      ElMessage.success('已标记为已读');
    }
  } catch (error) {
    ElMessage.error(error.message || '标记已读失败');
  }
};

const deleteNotification = async (item) => {
  try {
    const response = await notificationApi.deleteNotification(item.id);
    if (response.code === 200) {
      notifications.value = notifications.value.filter((notification) => notification.id !== item.id);
      ElMessage.success('消息已删除');
    }
  } catch (error) {
    ElMessage.error(error.message || '删除消息失败');
  }
};

const markAllAsRead = async () => {
  const unreadItems = notifications.value.filter((item) => !item.isRead);
  if (!unreadItems.length) {
    return;
  }

  try {
    await Promise.all(unreadItems.map((item) => notificationApi.markAsRead(item.id)));
    unreadItems.forEach((item) => {
      item.isRead = 1;
    });
    ElMessage.success('所有消息已标记为已读');
  } catch (error) {
    ElMessage.error(error.message || '批量标记已读失败');
  }
};

onMounted(() => {
  loadNotifications();
});
</script>

<style scoped>
.notification-page {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.page-hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  padding: 28px 30px;
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

.page-hero h2 {
  margin: 0;
  font-family: 'Noto Serif SC', serif;
  font-size: 30px;
  color: #334235;
}

.page-hero p {
  margin: 8px 0 0;
  color: #6b796d;
}

.hero-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.summary-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.summary-card {
  min-height: 120px;
  padding: 22px;
  border-radius: 22px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  color: #334235;
  box-shadow: 0 12px 28px rgba(59, 79, 63, 0.06);
}

.summary-card span {
  color: #738075;
}

.summary-card strong {
  font-size: 28px;
  font-weight: 600;
}

.accent-green {
  background: linear-gradient(180deg, #f4fbf5 0%, #dcefdc 100%);
}

.accent-rose {
  background: linear-gradient(180deg, #fff7f7 0%, #f6dede 100%);
}

.list-card {
  border: 1px solid #e4ecdf;
  border-radius: 22px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #334235;
  font-weight: 600;
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.notification-row {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  padding: 16px 18px;
  border-radius: 18px;
  background: #f8fbf8;
  border: 1px solid #e3ece4;
}

.notification-row.unread {
  border-color: #f2b6b6;
  background: #fff9f9;
}

.notification-copy {
  flex: 1;
}

.notification-top {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 6px;
}

.notification-row strong {
  color: #334235;
}

.notification-row p {
  margin: 0 0 6px;
  color: #627568;
  line-height: 1.7;
}

.notification-row span {
  color: #8a998d;
  font-size: 13px;
}

.notification-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: center;
  gap: 6px;
  min-width: 90px;
}

@media (max-width: 768px) {
  .page-hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .summary-row {
    grid-template-columns: 1fr;
  }

  .notification-row {
    flex-direction: column;
  }

  .notification-actions {
    align-items: flex-start;
    min-width: auto;
  }
}
</style>
