<template>
  <view class="page-shell auth-page safe-bottom">
    <view class="auth-content">
      <view class="auth-hero">
        <view class="auth-badge">新用户注册</view>
        <view class="auth-title">创建你的健康档案</view>
        <view class="auth-desc">先注册账号，再继续填写健康信息与饮食目标。</view>
      </view>

      <view class="card auth-card">
        <view class="auth-card__title">创建账号</view>

        <view class="auth-field">
          <text class="auth-label">用户名</text>
          <view class="input-card">
            <input v-model.trim="form.username" placeholder="请输入用户名" type="text" />
          </view>
        </view>

        <view class="auth-field">
          <text class="auth-label">邮箱</text>
          <view class="input-card">
            <input v-model.trim="form.email" placeholder="请输入邮箱地址" type="text" />
          </view>
        </view>

        <view class="auth-field">
          <text class="auth-label">手机号</text>
          <view class="input-card">
            <input v-model.trim="form.phone" maxlength="11" placeholder="请输入手机号" type="number" />
          </view>
        </view>

        <view class="auth-field">
          <text class="auth-label">密码</text>
          <view class="input-card">
            <input v-model="form.password" placeholder="请设置密码" password type="text" />
          </view>
        </view>

        <view class="auth-field">
          <text class="auth-label">确认密码</text>
          <view class="input-card">
            <input v-model="form.confirmPassword" placeholder="请再次输入密码" password type="text" />
          </view>
        </view>

        <button class="primary-button" :disabled="loading" @click="handleRegister">
          {{ loading ? '注册中...' : '注册并继续' }}
        </button>

        <view class="auth-footer">
          <text class="muted">已经有账号？</text>
          <text class="auth-link" @click="goLogin">立即登录</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import authApi from '@/api/auth'
import { useUserStore } from '@/store/user'
import { reactive, ref } from 'vue'

const userStore = useUserStore()
const loading = ref(false)
const form = reactive({
  username: '',
  email: '',
  phone: '',
  password: '',
  confirmPassword: ''
})

const handleRegister = async () => {
  if (!form.username) {
    uni.showToast({ title: '请输入用户名', icon: 'none' })
    return
  }
  if (!/^\S+@\S+\.\S+$/.test(form.email)) {
    uni.showToast({ title: '请输入正确邮箱', icon: 'none' })
    return
  }
  if (!/^1[3-9]\d{9}$/.test(form.phone)) {
    uni.showToast({ title: '请输入正确手机号', icon: 'none' })
    return
  }
  if (!form.password || form.password.length < 6) {
    uni.showToast({ title: '密码至少 6 位', icon: 'none' })
    return
  }
  if (form.password !== form.confirmPassword) {
    uni.showToast({ title: '两次密码不一致', icon: 'none' })
    return
  }

  loading.value = true
  try {
    const registerPayload = {
      username: form.username,
      email: form.email,
      phone: form.phone,
      password: form.password
    }

    const registerResponse = await authApi.register(registerPayload)
    if (registerResponse.code !== 200) {
      throw new Error(registerResponse.message || '注册失败')
    }

    let authData = registerResponse.data
    if (!authData?.token) {
      const loginResponse = await authApi.login({
        email: form.email,
        password: form.password
      })
      if (loginResponse.code !== 200 || !loginResponse.data?.token) {
        throw new Error(loginResponse.message || '自动登录失败')
      }
      authData = loginResponse.data
    }

    if (authData.role === 'admin') {
      throw new Error('管理端账号请使用 Web 端登录')
    }

    userStore.setUser({
      userId: authData.userId,
      username: authData.username,
      email: authData.email,
      phone: authData.phone,
      avatar: authData.avatar,
      role: authData.role,
      token: authData.token
    })
    userStore.saveRecentAccount({
      email: form.email,
      password: form.password,
      username: authData.username,
      role: authData.role
    })
    userStore.setHealthInfo(null)
    userStore.setHealthAnalysis(null)
    userStore.setDietGoal(null)
    userStore.setDietGoalMeta(null)

    uni.showToast({ title: '注册成功', icon: 'success' })
    uni.reLaunch({ url: '/pages/onboarding/health-basic' })
  } catch (error) {
    uni.showToast({ title: error.message || '注册失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const goLogin = () => {
  uni.navigateBack({
    fail: () => {
      uni.reLaunch({ url: '/pages/auth/login' })
    }
  })
}
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
  font-size: 50rpx;
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

.auth-footer {
  margin-top: 28rpx;
  display: flex;
  justify-content: center;
  gap: 12rpx;
}

.auth-link {
  color: #486646;
  font-size: 24rpx;
}
</style>
