<template>
  <div class="auth-page">
    <div class="auth-card">
      <!-- 左：品牌说明区 -->
      <section class="auth-brand">
        <div class="auth-brand__badge">
          <svg width="30" height="30" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
              d="M12 3c4.2 1.7 6.5 4.9 6.5 8.8 0 3.9-2.9 6.7-6.5 8.2-3.6-1.5-6.5-4.3-6.5-8.2C5.5 7.9 7.8 4.7 12 3z"
              fill="#ffffff"
              fill-opacity="0.92"
            />
            <path d="M12 6.8v9.6" stroke="#668a72" stroke-width="1.5" stroke-linecap="round" />
            <path
              d="M12 11.2c1.6-.4 2.7-1.3 3.2-2.6M12 14.2c-1.5-.4-2.6-1.3-3.1-2.6"
              stroke="#668a72"
              stroke-width="1.5"
              stroke-linecap="round"
            />
          </svg>
        </div>

        <div>
          <span class="auth-brand__eyebrow">Health Diet System</span>
          <h1 class="auth-brand__title">基于人工智能的<br />个人饮食健康管理系统</h1>
          <p class="auth-brand__desc">
            融合健康档案、饮食目标与智能推荐能力，为每位用户生成可执行的个性化饮食方案。
          </p>
        </div>

        <ul class="auth-brand__points">
          <li class="auth-brand__point">个性化食谱推荐</li>
          <li class="auth-brand__point">健康目标管理</li>
          <li class="auth-brand__point">饮食记录与分析</li>
        </ul>
      </section>

      <!-- 右：登录表单区 -->
      <section class="auth-panel">
        <h2 class="auth-panel__title">欢迎回来</h2>
        <p class="auth-panel__desc">登录后继续管理你的健康饮食计划</p>

        <div class="auth-tabs">
          <button type="button" class="auth-tab is-active">账号登录</button>
        </div>

        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="rules"
          label-position="top"
          class="auth-form"
        >
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="loginForm.email" placeholder="请输入邮箱地址">
              <template v-if="recentAccounts.length" #suffix>
                <el-popover
                  placement="bottom-end"
                  :width="340"
                  trigger="click"
                  popper-class="recent-account-popper"
                >
                  <template #reference>
                    <button type="button" class="auth-recent-trigger" aria-label="最近登录账号">
                      ⌄
                    </button>
                  </template>

                  <div class="auth-recent">
                    <div class="auth-recent-head">
                      <strong>最近登录</strong>
                      <span>最多保留 5 个账号</span>
                    </div>

                    <div class="auth-recent-list">
                      <div
                        v-for="account in recentAccounts"
                        :key="account.email"
                        class="auth-recent-item"
                      >
                        <div class="auth-recent-item__main" @click="quickLogin(account)">
                          <div class="auth-recent-item__badge">{{ getAccountInitial(account) }}</div>
                          <div class="auth-recent-item__meta">
                            <strong>{{ account.username || account.email }}</strong>
                            <span>{{ account.email }}</span>
                            <em>上次登录：{{ formatRecentTime(account.lastLoginAt) }}</em>
                          </div>
                        </div>

                        <button
                          type="button"
                          class="auth-recent-item__remove"
                          :disabled="loading"
                          @click.stop="removeRecent(account.email)"
                        >
                          ×
                        </button>
                      </div>
                    </div>
                  </div>
                </el-popover>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              show-password
              placeholder="请输入密码"
            />
          </el-form-item>

          <el-form-item>
            <el-button class="auth-submit" @click="login" :loading="loading">登录</el-button>
          </el-form-item>

          <div class="auth-form__actions">
            <el-button text @click="resetForm">重置</el-button>
          </div>
        </el-form>

        <div class="auth-footer">
          <span>还没有账号？</span>
          <el-link @click="goToRegister">立即注册</el-link>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import authApi from '../api/auth'
import healthInfoApi from '../api/healthInfo'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()
const loginFormRef = ref(null)
const loading = ref(false)
const recentAccounts = ref(userStore.getRecentAccounts())

const loginForm = reactive({
  email: '',
  password: ''
})

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const refreshRecentAccounts = () => {
  recentAccounts.value = userStore.getRecentAccounts()
}

const redirectWithFallback = async (target) => {
  try {
    await router.replace(target)
  } catch (error) {
    console.error('route redirect failed:', error)
  }

  if (router.currentRoute.value.path !== target) {
    window.location.href = target
  }
}

const navigateAfterLogin = async (role = userStore.role) => {
  ElMessage.success('登录成功')

  if (role === 'admin') {
    await redirectWithFallback('/admin/overview')
    return
  }

  if (userStore.hasCompletedHealthProfile) {
    await redirectWithFallback('/dashboard/health-info')
    return
  }

  await redirectWithFallback('/health-info-basic')
}

const fetchHealthInfo = async () => {
  try {
    const healthResponse = await healthInfoApi.getHealthInfo()
    if (healthResponse.code === 200 && healthResponse.data) {
      userStore.setHealthInfo(healthResponse.data)
      userStore.setHealthAnalysis(healthResponse.analysis || null)
    } else {
      userStore.setHealthInfo(null)
      userStore.setHealthAnalysis(null)
    }
  } catch (error) {
    userStore.setHealthInfo(null)
    userStore.setHealthAnalysis(null)
  }
}

const submitLogin = async ({ email, password }) => {
  loading.value = true

  try {
    const response = await authApi.login({ email, password })

    if (response.code !== 200) {
      ElMessage.error(response.message || '登录失败')
      return
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
    refreshRecentAccounts()

    if (response.data.role === 'admin') {
      await navigateAfterLogin(response.data.role)
      return
    }

    await fetchHealthInfo()
    await navigateAfterLogin(response.data.role)
  } catch (error) {
    ElMessage.error(error?.message || '登录失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

const login = () => {
  loginFormRef.value.validate((valid) => {
    if (valid) {
      submitLogin({
        email: loginForm.email,
        password: loginForm.password
      })
    }
  })
}

const quickLogin = (account) => {
  loginForm.email = account.email
  loginForm.password = account.password
  submitLogin({
    email: account.email,
    password: account.password
  })
}

const removeRecent = (email) => {
  userStore.removeRecentAccount(email)
  refreshRecentAccounts()
  ElMessage.success('已移除历史账号')
}

const resetForm = () => {
  loginFormRef.value?.resetFields()
}

const goToRegister = () => {
  router.push('/register')
}

const getAccountInitial = (account) => {
  const source = account.username || account.email || '?'
  return source.trim().charAt(0).toUpperCase()
}

const formatRecentTime = (value) => {
  if (!value) return '未知'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '未知'

  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(async () => {
  if (!userStore.isLoggedIn) {
    return
  }

  await navigateAfterLogin(userStore.role)
})
</script>

<!-- 样式见 src/styles/auth.css（登录/注册共用一份，不再各写一遍） -->
