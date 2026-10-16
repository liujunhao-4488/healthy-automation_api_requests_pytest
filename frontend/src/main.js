import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

// 顺序很重要：先加载 Element Plus 原始样式，再加载我们自己的基础层，
// 这样 base.css 里对 Element 变量的覆盖才能生效（后写的优先级更高）。
import 'element-plus/dist/index.css'
import './styles/base.css'
import './styles/admin.css'
import './styles/auth.css'

import 'dayjs/locale/zh-cn'
import router from './router'
import App from './App.vue'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus, {
  locale: zhCn
})
app.mount('#app')
