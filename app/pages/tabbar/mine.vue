<template>
  <view class="page-shell safe-bottom">
    <view class="page-content mine-page">
      <view class="hero-card card">
        <view class="hero-main">
          <image
            v-if="avatarSrc"
            class="avatar avatar-image"
            :src="avatarSrc"
            mode="aspectFill"
            @error="handleAvatarError"
          />
          <view v-else class="avatar">{{ userInitial }}</view>
          <view>
            <view class="hero-title">{{ displayName }}</view>
            <view class="hero-desc">{{ displayEmail }}</view>
          </view>
        </view>
        <text class="hero-action" @click="loadData">刷新</text>
      </view>

      <view class="summary-grid">
        <view class="summary-card soft-card">
          <text class="summary-label">当前目标</text>
          <text class="summary-value">{{ goalLabel }}</text>
        </view>
        <view class="summary-card soft-card">
          <text class="summary-label">提醒数量</text>
          <text class="summary-value">{{ notificationCount }}</text>
        </view>
        <view class="summary-card soft-card">
          <text class="summary-label">AI 会话</text>
          <text class="summary-value">{{ conversationCount }}</text>
        </view>
      </view>

      <view class="section-block">
        <view class="section-title">
          <text class="section-title__text">个人概览</text>
        </view>
        <view class="card info-card">
          <view class="info-row">
            <text>用户名</text>
            <text>{{ profile.username || displayName }}</text>
          </view>
          <view class="info-row">
            <text>手机号</text>
            <text>{{ profile.phone || userStore.phone || '未填写' }}</text>
          </view>
          <view class="info-row clickable-row" @click="showPreferenceDetail = true">
            <text>饮食偏好</text>
            <view class="info-note-row">
              <text class="info-note">{{ preferenceSummary }}</text>
              <text class="row-arrow">›</text>
            </view>
          </view>
          <view class="info-row no-border">
            <text>健康状态</text>
            <text>{{ healthStatus }}</text>
          </view>
        </view>
      </view>

      <view class="section-block">
        <view class="section-title">
          <text class="section-title__text">常用功能</text>
        </view>
        <view class="menu-list">
          <view class="card menu-item" @click="openNotifications">
            <view>
              <text class="menu-title">消息中心</text>
              <text class="menu-desc">查看系统通知与饮食提醒</text>
            </view>
            <text class="menu-value">{{ notificationCount }}</text>
          </view>
          <view class="card menu-item" @click="openGoalSetup">
            <view>
              <text class="menu-title">饮食目标</text>
              <text class="menu-desc">调整目标体重、热量与提醒时间</text>
            </view>
            <text class="menu-value">编辑</text>
          </view>
          <view class="card menu-item" @click="openHealthProfile">
            <view>
              <text class="menu-title">健康档案</text>
              <text class="menu-desc">查看和修改身高体重、运动习惯与慢病信息</text>
            </view>
            <text class="menu-value">{{ healthStatus }}</text>
          </view>
          <view class="card menu-item" @click="switchTab('/pages/tabbar/recipes')">
            <view>
              <text class="menu-title">食谱收藏</text>
              <text class="menu-desc">前往食谱页查看已收藏与推荐内容</text>
            </view>
            <text class="menu-value">查看</text>
          </view>
          <view class="card menu-item" @click="openAssistant">
            <view>
              <text class="menu-title">AI 助手</text>
              <text class="menu-desc">继续查看会话记录与饮食问答</text>
            </view>
            <text class="menu-value">{{ conversationCount }}</text>
          </view>
        </view>
      </view>

      <button class="secondary-button logout-btn" @click="handleLogout">退出登录</button>

      <view v-if="showPreferenceDetail" class="sheet-mask" @click="showPreferenceDetail = false">
        <view class="preference-sheet" @click.stop>
          <view class="sheet-handle"></view>
          <view class="sheet-title">饮食偏好详情</view>

          <view class="preference-detail-list">
            <view class="preference-detail-item">
              <text class="detail-label">饮食类型</text>
              <text class="detail-value">{{ preferenceDetail.dietType || '未设置' }}</text>
            </view>
            <view class="preference-detail-item">
              <text class="detail-label">喜欢食材</text>
              <text class="detail-value">{{ preferenceDetail.favorites || '未设置' }}</text>
            </view>
            <view class="preference-detail-item">
              <text class="detail-label">忌口/过敏</text>
              <text class="detail-value">{{ preferenceDetail.allergies || '未设置' }}</text>
            </view>
            <view class="preference-detail-item">
              <text class="detail-label">不喜欢食材</text>
              <text class="detail-value">{{ preferenceDetail.dislikes || '未设置' }}</text>
            </view>
          </view>

          <button class="primary-button sheet-button" @click="showPreferenceDetail = false">知道了</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import assistantApi from '@/api/assistant'
import notificationApi from '@/api/notification'
import userApi from '@/api/user'
import { useUserStore } from '@/store/user'
import { BASE_URL } from '@/utils/request'
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

const userStore = useUserStore()
const profile = ref({})
const preference = ref({})
const notificationCount = ref(0)
const conversationCount = ref(0)
const avatarLoadFailed = ref(false)
const showPreferenceDetail = ref(false)

const goalLabelMap = {
  fat_loss: '减肥减脂',
  muscle_toning: '增肌塑形',
  weight_maintenance: '维持体重',
  healthy_weight_gain: '健康增重',
  blood_sugar_control: '控糖饮食',
  lipid_control: '控脂降脂',
  low_sodium: '控压低盐',
  pregnancy_nutrition: '孕妇营养',
  child_growth: '儿童成长',
  senior_wellness: '老年养生'
}

const displayName = computed(() => profile.value.username || userStore.username || '用户')
const displayEmail = computed(() => profile.value.email || userStore.email || '未绑定邮箱')
const userInitial = computed(() => (displayName.value || 'U').trim().slice(0, 1).toUpperCase())
const avatarSrc = computed(() => {
  if (avatarLoadFailed.value) {
    return ''
  }

  const rawAvatar = String(profile.value.avatar ?? userStore.avatar ?? '').trim()
  if (!rawAvatar) {
    return ''
  }

  if (/^(data:image\/|https?:\/\/|file:\/\/|blob:)/i.test(rawAvatar)) {
    return rawAvatar
  }

  if (rawAvatar.startsWith('//')) {
    return `https:${rawAvatar}`
  }

  const apiOrigin = BASE_URL.replace(/\/api\/?$/, '')
  const normalizedAvatar = rawAvatar.replace(/^\.?\//, '')

  if (rawAvatar.startsWith('/')) {
    return `${apiOrigin}${rawAvatar}`
  }

  return `${apiOrigin}/${normalizedAvatar}`
})
const goalLabel = computed(() => goalLabelMap[userStore.dietGoal?.goalType] || '未设置')

const splitPreferenceItems = (value) => String(value || '')
  .split(/[,，、;；\s]+/)
  .map((item) => item.trim())
  .filter(Boolean)

const preferenceDetail = computed(() => ({
  dietType: preference.value.dietType || '',
  favorites: preference.value.favorites || preference.value.preferredFoods || preference.value.preferredFood || '',
  allergies: preference.value.allergies || preference.value.avoidedFoods || preference.value.avoidedFood || '',
  dislikes: preference.value.dislikes || ''
}))

const preferenceSummary = computed(() => {
  const detail = preferenceDetail.value
  const summary = [
    detail.dietType,
    splitPreferenceItems(detail.favorites).length ? `偏好${splitPreferenceItems(detail.favorites).length}项` : '',
    splitPreferenceItems(detail.allergies).length ? `忌口${splitPreferenceItems(detail.allergies).length}项` : '',
    splitPreferenceItems(detail.dislikes).length ? `不喜欢${splitPreferenceItems(detail.dislikes).length}项` : ''
  ].filter(Boolean).join(' · ')
  return summary || '暂未设置偏好'
})

const healthStatus = computed(() => {
  if (!userStore.hasHealthInfo) return '未完善'
  if (!userStore.hasCompletedHealthProfile) return '待补充详细信息'
  return '已完善'
})

const loadData = async () => {
  try {
    const [profileResponse, preferenceResponse, notificationResponse, conversationResponse] = await Promise.all([
      userApi.getProfile(),
      userApi.getDietPreference(),
      notificationApi.getNotifications(),
      assistantApi.getConversations()
    ])

    if (profileResponse.code === 200 && profileResponse.data) {
      profile.value = profileResponse.data
      avatarLoadFailed.value = false
      userStore.updateProfile(profileResponse.data)
    } else {
      profile.value = {}
      avatarLoadFailed.value = false
    }

    preference.value = preferenceResponse.code === 200 && preferenceResponse.data ? preferenceResponse.data : {}

    const notifications = notificationResponse.code === 200 && Array.isArray(notificationResponse.data)
      ? notificationResponse.data
      : []
    notificationCount.value = notifications.filter((item) => !item.isRead).length

    const conversations = conversationResponse.code === 200 && Array.isArray(conversationResponse.data)
      ? conversationResponse.data
      : []
    conversationCount.value = conversations.length
  } catch (error) {
    profile.value = {}
    preference.value = {}
    notificationCount.value = 0
    conversationCount.value = 0
    avatarLoadFailed.value = false
  }
}

const handleAvatarError = () => {
  avatarLoadFailed.value = true
}

const switchTab = (url) => {
  uni.switchTab({ url })
}

const openNotifications = () => {
  uni.navigateTo({ url: '/pages/detail/notifications' })
}

const openGoalSetup = () => {
  uni.navigateTo({ url: '/pages/onboarding/diet-goal' })
}

const openHealthProfile = () => {
  uni.navigateTo({ url: '/pages/mine/health-profile' })
}

const openAssistant = () => {
  uni.navigateTo({ url: '/pages/assistant/chat' })
}

const handleLogout = () => {
  userStore.logout()
  uni.reLaunch({ url: '/pages/auth/login' })
}

onShow(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.mine-page {
  padding-top: 20rpx;
}

.hero-card {
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
  padding: 32rpx;
  align-items: flex-start;
}

.hero-main {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(72, 102, 70, 0.12);
  color: #486646;
  font-size: 36rpx;
  font-weight: 700;
}

.avatar-image {
  overflow: hidden;
}

.hero-title {
  font-size: 38rpx;
  font-weight: 700;
}

.hero-desc,
.hero-action {
  font-size: 24rpx;
  color: #5b6159;
}

.hero-desc {
  margin-top: 10rpx;
}

.hero-action {
  color: #486646;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18rpx;
  margin-top: 22rpx;
}

.summary-card {
  padding: 24rpx;
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
  color: #2e342d;
}

.section-block {
  margin-top: 28rpx;
}

.info-card {
  padding: 0 28rpx;
}

.info-row {
  display: flex;
  justify-content: space-between;
  gap: 24rpx;
  padding: 24rpx 0;
  border-bottom: 1rpx solid #edf1e8;
  font-size: 24rpx;
  color: #2e342d;
}

.info-row.no-border {
  border-bottom: none;
}

.clickable-row {
  align-items: center;
}

.info-note {
  text-align: right;
  color: #5b6159;
}

.info-note-row {
  flex: 1;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10rpx;
  min-width: 0;
}

.info-note-row .info-note {
  max-width: 410rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.row-arrow {
  color: #8a9486;
  font-size: 34rpx;
  line-height: 1;
}

.menu-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
  padding: 28rpx;
}

.menu-title {
  display: block;
  font-size: 28rpx;
  font-weight: 600;
  color: #2e342d;
}

.menu-desc {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  line-height: 1.6;
  color: #5b6159;
}

.menu-value {
  flex-shrink: 0;
  color: #486646;
  font-size: 24rpx;
}

.logout-btn {
  margin-top: 32rpx;
}

.sheet-mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: 50;
  display: flex;
  align-items: flex-end;
  background: rgba(22, 31, 21, 0.38);
}

.preference-sheet {
  width: 100%;
  padding: 18rpx 32rpx calc(env(safe-area-inset-bottom) + 32rpx);
  border-radius: 36rpx 36rpx 0 0;
  background: #fff;
  box-shadow: 0 -18rpx 48rpx rgba(46, 52, 45, 0.16);
}

.sheet-handle {
  width: 72rpx;
  height: 8rpx;
  margin: 0 auto 24rpx;
  border-radius: 999rpx;
  background: #dfe7dc;
}

.sheet-title {
  font-size: 34rpx;
  font-weight: 700;
  color: #2e342d;
}

.preference-detail-list {
  margin-top: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.preference-detail-item {
  padding: 22rpx 24rpx;
  border: 1rpx solid #e3ebdf;
  border-radius: 24rpx;
  background: #f7faf4;
}

.detail-label {
  display: block;
  color: #6d7768;
  font-size: 22rpx;
}

.detail-value {
  display: block;
  margin-top: 8rpx;
  color: #2e342d;
  font-size: 27rpx;
  line-height: 1.6;
}

.sheet-button {
  margin-top: 28rpx;
}
</style>
