<script setup>
/* ============================================================
   AccountView.vue · 个人中心
   ------------------------------------------------------------
   对应静态版 pages/account.html，一个页面 5 个 tab：
     账号资料 / 饮食偏好 / 我的收藏 / 阅读历史 / 通知中心

   原版用 .tab.on + .tab-panel.on 切显隐，这里用一个 tab 状态控制，
   通知的「标记已读 / 删除」直接改 store，侧边栏未读角标会自动跟着变。
   ============================================================ */
import { ref, reactive, computed, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import DB from '@/mock/db'
import { recipesApi } from '@/services/api'
import { toast } from '@/composables/useToast'
import { confirmDialog } from '@/composables/useConfirm'
import SvgIcon from '@/components/SvgIcon.vue'

const store = useAppStore()
const router = useRouter()

/* ---------------- tab ---------------- */
const tab = ref('profile')
const tabs = [
  { key: 'profile', label: '账号资料' },
  { key: 'prefs', label: '饮食偏好' },
  { key: 'favs', label: '我的收藏' },
  { key: 'history', label: '阅读历史' },
  { key: 'notifs', label: '通知中心' }
]

/* ---------------- 顶部资料 ---------------- */
const profile = reactive({
  username: store.session?.username || '林嘉禾',
  email: store.session?.email || DB.user.email,
  phone: ''
})
const gender = ref('女')

const roleText = computed(() => (store.isAdmin ? '管理员' : '普通用户'))

const stats = computed(() => ({
  recipes: store.recipeCollectIds.length,
  articles: store.articleCollectIds.length,
  records: store.recordList.length,
  streak: '5 天'
}))

/* ---------------- 资料保存 ---------------- */
function saveProfile() {
  const n = profile.username.trim()
  const em = profile.email.trim()
  if (n.length < 2) {
    toast('用户名至少 2 个字符', 'error')
    return
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(em)) {
    toast('邮箱格式不正确', 'error')
    return
  }
  store.updateProfile({ username: n, email: em, phone: profile.phone.trim() })
  toast('资料已更新')
}

function editProfile() {
  tab.value = 'profile'
  setTimeout(() => document.getElementById('pfName')?.focus(), 60)
}

async function logout() {
  const ok = await confirmDialog('退出后需要重新登录，本机记录会保留。', {
    title: '退出登录',
    okText: '退出',
    danger: true
  })
  if (!ok) return
  store.logout()
  router.push('/login')
}

/* ---------------- 修改密码 ---------------- */
const pwdOpen = ref(false)
const pwd = reactive({ old: '', next: '', confirm: '' })

function openPwd() {
  pwd.old = ''
  pwd.next = ''
  pwd.confirm = ''
  pwdOpen.value = true
}
function savePwd() {
  if (!pwd.old) {
    toast('请输入当前密码', 'error')
    return
  }
  if (pwd.next.length < 6 || pwd.next.length > 50) {
    toast('新密码长度需为 6–50 位', 'error')
    return
  }
  if (pwd.next !== pwd.confirm) {
    toast('两次输入的新密码不一致', 'error')
    return
  }
  pwdOpen.value = false
  toast('密码已更新（演示环境不强制重新登录）')
}

/* ---------------- 饮食偏好 ---------------- */
const DIET = ['清淡', '低脂', '低盐', '低糖', '高蛋白', '素食']
const ALLERGENS = ['花生', '海鲜', '乳制品', '鸡蛋', '麸质', '坚果']
const DISLIKES = ['香菜', '动物内脏', '苦瓜', '芹菜', '洋葱']
const LIKES = ['鸡胸肉', '三文鱼', '蓝莓', '燕麦', '豆腐', '西兰花']

const prefs = reactive({
  diet: (store.preferences.dietType || []).slice(),
  allergens: (store.preferences.allergens || []).slice(),
  dislikes: (store.preferences.dislikes || []).slice(),
  likes: (store.preferences.likes || []).slice()
})
const mealsPerDay = ref(+store.preferences.mealsPerDay || 3)
const snackOn = ref(!!store.preferences.snack)

const prefGroups = [
  { key: 'diet', label: '饮食类型（可多选）', options: DIET },
  { key: 'allergens', label: '过敏原（命中后不再推荐）', options: ALLERGENS },
  { key: 'dislikes', label: '不喜欢的食材', options: DISLIKES },
  { key: 'likes', label: '常吃食材', options: LIKES }
]

function togglePref(key, val) {
  const list = prefs[key].slice()
  const i = list.indexOf(val)
  if (i > -1) list.splice(i, 1)
  else list.push(val)
  prefs[key] = list
}

function savePrefs() {
  store.savePreferences({
    dietType: prefs.diet,
    allergens: prefs.allergens,
    dislikes: prefs.dislikes,
    likes: prefs.likes,
    mealsPerDay: mealsPerDay.value,
    snack: snackOn.value
  })
  toast('饮食偏好已保存')
}

/* ---------------- 收藏 ---------------- */
/* 收藏食谱接真接口后，完整数据由 /recipe/collect/list 提供，
   不能再拿 id 去本地 DB.recipes 里找了 —— 后端 id 是 101 起，本地只有 1~8。 */
const favList = ref([])

async function loadFavs() {
  const res = await recipesApi.collected()
  if (res.code === 200) favList.value = res.data
}

/* 再用 store 里的 id 过滤一遍：取消收藏后能立刻从列表里消失，不用等接口重拉 */
const favRecipes = computed(() =>
  favList.value.filter((r) => store.recipeCollectIds.includes(r.id))
)
const favArticles = computed(() =>
  store.articleCollectIds.map((id) => DB.articles.find((a) => a.id === +id)).filter(Boolean)
)

async function unfav(id) {
  const res = await recipesApi.collect(id)
  if (res.code !== 200) {
    toast(res.message, 'error')
    return
  }
  if (!res.data.collected) {
    favList.value = favList.value.filter((r) => r.id !== +id)
    toast('已取消收藏')
  }
}

onMounted(loadFavs)

/* ---------------- 阅读历史 ---------------- */
const reads = computed(() =>
  store.articleReadList
    .map((r) => ({ ...r, article: DB.articles.find((a) => a.id === r.id) }))
    .filter((r) => r.article)
)

/* ---------------- 通知 ---------------- */
const notifFilter = ref('all')
const notifList = computed(() =>
  store.notifications.filter((n) => notifFilter.value === 'all' || !n.read)
)

const NOTIF_ICON = {
  警告: 'alert',
  目标达成: 'target',
  文章推荐: 'news',
  饮食提醒: 'clock'
}

const LINK_MAP = {
  'home.html': '/',
  'health.html': '/health',
  'goal.html': '/goal',
  'record.html': '/record',
  'recipes.html': '/recipes',
  'ingredients.html': '/ingredients',
  'knowledge.html': '/knowledge',
  'assistant.html': '/assistant',
  'account.html': '/account',
  'admin.html': '/admin'
}

/** 把静态版的 'xxx.html?id=1' 转成 SPA 路由 */
function notifLink(link) {
  if (!link) return ''
  const [file, query] = link.split('?')
  const id = query ? new URLSearchParams(query).get('id') : ''
  if (file === 'recipe-detail.html') return '/recipes/' + id
  if (file === 'article-detail.html') return '/knowledge/' + id
  return LINK_MAP[file] || '/'
}

function markRead(n) {
  store.markNotifRead(n.id)
  toast('已标记为已读')
}
function delNotif(n) {
  store.removeNotif(n.id)
  toast('通知已删除')
}
function markAll() {
  store.markAllRead()
  toast('全部通知已标记为已读')
}
</script>

<template>
  <header class="page-head reveal">
    <div>
      <p class="eyebrow">Account &amp; Preferences</p>
      <h1 class="page-title">个人中心</h1>
      <p class="page-sub">账号资料、饮食偏好、收藏与通知，都在这一页管理。</p>
    </div>
    <div class="page-actions">
      <RouterLink class="btn btn-outline" to="/health">
        <SvgIcon name="heart-pulse" />健康档案
      </RouterLink>
      <RouterLink class="btn btn-primary" to="/goal">
        <SvgIcon name="target" />调整目标
      </RouterLink>
    </div>
  </header>

  <!-- 资料头 -->
  <section class="card profile-head reveal d1">
    <span class="avatar lg">{{ (profile.username || '用')[0] }}</span>
    <div class="grow">
      <div class="row" style="gap: 10px">
        <h2 class="display" style="font-size: 24px; color: var(--green-950)">{{ profile.username }}</h2>
        <span class="badge"><SvgIcon name="shield" />{{ roleText }}</span>
        <span class="badge gray">账号正常</span>
      </div>
      <p class="small muted">{{ profile.email }} · 注册于 {{ DB.user.joined }}</p>
      <div class="account-stat">
        <div>
          <div class="v num">{{ stats.recipes }}</div>
          <div class="k">收藏食谱</div>
        </div>
        <div>
          <div class="v num">{{ stats.articles }}</div>
          <div class="k">收藏文章</div>
        </div>
        <div>
          <div class="v num">{{ stats.records }}</div>
          <div class="k">累计记录</div>
        </div>
        <div>
          <div class="v num">{{ stats.streak }}</div>
          <div class="k">连续记录</div>
        </div>
      </div>
    </div>
    <button class="btn btn-soft btn-sm" @click="editProfile">
      <SvgIcon name="edit" />编辑资料
    </button>
  </section>

  <!-- tab 头 -->
  <div class="tabs mt-24 reveal d2" role="tablist">
    <button
      v-for="t in tabs"
      :key="t.key"
      class="tab"
      :class="{ on: tab === t.key }"
      @click="tab = t.key"
    >
      {{ t.label }}
      <span
        v-if="t.key === 'notifs'"
        class="badge amber"
        style="margin-left: 4px"
        :style="{ display: store.unreadCount ? 'inline-flex' : 'none' }"
      >
        {{ store.unreadCount }}
      </span>
    </button>
  </div>

  <!-- ===== 账号资料 ===== -->
  <section v-show="tab === 'profile'" class="tab-panel on">
    <div class="grid split">
      <article class="card">
        <div class="card-hd">
          <h3>基础资料</h3>
          <span class="small muted">用于账号识别与提醒</span>
        </div>
        <div class="card-bd">
          <form class="grid g2" novalidate @submit.prevent="saveProfile">
            <label class="field">
              <span class="field-label">用户名</span>
              <input id="pfName" v-model="profile.username" class="input" type="text" />
            </label>
            <label class="field">
              <span class="field-label">邮箱</span>
              <input v-model="profile.email" class="input" type="email" />
            </label>
            <label class="field">
              <span class="field-label">手机号</span>
              <input v-model="profile.phone" class="input" type="tel" placeholder="选填" />
            </label>
            <label class="field">
              <span class="field-label">性别</span>
              <select v-model="gender" class="select">
                <option>女</option>
                <option>男</option>
                <option>不便透露</option>
              </select>
            </label>
            <div class="field" style="grid-column: 1/-1">
              <span class="field-label">当前目标</span>
              <div class="row wrap">
                <span class="chip on">{{ store.goalInfo.goalType }}</span>
                <span class="tag">每日 {{ store.goalInfo.kcal }} kcal</span>
                <span class="tag">目标体重 {{ store.goalInfo.targetWeight.toFixed(1) }} kg</span>
              </div>
            </div>
            <div style="grid-column: 1/-1" class="row">
              <button class="btn btn-primary" type="submit">保存资料</button>
              <span class="small muted">修改邮箱需重新验证，演示环境直接生效。</span>
            </div>
          </form>
        </div>
      </article>

      <aside class="col" style="gap: 20px">
        <article class="card">
          <div class="card-hd"><h3>账号与安全</h3></div>
          <div class="card-bd">
            <div class="row-between" style="padding: 10px 0; border-bottom: 1px dashed var(--border)">
              <div>
                <strong style="font-size: 13px">登录密码</strong>
                <p class="small muted">上次修改：30 天前</p>
              </div>
              <button class="btn btn-outline btn-sm" @click="openPwd">修改</button>
            </div>
            <div class="row-between" style="padding: 10px 0; border-bottom: 1px dashed var(--border)">
              <div>
                <strong style="font-size: 13px">邮箱验证</strong>
                <p class="small muted">{{ profile.email }} 已验证</p>
              </div>
              <span class="badge"><SvgIcon name="check" />已验证</span>
            </div>
            <div class="row-between" style="padding: 10px 0">
              <div>
                <strong style="font-size: 13px">登录设备</strong>
                <p class="small muted">Windows · Chrome · 当前设备</p>
              </div>
              <span class="dot" />
            </div>
            <button class="btn btn-danger btn-sm btn-block mt-16" @click="logout">
              <SvgIcon name="logout" />退出登录
            </button>
          </div>
        </article>

        <div class="alert-inline green">
          <SvgIcon name="info" />
          <span>你的健康档案与饮食偏好只用于本机原型演示，不会上传到服务器。</span>
        </div>
      </aside>
    </div>
  </section>

  <!-- ===== 饮食偏好 ===== -->
  <section v-show="tab === 'prefs'" class="tab-panel on">
    <div class="grid split">
      <article class="card">
        <div class="card-hd">
          <h3>口味与禁忌</h3>
          <span class="small muted">会参与推荐过滤</span>
        </div>
        <div class="card-bd">
          <template v-for="(g, i) in prefGroups" :key="g.key">
            <p class="field-label" :class="{ 'mt-24': i > 0 }">{{ g.label }}</p>
            <div class="row wrap">
              <button
                v-for="opt in g.options"
                :key="opt"
                type="button"
                class="chip"
                :class="{ on: prefs[g.key].includes(opt) }"
                @click="togglePref(g.key, opt)"
              >
                {{ opt }}
              </button>
            </div>
          </template>

          <div class="row-between mt-24" style="padding-top: 16px; border-top: 1px dashed var(--border)">
            <div>
              <p class="field-label" style="margin: 0">每日餐次</p>
              <div class="seg mt-8">
                <button
                  v-for="m in [3, 4, 5]"
                  :key="m"
                  :class="{ on: mealsPerDay === m }"
                  @click="mealsPerDay = m"
                >
                  {{ m === 3 ? '三餐' : m === 4 ? '三餐 + 加餐' : '少食多餐' }}
                </button>
              </div>
            </div>
            <label class="switch">
              <input v-model="snackOn" type="checkbox" />
              <span class="track" />
              <span class="switch-text">安排加餐</span>
            </label>
          </div>

          <button class="btn btn-primary mt-24" @click="savePrefs">保存偏好</button>
        </div>
      </article>

      <aside class="col" style="gap: 20px">
        <article class="card card-pad">
          <p class="eyebrow" style="margin: 0">Preview · 偏好预览</p>
          <p class="small muted mt-8">
            根据当前偏好，推荐会优先选择清淡、低脂的做法，并排除花生与香菜。
          </p>
          <div class="mt-16">
            <div class="row wrap" style="gap: 6px">
              <template v-if="prefs.diet.length">
                <span v-for="d in prefs.diet" :key="d" class="tag">{{ d }}</span>
              </template>
              <span v-else class="small muted">未选择饮食类型</span>
            </div>
            <div class="small muted mt-12">过敏原：{{ prefs.allergens.join('、') || '无' }}</div>
            <div class="small muted mt-8">
              推荐将优先使用：{{ prefs.likes.slice(0, 4).join('、') || '暂无' }}
            </div>
          </div>
        </article>
        <div class="alert-inline">
          <SvgIcon name="alert" />
          <span>过敏原属于安全信息，命中后将被强制排除；如为严重过敏，请以医生意见为准。</span>
        </div>
      </aside>
    </div>
  </section>

  <!-- ===== 我的收藏 ===== -->
  <section v-show="tab === 'favs'" class="tab-panel on">
    <div class="grid split">
      <article class="card">
        <div class="card-hd">
          <h3>收藏的食谱</h3>
          <RouterLink class="link-btn" to="/recipes">
            去找食谱 <SvgIcon name="chevron-right" />
          </RouterLink>
        </div>
        <div class="card-bd">
          <template v-if="favRecipes.length">
            <div v-for="r in favRecipes" :key="r.id" class="fav-row">
              <img class="fav-thumb" :src="r.img" :alt="r.name" />
              <div class="fav-main">
                <strong>{{ r.name }}</strong>
                <span>{{ r.mealType }} · {{ r.kcal }} kcal · 蛋白 {{ r.p }}g</span>
              </div>
              <RouterLink class="btn btn-outline btn-sm" :to="'/recipes/' + r.id">查看</RouterLink>
              <button class="icon-btn plain" title="取消收藏" @click="unfav(r.id)">
                <SvgIcon name="bookmark" />
              </button>
            </div>
          </template>
          <div v-else class="empty">
            <div class="empty-ico"><SvgIcon name="bookmark" /></div>
            <h4>还没有收藏食谱</h4>
            <p>在食谱库点击书签图标即可收藏。</p>
          </div>
        </div>
      </article>

      <aside class="card">
        <div class="card-hd">
          <h3>收藏的文章</h3>
          <RouterLink class="link-btn" to="/knowledge">
            去读文章 <SvgIcon name="chevron-right" />
          </RouterLink>
        </div>
        <div class="card-bd">
          <template v-if="favArticles.length">
            <div v-for="a in favArticles" :key="a.id" class="fav-row">
              <div class="fav-main">
                <strong>{{ a.title }}</strong>
                <span>{{ a.cat }} · {{ a.date }} · {{ a.views.toLocaleString('zh-CN') }} 阅读</span>
              </div>
              <RouterLink class="btn btn-outline btn-sm" :to="'/knowledge/' + a.id">阅读</RouterLink>
            </div>
          </template>
          <div v-else class="empty">
            <div class="empty-ico"><SvgIcon name="news" /></div>
            <h4>还没有收藏文章</h4>
            <p>在文章详情页点击收藏即可。</p>
          </div>
        </div>
      </aside>
    </div>
  </section>

  <!-- ===== 阅读历史 ===== -->
  <section v-show="tab === 'history'" class="tab-panel on">
    <article class="card">
      <div class="card-hd">
        <h3>最近阅读</h3>
        <span class="small muted">记录阅读时长，用于内容推荐</span>
      </div>
      <div class="card-bd">
        <template v-if="reads.length">
          <div v-for="r in reads" :key="r.id" class="hist-row">
            <img class="fav-thumb" :src="r.article.cover" alt="" />
            <div class="fav-main">
              <strong>{{ r.article.title }}</strong>
              <span>{{ r.date }} · 阅读 {{ r.duration }} 秒 · {{ r.article.cat }}</span>
            </div>
            <RouterLink class="btn btn-outline btn-sm" :to="'/knowledge/' + r.article.id">
              继续阅读
            </RouterLink>
          </div>
        </template>
        <div v-else class="empty">
          <div class="empty-ico"><SvgIcon name="file-text" /></div>
          <h4>还没有阅读记录</h4>
          <p>阅读文章后会自动记录，用于优化推荐。</p>
        </div>
      </div>
    </article>
  </section>

  <!-- ===== 通知中心 ===== -->
  <section v-show="tab === 'notifs'" class="tab-panel on">
    <article class="card">
      <div class="card-hd">
        <h3>通知中心</h3>
        <div class="notif-toolbar" style="margin: 0">
          <div class="seg">
            <button :class="{ on: notifFilter === 'all' }" @click="notifFilter = 'all'">全部</button>
            <button :class="{ on: notifFilter === 'unread' }" @click="notifFilter = 'unread'">
              未读
            </button>
          </div>
          <button class="btn btn-outline btn-sm" @click="markAll">
            <SvgIcon name="check" />全部已读
          </button>
        </div>
      </div>

      <div>
        <template v-if="notifList.length">
          <div
            v-for="n in notifList"
            :key="n.id"
            class="notif-item"
            :class="{ unread: !n.read, amber: n.type === '警告' }"
          >
            <span class="notif-ico"><SvgIcon :name="NOTIF_ICON[n.type] || 'bell'" /></span>
            <div class="notif-bd grow">
              <strong>{{ n.title }}</strong>
              <p>{{ n.content }}</p>
              <div class="row mt-8" style="gap: 8px">
                <span class="tag">{{ n.type }}</span>
                <RouterLink v-if="n.link" class="link-btn" :to="notifLink(n.link)">
                  查看详情
                </RouterLink>
                <button class="link-btn" @click="markRead(n)">标记已读</button>
                <button class="link-btn" style="color: var(--text-3)" @click="delNotif(n)">删除</button>
              </div>
            </div>
            <span class="notif-time">{{ n.time.split(' ')[1] }}</span>
            <span v-if="!n.read" class="unread-mark" />
          </div>
        </template>
        <div v-else class="empty" style="padding: 40px 20px">
          <div class="empty-ico"><SvgIcon name="bell" /></div>
          <h4>没有通知</h4>
          <p>{{ notifFilter === 'unread' ? '所有通知都已读。' : '有新消息时会出现在这里。' }}</p>
        </div>
      </div>
    </article>
  </section>

  <p class="small muted mt-32" style="text-align: center">
    账号相关操作均为本地模拟，不会产生真实短信或邮件。
  </p>

  <!-- 修改密码弹窗 -->
  <div class="overlay" :class="{ open: pwdOpen }" @click.self="pwdOpen = false">
    <div class="modal" style="width: min(440px, 100%)">
      <div class="modal-hd">
        <div>
          <h3>修改密码</h3>
          <p>新密码需 6–50 位，修改后需重新登录。</p>
        </div>
        <button class="modal-close" @click="pwdOpen = false"><SvgIcon name="x" /></button>
      </div>
      <div class="modal-bd">
        <label class="field mb-16">
          <span class="field-label">当前密码</span>
          <input v-model="pwd.old" class="input" type="password" placeholder="请输入当前密码" />
        </label>
        <label class="field mb-16">
          <span class="field-label">新密码</span>
          <input v-model="pwd.next" class="input" type="password" placeholder="6–50 位" />
        </label>
        <label class="field">
          <span class="field-label">确认新密码</span>
          <input v-model="pwd.confirm" class="input" type="password" placeholder="再次输入" />
        </label>
        <p class="small muted mt-12">演示环境：当前密码为 123456。</p>
      </div>
      <div class="modal-ft">
        <button class="btn btn-outline" @click="pwdOpen = false">取消</button>
        <button class="btn btn-primary" @click="savePwd">确认修改</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fav-row {
  display: flex;
  gap: 14px;
  align-items: center;
  padding: 14px 0;
  border-bottom: 1px dashed var(--border);
}
.fav-row:last-child {
  border-bottom: 0;
}
.fav-row .fav-thumb {
  width: 74px;
  height: 56px;
  border-radius: 10px;
  object-fit: cover;
  flex: none;
}
.fav-row .fav-main {
  flex: 1;
  min-width: 0;
}
.fav-row .fav-main strong {
  display: block;
  font-size: 13px;
  font-weight: 500;
}
.fav-row .fav-main span {
  font-size: 11.5px;
  color: var(--text-3);
}
.hist-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 0;
  border-bottom: 1px dashed var(--border);
}
.hist-row:last-child {
  border-bottom: 0;
}
.hist-row .fav-thumb {
  width: 74px;
  height: 56px;
  border-radius: 10px;
  object-fit: cover;
  flex: none;
}
.hist-row .fav-main {
  flex: 1;
  min-width: 0;
}
.hist-row .fav-main strong {
  display: block;
  font-size: 13px;
  font-weight: 500;
}
.hist-row .fav-main span {
  font-size: 11.5px;
  color: var(--text-3);
}
.notif-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}
.account-stat {
  display: flex;
  gap: 28px;
  flex-wrap: wrap;
  margin-top: 6px;
}
.account-stat .v {
  font-family: var(--font-num);
  font-size: 22px;
  color: var(--green-950);
}
.account-stat .k {
  font-size: 11px;
  color: var(--text-3);
}
</style>
