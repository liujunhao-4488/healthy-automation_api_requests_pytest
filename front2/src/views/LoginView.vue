<script setup>
/* ============================================================
   LoginView.vue · 登录 / 注册
   ------------------------------------------------------------
   对应静态版 index.html。原来是两个 <form> + 一段 inline script，
   现在用一个 tab 状态控制显示哪一栏，校验错误用对象存。
   ============================================================ */
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '@/services/api'
import { useAppStore } from '@/stores/app'
import { toast } from '@/composables/useToast'
import SvgIcon from '@/components/SvgIcon.vue'
import heroFood from '@/assets/hero-food.jpg'

const router = useRouter()
const store = useAppStore()

/** 当前 tab：login | register */
const tab = ref('login')

/**
 * 后端种子测试账号（backend 数据库里的演示用户）。
 * 想用自己的账号，直接在输入框里改就行，这里只是预填。
 */
const DEMO_EMAIL = '2311697186@qq.com'
const DEMO_PASSWORD = '123456'

const loginForm = reactive({ email: DEMO_EMAIL, password: DEMO_PASSWORD, remember: true })
const registerForm = reactive({ username: '', email: '', phone: '', password: '' })

/** 每个字段是否报错；对应原来的 .field.has-error */
const loginErr = reactive({ email: false, password: false })
const regErr = reactive({ name: false, email: false, password: false })

const busy = ref(false)

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function resetErrors(obj) {
  Object.keys(obj).forEach((k) => (obj[k] = false))
}

/** 后端连不上时返回的 code（见 services/http.js） */
const OFFLINE_CODES = [-1, -2]

async function onLogin() {
  resetErrors(loginErr)
  const email = loginForm.email.trim()
  if (!EMAIL_RE.test(email)) {
    loginErr.email = true
    return
  }
  if (loginForm.password.length < 6) {
    loginErr.password = true
    return
  }
  busy.value = true
  // 真登录：POST /auth/login，成功返回 { token, userId, username, role, ... }
  const res = await authApi.login({ email, password: loginForm.password })
  busy.value = false
  if (res.code !== 200) {
    toast(res.message, 'error')
    return
  }
  store.enter(res.data)
  toast('登录成功，正在进入工作台')
  setTimeout(() => router.push('/'), 320)
}

async function onDemo() {
  // 优先走真实后端；只有「连不上」才退回本地假会话，保证任何情况下都能看界面
  loginForm.email = DEMO_EMAIL
  loginForm.password = DEMO_PASSWORD
  busy.value = true
  const res = await authApi.login({ email: DEMO_EMAIL, password: DEMO_PASSWORD })
  busy.value = false

  if (res.code === 200) {
    store.enter(res.data)
    toast('已用体验账号登录')
  } else if (OFFLINE_CODES.includes(res.code)) {
    store.login(DEMO_EMAIL, DEMO_PASSWORD)
    toast('后端未连接，已进入本地体验模式')
  } else {
    toast(res.message, 'error')
    return
  }
  setTimeout(() => router.push('/'), 320)
}

async function onRegister() {
  resetErrors(regErr)
  const username = registerForm.username.trim()
  const email = registerForm.email.trim()
  if (!username) {
    regErr.name = true
    return
  }
  if (!EMAIL_RE.test(email)) {
    regErr.email = true
    return
  }
  if (registerForm.password.length < 6 || registerForm.password.length > 50) {
    regErr.password = true
    return
  }
  busy.value = true
  // 后端注册成功后直接发 token，不用再登录一次
  const res = await authApi.register({
    username,
    email,
    phone: registerForm.phone.trim(),
    password: registerForm.password
  })
  busy.value = false
  if (res.code !== 200) {
    toast(res.message, 'error')
    return
  }
  store.enter(res.data)
  toast('注册成功，正在进入健康引导')
  setTimeout(() => router.push('/health'), 320)
}

function onForgot() {
  toast('演示环境暂未接入邮件服务，请使用体验账号登录')
}

/* 登录页有独立的页面背景（body[data-page="login"]），进出页面时挂载/清理 */
onMounted(() => {
  document.body.dataset.page = 'login'
})
onUnmounted(() => {
  delete document.body.dataset.page
})
</script>

<template>
  <main class="app-content">
    <div class="auth">
      <!-- 左侧品牌区 -->
      <section class="auth-visual">
        <img :src="heroFood" alt="新鲜食材平铺摄影" />
        <div class="auth-visual-inner">
          <div class="auth-brand">
            <span class="brand-mark">
              <SvgIcon name="leaf" :stroke-width="1.6" />
            </span>
            <span>
              <strong>膳衡</strong>
              <small>SHANHENG · 健康饮食</small>
            </span>
          </div>

          <div class="auth-quote">
            <h2>把「吃得健康」<br />变成每天可执行的三餐。</h2>
            <p>
              建立健康档案，设定饮食目标，记录每一餐，让 AI 结合权威食养指南给你可追溯的建议。
            </p>
            <div class="auth-tags mt-24">
              <span>AI 个性化推荐</span>
              <span>营养量化记录</span>
              <span>权威食养指南 RAG</span>
            </div>
          </div>

          <p class="small" style="color: #a9c3b4">
            本系统仅提供饮食与营养建议，不替代医疗诊断与医嘱。
          </p>
        </div>
      </section>

      <!-- 右侧表单区 -->
      <section class="auth-panel">
        <div class="auth-box">
          <p class="eyebrow">Welcome back</p>
          <h1>今天，好好吃饭</h1>
          <p class="sub">登录后继续记录你的饮食与目标进度。</p>

          <div class="auth-tabs">
            <button class="auth-tab" :class="{ on: tab === 'login' }" @click="tab = 'login'">
              登录
            </button>
            <button class="auth-tab" :class="{ on: tab === 'register' }" @click="tab = 'register'">
              注册
            </button>
          </div>

          <!-- 登录 -->
          <form
            class="auth-form"
            :class="{ on: tab === 'login' }"
            novalidate
            @submit.prevent="onLogin"
          >
            <label class="field" :class="{ 'has-error': loginErr.email }">
              <span class="field-label">邮箱</span>
              <input
                v-model="loginForm.email"
                class="input"
                type="email"
                placeholder="you@example.com"
                autocomplete="email"
              />
              <span class="field-error">请输入有效的邮箱地址</span>
            </label>
            <label class="field" :class="{ 'has-error': loginErr.password }">
              <span class="field-label">密码</span>
              <input
                v-model="loginForm.password"
                class="input"
                type="password"
                placeholder="6–50 位"
                autocomplete="current-password"
              />
              <span class="field-error">密码至少 6 位</span>
            </label>
            <div class="row-between">
              <label class="switch">
                <input v-model="loginForm.remember" type="checkbox" />
                <span class="track" />
                <span class="switch-text">记住我</span>
              </label>
              <button type="button" class="link-btn" @click="onForgot">忘记密码？</button>
            </div>
            <button
              class="btn btn-primary btn-block btn-lg"
              type="submit"
              :disabled="busy"
            >
              <span v-if="busy" class="spinner" />
              <span>{{ busy ? '登录中' : '登录' }}</span>
            </button>

            <div class="auth-divider">或</div>
            <button class="btn btn-outline btn-block" type="button" @click="onDemo">
              <SvgIcon name="play" /> 使用体验账号快速进入
            </button>

            <div class="auth-note">
              体验账号：<b>jiahe@example.com</b> / <b>123456</b>（管理员角色，可查看管理后台）。<br />
              演示用的所有数据均为本地假数据，不会上传。
            </div>
          </form>

          <!-- 注册 -->
          <form
            class="auth-form"
            :class="{ on: tab === 'register' }"
            novalidate
            @submit.prevent="onRegister"
          >
            <label class="field" :class="{ 'has-error': regErr.name }">
              <span class="field-label">用户名</span>
              <input v-model="registerForm.username" class="input" type="text" placeholder="2–20 个字符" />
              <span class="field-error">请输入用户名</span>
            </label>
            <label class="field" :class="{ 'has-error': regErr.email }">
              <span class="field-label">邮箱</span>
              <input v-model="registerForm.email" class="input" type="email" placeholder="you@example.com" />
              <span class="field-error">请输入有效的邮箱地址</span>
            </label>
            <label class="field">
              <span class="field-label">手机号</span>
              <input
                v-model="registerForm.phone"
                class="input"
                type="tel"
                placeholder="选填，用于接收饮食提醒"
              />
            </label>
            <label class="field" :class="{ 'has-error': regErr.password }">
              <span class="field-label">密码</span>
              <input v-model="registerForm.password" class="input" type="password" placeholder="6–50 位" />
              <span class="field-error">密码长度需在 6–50 位之间</span>
            </label>
            <button
              class="btn btn-primary btn-block btn-lg"
              type="submit"
              :disabled="busy"
            >
              <span v-if="busy" class="spinner" />
              <span>{{ busy ? '创建中' : '创建账号' }}</span>
            </button>
            <p class="small muted" style="text-align: center">
              注册即表示同意《用户协议》与《隐私政策》。
            </p>
          </form>
        </div>
      </section>
    </div>
  </main>
</template>
