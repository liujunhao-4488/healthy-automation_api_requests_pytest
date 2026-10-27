import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// 全局设计系统：静态版的 styles.css 原样搬过来
import './styles/base.css'

createApp(App).use(createPinia()).use(router).mount('#app')
