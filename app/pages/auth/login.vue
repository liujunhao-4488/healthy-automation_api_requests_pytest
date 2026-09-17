<template>
  <view class="page-shell auth-page safe-bottom">
    <view class="auth-content">
      <view class="auth-hero">
        <view class="auth-badge">智能饮食管理</view>
        <view class="auth-title">欢迎回来</view>
        <view class="auth-desc">登录后可继续查看健康档案、饮食目标与个性化推荐。</view>
      </view>

      <view class="card auth-card">
        <view class="auth-card__title">账号登录</view>

        <view class="auth-field">
          <text class="auth-label">邮箱</text>
          <view class="input-card">
            <input v-model.trim="form.email" placeholder="请输入邮箱地址" type="text" />
          </view>
        </view>

        <view class="auth-field">
          <text class="auth-label">密码</text>
          <view class="input-card">
            <input v-model="form.password" placeholder="请输入密码" password type="text" />
          </view>
        </view>

        <button class="primary-button" :disabled="loading" @click="handleLogin">
          {{ loading ? '登录中...' : '登录' }}
        </button>

        <view v-if="recentAccounts.length" class="recent-block">
          <view class="recent-title">最近登录</view>
          <view class="recent-list">
            <view v-for="account in recentAccounts" :key="account.email" class="recent-item">
              <view class="recent-main" @click="quickLogin(account)">
                <view class="recent-avatar">{{ getInitial(account) }}</view>
                <view class="recent-copy">
                  <text class="recent-name">{{ account.username || account.email }}</text>
                  <text class="recent-email">{{ account.email }}</text>
                </view>
              </view>
              <text class="recent-remove" @click.stop="removeRecent(account.email)">移除</text>
            </view>
          </view>
        </view>

        <view class="auth-footer">
          <text class="muted">还没有账号？</text>
          <text class="auth-link" @click="goRegister">立即注册</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import authApi from '@/api/auth'
import dietGoalApi from '@/api/dietGoal'
import healthInfoApi from '@/api/healthInfo'
import { useUserStore } from '@/store/user'
import { computed, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

const userStore = useUserStore()
const loading = ref(false)
const form = reactive({
  email: '',
  password: ''
})

const recentAccounts = computed(() => userStore.recentAccounts || [])

const routeAfterLogin = () => {
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

const syncUserAssets = async () => {
  try {
    const [healthResponse, goalResponse] = await Promise.all([
      healthInfoApi.getHealthInfo(),
      dietGoalApi.getDietGoal()
    ])

    if (healthResponse.code === 200 && healthResponse.data) {
      userStore.setHealthInfo(healthResponse.data)
      userStore.setHealthAnalysis(healthResponse.analysis || null)
    } else {
      userStore.setHealthInfo(null)
      userStore.setHealthAnalysis(null)
    }

    if (goalResponse.code === 200 && goalResponse.data) {
      userStore.setDietGoal(goalResponse.data)
      userStore.setDietGoalMeta(goalResponse.meta || null)
    } else {
      userStore.setDietGoal(null)
      userStore.setDietGoalMeta(null)
    }
  } catch (error) {
    userStore.setHealthInfo(null)
    userStore.setHealthAnalysis(null)
    userStore.setDietGoal(null)
    userStore.setDietGoalMeta(null)
  }
}

const submitLogin = async (email, password) => {
  loading.value = true
  try {
    const response = await authApi.login({ email, password })
    if (response.code !== 200 || !response.data?.token) {
      throw new Error(response.message || '登录失败')
    }

    if (response.data.role === 'admin') {
      throw new Error('管理端账号请使用 Web 端登录')
    }

    userStore.setUser({
      userId: response.data.userId,
      username: response.data.username,
      email: response.data.email,
      phone: response.data.phone,
      avatar: response.data.avatar,
      role: response.data.role,
      token: response.data.token
    })

    userStore.saveRecentAccount({
      email,
      password,
      username: response.data.username,
      role: response.data.role
    })

    await syncUserAssets()
    uni.showToast({ title: '登录成功', icon: 'success' })
    routeAfterLogin()
  } catch (error) {
    uni.showToast({ title: error.message || '登录失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const handleLogin = () => {
  if (!form.email) {
    uni.showToast({ title: '请输入邮箱', icon: 'none' })
    return
  }
  if (!/^\S+@\S+\.\S+$/.test(form.email)) {
    uni.showToast({ title: '邮箱格式不正确', icon: 'none' })
    return
  }
  if (!form.password) {
    uni.showToast({ title: '请输入密码', icon: 'none' })
    return
  }

  submitLogin(form.email, form.password)
}

const quickLogin = (account) => {
  form.email = account.email || ''
  form.password = account.password || ''
  if (form.email && form.password) {
    submitLogin(form.email, form.password)
  }
}

const removeRecent = (email) => {
  userStore.removeRecentAccount(email)
  uni.showToast({ title: '已移除', icon: 'none' })
}

const getInitial = (account) => {
  const source = account.username || account.email || 'U'
  return source.trim().slice(0, 1).toUpperCase()
}

const goRegister = () => {
  uni.navigateTo({ url: '/pages/auth/register' })
}

onShow(() => {
  if (userStore.isLoggedIn && userStore.role !== 'admin') {
    routeAfterLogin()
  }
})
</script>

<style scoped lang="scss">
.auth-page {
  padding: 32rpx;
}

.auth-content {
  padding: 24rpx 0 40rpx;
}

.auth-hero {
  padding: 24rpx 8rpx 36rpx;
}

.auth-badge {
  display: inline-flex;
  padding: 12rpx 24rpx;
  border-radius: 999rpx;
  background: rgba(72, 102, 70, 0.12);
  color: #486646;
  font-size: 22rpx;
}

.auth-title {
  margin-top: 28rpx;
  font-size: 54rpx;
  font-weight: 700;
  color: #2e342d;
}

.auth-desc {
  margin-top: 18rpx;
  font-size: 28rpx;
  line-height: 1.7;
  color: #5b6159;
}

.auth-card {
  padding: 40rpx 32rpx;
}

.auth-card__title {
  font-size: 36rpx;
  font-weight: 700;
  margin-bottom: 28rpx;
}

.auth-field {
  margin-bottom: 24rpx;
}

.auth-label {
  display: block;
  margin-bottom: 12rpx;
  font-size: 24rpx;
  color: #5b6159;
}

.recent-block {
  margin-top: 28rpx;
  padding-top: 28rpx;
}

.recent-title {
  margin-bottom: 16rpx;
  font-size: 24rpx;
  color: #5b6159;
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.recent-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 22rpx;
  border-radius: 24rpx;
  background: #f2f5ed;
}

.recent-main {
  display: flex;
  align-items: center;
  gap: 18rpx;
  flex: 1;
}

.recent-avatar {
  width: 68rpx;
  height: 68rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #486646;
  color: #fff;
  font-size: 28rpx;
  font-weight: 600;
}

.recent-copy {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.recent-name {
  font-size: 26rpx;
  color: #2e342d;
}

.recent-email {
  font-size: 22rpx;
  color: #7b8379;
}

.recent-remove,
.auth-link {
  color: #486646;
  font-size: 24rpx;
}

.auth-footer {
  margin-top: 28rpx;
  display: flex;
  justify-content: center;
  gap: 12rpx;
}
</style>
