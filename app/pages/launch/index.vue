<template>
  <view class="page-shell launch-page">
    <view class="launch-card card">
      <view class="launch-mark">有机呼吸</view>
      <view class="launch-title">正在进入健康饮食助手</view>
      <view class="launch-desc">根据你的登录状态与健康档案，为你恢复到合适的页面。</view>
      <view class="launch-loading">
        <view class="launch-dot" />
        <view class="launch-dot" />
        <view class="launch-dot" />
      </view>
    </view>
  </view>
</template>

<script setup>
import { useUserStore } from '@/store/user'
import { onShow } from '@dcloudio/uni-app'

const userStore = useUserStore()

const goNext = () => {
  if (!userStore.isLoggedIn) {
    uni.reLaunch({ url: '/pages/auth/login' })
    return
  }

  if (userStore.role === 'admin') {
    userStore.logout()
    uni.showToast({ title: '管理端请使用 Web 登录', icon: 'none' })
    uni.reLaunch({ url: '/pages/auth/login' })
    return
  }

  if (!userStore.hasHealthInfo) {
    uni.reLaunch({ url: '/pages/onboarding/health-basic' })
    return
  }

  if (!userStore.hasCompletedHealthProfile) {
    uni.reLaunch({ url: '/pages/onboarding/health-detail' })
    return
  }

  if (!userStore.hasDietGoal) {
    uni.reLaunch({ url: '/pages/onboarding/diet-goal' })
    return
  }

  uni.switchTab({ url: '/pages/tabbar/home' })
}

onShow(() => {
  setTimeout(goNext, 120)
})
</script>

<style scoped lang="scss">
.launch-page {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32rpx;
}

.launch-card {
  width: 100%;
  padding: 72rpx 56rpx;
  text-align: center;
}

.launch-mark {
  display: inline-flex;
  padding: 12rpx 28rpx;
  border-radius: 999rpx;
  background: rgba(72, 102, 70, 0.12);
  color: #486646;
  font-size: 24rpx;
  margin-bottom: 28rpx;
}

.launch-title {
  font-size: 42rpx;
  font-weight: 700;
  color: #2e342d;
}

.launch-desc {
  margin-top: 20rpx;
  font-size: 28rpx;
  line-height: 1.7;
  color: #5b6159;
}

.launch-loading {
  margin-top: 44rpx;
  display: flex;
  justify-content: center;
  gap: 16rpx;
}

.launch-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: #486646;
  opacity: 0.3;
  animation: pulse 1.2s infinite ease-in-out;
}

.launch-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.launch-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes pulse {
  0%,
  100% {
    transform: translateY(0);
    opacity: 0.3;
  }

  50% {
    transform: translateY(-8rpx);
    opacity: 1;
  }
}
</style>
