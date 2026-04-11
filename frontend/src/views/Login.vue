<template>
  <div class="login-page">
    <div class="login-shell">
      <section class="login-brand">
        <div class="brand-icon">
          <div class="brand-icon-inner">
            <span class="brand-monitor"></span>
          </div>
        </div>

        <div class="brand-copy">
          <h1>基于人工智能的个人饮食健康管理系统</h1>
          <p>基于健康档案、饮食目标和智能推荐能力打造的一体化健康饮食平台。</p>
        </div>

        <ul class="brand-points">
          <li>个性化食谱推荐</li>
          <li>健康目标管理</li>
          <li>饮食记录与分析</li>
        </ul>
      </section>

      <section class="login-panel">
        <div class="panel-head">
          <h2>欢迎登录</h2>
          <p>请输入您的账号信息</p>
        </div>

        <div class="login-tabs">
          <button type="button" class="tab-item active">账号登录</button>
        </div>

        <el-form ref="loginFormRef" :model="loginForm" :rules="rules" label-position="top" class="login-form">
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="loginForm.email" placeholder="请输入邮箱地址" class="login-input">
              <template v-if="recentAccounts.length" #suffix>
                <el-popover
                  placement="bottom-end"
                  :width="340"
                  trigger="click"
                  popper-class="recent-account-popper"
                >
                  <template #reference>
                    <button type="button" class="recent-trigger" aria-label="最近登录账号">
                      <span class="recent-trigger-icon">⌄</span>
                    </button>
                  </template>

                  <div class="recent-dropdown">
                    <div class="recent-dropdown-head">
                      <strong>最近登录</strong>
                      <span>最多保留 5 个账号</span>
                    </div>

                    <div class="recent-dropdown-list">
                      <div
                        v-for="account in recentAccounts"
                        :key="account.email"
                        class="recent-dropdown-item"
                      >
                        <div class="recent-item-main" @click="quickLogin(account)">
                          <div class="recent-badge">{{ getAccountInitial(account) }}</div>
                          <div class="recent-meta">
                            <strong>{{ account.username || account.email }}</strong>
                            <span>{{ account.email }}</span>
                            <em>上次登录：{{ formatRecentTime(account.lastLoginAt) }}</em>
                          </div>
                        </div>

                        <button
                          type="button"
                          class="recent-remove"
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
              class="login-input"
            />
          </el-form-item>

          <el-form-item class="login-submit">
            <el-button class="submit-button" @click="login" :loading="loading">登录</el-button>
          </el-form-item>

          <div class="form-footer">
            <el-button text @click="resetForm" class="reset-link">重置</el-button>
          </div>
        </el-form>

        <div class="auth-footer">
          <span>还没有账号？</span>
          <el-link class="register-link" @click="goToRegister">立即注册</el-link>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
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

const navigateAfterLogin = () => {
  ElMessage.success('登录成功')

  if (userStore.isAdmin) {
    router.push('/admin/overview')
    return
  }

  if (userStore.hasCompletedHealthProfile) {
    router.push('/dashboard/health-info')
    return
  }

  router.push('/health-info-basic')
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

    await fetchHealthInfo()
    navigateAfterLogin()
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
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
  background:
    radial-gradient(circle at top left, rgba(123, 160, 136, 0.18), transparent 28%),
    linear-gradient(180deg, #f4f8f6 0%, #edf3ef 100%);
}

.login-shell {
  width: min(1180px, 100%);
  min-height: 720px;
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  background: #ffffff;
  border-radius: 32px;
  overflow: hidden;
  box-shadow: 0 28px 80px rgba(77, 104, 88, 0.14);
  border: 1px solid rgba(221, 232, 227, 0.9);
}

.login-brand {
  position: relative;
  padding: 72px 60px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 28px;
  background:
    radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.12), transparent 16%),
    linear-gradient(180deg, #6f9580 0%, #86ab95 100%);
  color: #fff;
}

.brand-icon {
  display: flex;
  justify-content: center;
}

.brand-icon-inner {
  width: 132px;
  height: 132px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.14);
  backdrop-filter: blur(4px);
}

.brand-monitor {
  width: 54px;
  height: 40px;
  border: 4px solid #fff;
  border-radius: 8px;
  position: relative;
  display: block;
}

.brand-monitor::before {
  content: '';
  position: absolute;
  bottom: -16px;
  left: 50%;
  width: 22px;
  height: 4px;
  background: #fff;
  transform: translateX(-50%);
  border-radius: 999px;
}

.brand-monitor::after {
  content: '';
  position: absolute;
  bottom: -10px;
  left: 50%;
  width: 4px;
  height: 12px;
  background: #fff;
  transform: translateX(-50%);
  border-radius: 999px;
}

.brand-copy {
  text-align: center;
}

.brand-copy h1 {
  margin: 0 0 14px;
  font-size: 44px;
  line-height: 1.2;
  font-weight: 700;
  letter-spacing: 1px;
}

.brand-copy p {
  margin: 0;
  font-size: 18px;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.88);
}

.brand-points {
  list-style: none;
  margin: 8px auto 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: fit-content;
  color: rgba(255, 255, 255, 0.92);
  font-size: 18px;
}

.brand-points li {
  position: relative;
  padding-left: 28px;
}

.brand-points li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 10px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.85);
}

.login-panel {
  padding: 78px 54px 52px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.panel-head h2 {
  margin: 0;
  font-size: 46px;
  line-height: 1.15;
  color: #1d3b2f;
  font-weight: 700;
}

.panel-head p {
  margin: 14px 0 0;
  color: #7d9082;
  font-size: 18px;
}

.login-tabs {
  display: flex;
  gap: 32px;
  margin-top: 40px;
  padding-bottom: 14px;
  border-bottom: 1px solid #dde5ef;
}

.tab-item {
  border: none;
  background: transparent;
  padding: 0 0 12px;
  font-size: 20px;
  color: #6b7f71;
  cursor: pointer;
}

.tab-item.active {
  color: #7ba088;
  font-weight: 600;
  border-bottom: 3px solid #7ba088;
}

.tab-item.disabled {
  opacity: 0.62;
  cursor: default;
}

.login-form {
  margin-top: 28px;
}

.login-form :deep(.el-form-item__label) {
  font-size: 15px;
  color: #5d7163;
  padding-bottom: 8px;
}

.login-input :deep(.el-input__wrapper) {
  min-height: 54px;
  border-radius: 14px;
  box-shadow: none;
  background: #fff;
  border: 1px solid #d8e2ef;
  padding: 0 16px;
}

.login-input :deep(.el-input__wrapper:hover) {
  border-color: #bdd1c3;
}

.login-input :deep(.el-input__wrapper.is-focus) {
  border-color: #7ba088;
  box-shadow: 0 0 0 3px rgba(123, 160, 136, 0.14);
}

.login-input :deep(.el-input__inner) {
  font-size: 16px;
  color: #2d4335;
}

.login-submit {
  margin-top: 12px;
}

.submit-button {
  width: 100%;
  height: 54px;
  border: none;
  border-radius: 14px;
  background: linear-gradient(180deg, #7ba088 0%, #6b9078 100%);
  color: #fff;
  font-size: 18px;
  font-weight: 600;
}

.submit-button:hover {
  background: linear-gradient(180deg, #739982 0%, #62866f 100%);
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 2px;
}

.reset-link {
  color: #7d9082;
  font-size: 14px;
}

.auth-footer {
  margin-top: 36px;
  text-align: center;
  color: #839587;
  font-size: 15px;
}

.register-link {
  margin-left: 6px;
  color: #7ba088;
  font-size: 15px;
  font-weight: 600;
}

.recent-trigger {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: #7b9280;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 0;
}

.recent-trigger:hover {
  color: #6d9079;
}

.recent-trigger-icon {
  font-size: 16px;
  line-height: 1;
}

.recent-dropdown {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recent-dropdown-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.recent-dropdown-head strong {
  color: #344c3b;
  font-size: 14px;
}

.recent-dropdown-head span {
  color: #8aa08f;
  font-size: 12px;
}

.recent-dropdown-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.recent-dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid #dce7df;
  border-radius: 14px;
  background: linear-gradient(180deg, #fbfdfb 0%, #f4f8f5 100%);
  padding: 10px 12px;
}

.recent-item-main {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.recent-badge {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #7ba088 0%, #92b39d 100%);
  color: #fff;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}

.recent-meta {
  min-width: 0;
}

.recent-meta strong {
  display: block;
  color: #344c3b;
  font-size: 14px;
}

.recent-meta span,
.recent-meta em {
  display: block;
  color: #7d9082;
  font-size: 12px;
  font-style: normal;
  line-height: 1.5;
}

.recent-remove {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 50%;
  background: #edf4ef;
  color: #7d9082;
  cursor: pointer;
  flex-shrink: 0;
}

.recent-remove:hover {
  background: #e4ede7;
  color: #5e7264;
}

@media (max-width: 980px) {
  .login-shell {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .login-brand {
    padding: 48px 30px;
  }

  .login-panel {
    padding: 44px 28px 36px;
  }

  .brand-copy h1 {
    font-size: 36px;
  }

  .panel-head h2 {
    font-size: 38px;
  }
}

@media (max-width: 640px) {
  .login-page {
    padding: 14px;
  }

  .login-shell {
    border-radius: 22px;
  }

  .login-brand {
    padding: 38px 22px;
  }

  .login-panel {
    padding: 34px 20px 28px;
  }

  .brand-copy h1 {
    font-size: 30px;
  }

  .brand-copy p,
  .brand-points {
    font-size: 15px;
  }

  .panel-head h2 {
    font-size: 32px;
  }

  .panel-head p {
    font-size: 15px;
  }

  .login-tabs {
    gap: 20px;
  }

  .tab-item {
    font-size: 17px;
  }
}
</style>
