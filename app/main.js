import { createSSRApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import { useUserStore } from './store/user'
import { setUnauthorizedHandler } from './utils/request'

export function createApp() {
  const app = createSSRApp(App)
  const pinia = createPinia()
  app.use(pinia)

  const userStore = useUserStore(pinia)
  setUnauthorizedHandler(() => {
    userStore.logout()
    const pages = getCurrentPages()
    const currentRoute = pages[pages.length - 1]?.route
    if (currentRoute !== 'pages/auth/login') {
      uni.reLaunch({ url: '/pages/auth/login' })
    }
  })

  return {
    app,
    pinia
  }
}
