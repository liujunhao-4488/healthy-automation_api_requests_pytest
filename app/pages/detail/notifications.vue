<template>
  <view class="page-shell safe-bottom">
    <view class="page-content notifications-page">
      <view class="hero-card card">
        <view>
          <view class="hero-title">消息中心</view>
          <view class="hero-desc">查看系统通知、饮食提醒与状态更新。</view>
        </view>
        <text class="hero-action" @click="loadNotifications">刷新</text>
      </view>

      <view class="summary-card soft-card">
        <text class="summary-label">未读消息</text>
        <text class="summary-value">{{ unreadCount }}</text>
      </view>

      <view v-if="loading" class="card empty-card">
        <text>正在加载通知...</text>
      </view>

      <view v-else-if="notifications.length" class="list-stack">
        <view v-for="item in notifications" :key="item.id" class="card notice-card">
          <view class="notice-head">
            <view>
              <text class="notice-title">{{ item.title }}</text>
              <text class="notice-time">{{ item.timeText }}</text>
            </view>
            <text class="notice-state" :class="{ unread: !item.isRead }">{{ item.isRead ? '已读' : '未读' }}</text>
          </view>
          <text class="notice-content">{{ item.content }}</text>
          <view class="action-row">
            <button class="secondary-button small-btn" @click="markRead(item)">标记已读</button>
            <button class="secondary-button small-btn danger-btn" @click="deleteItem(item)">删除</button>
          </view>
        </view>
      </view>

      <view v-else class="card empty-card">
        <text>当前暂无通知</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import notificationApi from '@/api/notification'
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

const loading = ref(false)
const notifications = ref([])

const normalizeNotification = (item) => ({
  ...item,
  title: item.title || item.subject || '系统通知',
  content: item.content || item.message || '暂无内容',
  timeText: item.createTime || item.createdAt || item.sendTime || '刚刚'
})

const unreadCount = computed(() => notifications.value.filter((item) => !item.isRead).length)

const loadNotifications = async () => {
  loading.value = true
  try {
    const response = await notificationApi.getNotifications()
    notifications.value = response.code === 200 && Array.isArray(response.data)
      ? response.data.map(normalizeNotification)
      : []
  } catch (error) {
    notifications.value = []
  } finally {
    loading.value = false
  }
}

const markRead = async (item) => {
  if (!item?.id || item.isRead) return
  try {
    const response = await notificationApi.markAsRead(item.id)
    if (response.code !== 200) {
      throw new Error(response.message || '操作失败')
    }
    notifications.value = notifications.value.map((current) => current.id === item.id ? { ...current, isRead: true } : current)
    uni.showToast({ title: '已标记', icon: 'none' })
  } catch (error) {
    uni.showToast({ title: error.message || '操作失败', icon: 'none' })
  }
}

const deleteItem = async (item) => {
  if (!item?.id) return
  try {
    const response = await notificationApi.deleteNotification(item.id)
    if (response.code !== 200) {
      throw new Error(response.message || '删除失败')
    }
    notifications.value = notifications.value.filter((current) => current.id !== item.id)
    uni.showToast({ title: '已删除', icon: 'none' })
  } catch (error) {
    uni.showToast({ title: error.message || '删除失败', icon: 'none' })
  }
}

onShow(() => {
  loadNotifications()
})
</script>

<style scoped lang="scss">
.notifications-page {
  padding-top: 20rpx;
}

.hero-card {
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
  padding: 32rpx;
}

.hero-title {
  font-size: 40rpx;
  font-weight: 700;
}

.hero-desc {
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: #5b6159;
}

.hero-action {
  color: #486646;
  font-size: 24rpx;
}

.summary-card {
  margin-top: 22rpx;
  padding: 26rpx 28rpx;
}

.summary-label {
  display: block;
  font-size: 22rpx;
  color: #5b6159;
}

.summary-value {
  display: block;
  margin-top: 10rpx;
  font-size: 32rpx;
  font-weight: 700;
}

.list-stack {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  margin-top: 22rpx;
}

.notice-card {
  padding: 28rpx;
}

.notice-head {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
}

.notice-title {
  display: block;
  font-size: 28rpx;
  font-weight: 600;
  color: #2e342d;
}

.notice-time {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #7c8578;
}

.notice-state {
  flex-shrink: 0;
  color: #7c8578;
  font-size: 22rpx;
}

.notice-state.unread {
  color: #486646;
}

.notice-content {
  display: block;
  margin-top: 18rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: #5b6159;
}

.action-row {
  display: flex;
  gap: 16rpx;
  margin-top: 22rpx;
}

.small-btn {
  height: 78rpx;
  font-size: 24rpx;
}

.danger-btn {
  color: #9a4b4b;
}

.empty-card {
  margin-top: 22rpx;
  padding: 36rpx 28rpx;
  text-align: center;
  color: #7c8578;
  font-size: 24rpx;
}
</style>
