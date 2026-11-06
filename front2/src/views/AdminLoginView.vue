<script setup>
/* ============================================================
   AdminLoginView.vue · 后台独立登录
   ------------------------------------------------------------
   与用户端 /login 完全分开：
     · 只发放后台会话（sh_admin_session），不动用户端会话
     · 后端返回 role != admin 时拒绝登录
     · 普通用户想进 /admin 会被路由守卫送到这里，但用自己账号登不进来
   ============================================================ */
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authApi } from '@/services/api'
import { useAppStore } from '@/stores/app'
import { toast } from '@/composables/useToast'
import SvgIcon from '@/components/SvgIcon.vue'

const route = useRoute()
const router = useRouter()
const store = useAppStore()

/** 演示环境的管理员账号（database/seed_test.sql 里的 admin@qq.com） */
const DEMO_ADMIN_EMAIL = 'admin@qq.com'
const DEMO_ADMIN_PASSWORD = '123456'

const form = reactive({ email: DEMO_ADMIN_EMAIL, password: DEMO_ADMIN_PASSWORD })
const err = reactive({ email: false, password: false })
const busy = ref(false)

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

/** 登录后回跳：只接受后台地址，避免被 query 带到用户端页面 */
function redirectTarget() {
  const to = String(route.query.redirect || '')
  if (to.startsWith('/admin') && to !== '/admin/login') return to
  return '/admin'
}

async function onLogin() {
  err.email = false
  err.password = false
  const email = form.email.trim()
  if (!EMAIL_RE.test(email)) {
    err.email = true
    return
  }
  if (form.password.length < 6) {
    err.password = true
    return
  }

  busy.value = true
  const res = await authApi.login({ email, password: form.password })
  busy.value = false

  if (res.code !== 200) {
    // 不再放行「离线体验管理员」：没有后端就没有可信身份，直接如实报错
    toast(res.message || '登录失败，请稍后重试', 'error')
    return
  }
  if (!res.data || res.data.role !== 'admin') {
    toast('该账号不是管理员，无法进入后台', 'error')
    return
  }
  store.enterAdmin(res.data)
  toast('登录成功，正在进入运营后台')
  setTimeout(() => router.replace(redirectTarget()), 320)
}

/* 后台登录页复用登录页的整页背景 */
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
      <section class="auth-visual">
        <div class="auth-visual-inner">
          <div class="auth-brand">
            <span class="brand-mark">
              <SvgIcon name="leaf" :stroke-width="1.6" />
            </span>
            <span>
              <strong>膳衡</strong>
              <small>SHANHENG · 运营后台</small>
            </span>
          </div>

          <div class="auth-quote">
            <h2>用户、内容与数据，<br />都在同一套权限边界内。</h2>
            <p>
              后台使用独立登录与独立会话，不与用户端互通。账号、食谱、文章、食材的每一次变更都留在这里。
            </p>
            <div class="auth-tags mt-24">
              <span>会话隔离</span>
              <span>管理员角色校验</span>
              <span>内容与用户管理</span>
            </div>
          </div>

          <p class="small" style="color: #a9c3b4">仅限授权运营人员使用，操作会被记录。</p>
        </div>
      </section>

      <section class="auth-panel">
        <div class="auth-box">
          <p class="eyebrow">Admin console</p>
          <h1>运营后台</h1>
          <p class="sub">使用管理员账号登录，与用户端账号互不通用。</p>

          <form class="auth-form on" novalidate @submit.prevent="onLogin">
            <label class="field" :class="{ 'has-error': err.email }">
              <span class="field-label">管理员邮箱</span>
              <input
                v-model="form.email"
                class="input"
                type="email"
                placeholder="admin@example.com"
                autocomplete="username"
              />
              <span class="field-error">请输入有效的邮箱地址</span>
            </label>
            <label class="field" :class="{ 'has-error': err.password }">
              <span class="field-label">密码</span>
              <input
                v-model="form.password"
                class="input"
                type="password"
                placeholder="6–50 位"
                autocomplete="current-password"
              />
              <span class="field-error">密码至少 6 位</span>
            </label>

            <button class="btn btn-primary btn-block btn-lg" type="submit" :disabled="busy">
              <span v-if="busy" class="spinner" />
              <span>{{ busy ? '登录中' : '进入后台' }}</span>
            </button>

            <div class="auth-note">
              演示管理员：<b>admin@qq.com</b> / <b>123456</b>。<br />
              普通用户请使用用户端登录页，后台不接受用户账号。
            </div>
          </form>
        </div>
      </section>
    </div>
  </main>
</template>
