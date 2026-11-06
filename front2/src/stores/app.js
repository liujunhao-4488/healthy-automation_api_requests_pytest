/* ============================================================
   stores/app.js · 全局状态层（Pinia）
   ------------------------------------------------------------
   会话 / 健康档案 / 饮食偏好 / 饮食目标 / 饮食记录 /
   收藏点赞阅读 / 通知 / AI 会话 / 饮水

   ⭐ 2026-11-06：本地 mock 已整体删除。
     这里的 ref 只做「后端数据的本地缓存 + 即时回显」，
     初始值一律是空的，任何真实数据都必须由接口拉取后写入。
     没数据就显示空态，绝不拿假数据顶替。
   ============================================================ */
import { ref, computed, watch } from 'vue'
import { defineStore } from 'pinia'
import { toHealthInfo, toGoalInfo } from '@/services/adapters/health'

const PREFIX = 'sh_'
const K = {
  session: PREFIX + 'session',
  adminSession: PREFIX + 'admin_session',
  health: PREFIX + 'health',
  /* 「档案/目标是否真的存在」的标记。和 health/goal 分开存：
     值可能是空的，光看值分不清「没填」和「填了但没数据」。 */
  healthFilled: PREFIX + 'health_filled',
  goalFilled: PREFIX + 'goal_filled',
  pref: PREFIX + 'pref',
  goal: PREFIX + 'goal',
  records: PREFIX + 'records',
  collectRecipe: PREFIX + 'collect_recipe',
  customRecipe: PREFIX + 'custom_recipe',
  collectArticle: PREFIX + 'collect_article',
  likeArticle: PREFIX + 'like_article',
  readArticle: PREFIX + 'read_article',
  notif: PREFIX + 'notif',
  convos: PREFIX + 'convos',
  water: PREFIX + 'water'
}

/* ============================================================
   空档案 / 空目标模板
   ------------------------------------------------------------
   以前 healthInfo 的兜底值是一套写死的假档案（29 岁 / 165cm / 68.4kg），
   后端返回 data:null（新用户没填过）时页面会静默沿用这套假数据 ——
   用户看到的体重、热量、推荐全是别人的。

   现在兜底一律是「全空」：没填就是没填，页面自己显示空态；
   数值一律给 0 而不是 undefined，避免模板里 .toFixed() 抛 NaN。
   ============================================================ */
export const EMPTY_HEALTH = {
  gender: '',
  /* 数值字段用空串而不是 0：输入框直接绑这些值，
     显示「0」比显示空更容易被当成真实数据（尤其是年龄 0、体重 0）。 */
  age: '',
  height: '',
  weight: '',
  waist: '',
  bmi: 0,
  bmr: 0,
  bloodPressure: '',
  bloodSugar: '',
  activity: '',
  exerciseMin: '',
  exerciseType: '',
  chronic: [],
  updatedAt: ''
}

export const EMPTY_GOAL = {
  goalType: '',
  startWeight: 0,
  currentWeight: 0,
  targetWeight: 0,
  kcal: 0,
  proteinPct: 0,
  carbPct: 0,
  fatPct: 0,
  water: 0,
  meals: 3,
  snack: false,
  startDate: '',
  endDate: ''
}

/* 饮食偏好：后端还没填过时就是「什么都没选」 */
export const EMPTY_PREFERENCES = {
  dietType: [],
  allergens: [],
  dislikes: [],
  likes: [],
  mealsPerDay: 3,
  snack: false
}

/* ---------------- 工具函数 ---------------- */
function pad(n) {
  return String(n).padStart(2, '0')
}
function todayStr() {
  const d = new Date()
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate())
}

/** 当前日期，形如 2026-10-26。模块加载时确定一次，和静态版行为一致。 */
export const TODAY = todayStr()

function read(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch (e) {
    return fallback
  }
}
function write(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch (e) {
    /* 忽略配额异常，和静态版一致 */
  }
}

/* 一次性清理：旧版本会用种子数据往 localStorage 里灌假记录、假收藏、
   假自定义食谱、假通知、假 AI 会话。删掉 mock 之后这些 key 里可能还留着，
   继续读下去就会把假数据当成用户真实数据，所以第一次加载时统一清掉。
   只清「曾经被灌过种子」的 key，登录态 / 档案 / 目标这类真实缓存不动。 */
const PURGED_KEY = PREFIX + 'mock_purged_v1'
function purgeOldMockData() {
  try {
    if (localStorage.getItem(PURGED_KEY)) return
    ;[
      K.records,
      K.collectRecipe,
      K.customRecipe,
      K.collectArticle,
      K.likeArticle,
      K.readArticle,
      K.notif,
      K.convos,
      K.pref,
      K.water
    ].forEach((key) => localStorage.removeItem(key))
    localStorage.setItem(PURGED_KEY, '1')
  } catch (e) {
    /* 隐私模式下 localStorage 可能不可用，忽略 */
  }
}
purgeOldMockData()

export const useAppStore = defineStore('app', () => {
  /* ================= 状态 ================= */
  const session = ref(read(K.session, null)) // 用户端登录态
  const adminSession = ref(read(K.adminSession, null)) // 后台登录态，与用户端完全隔离
  const healthFilled = ref(!!read(K.healthFilled, false)) // 后端确实存在档案
  const goalFilled = ref(!!read(K.goalFilled, false)) // 后端确实存在目标
  /* 只有「标记为已填」时才复用本地缓存；老版本留下的 sh_health（其实是
     那套假档案）没有配套标记，会被直接丢弃。 */
  const healthInfo = ref(
    healthFilled.value ? read(K.health, { ...EMPTY_HEALTH }) : { ...EMPTY_HEALTH }
  )
  const preferences = ref(read(K.pref, { ...EMPTY_PREFERENCES })) // 饮食偏好
  const goalInfo = ref(goalFilled.value ? read(K.goal, { ...EMPTY_GOAL }) : { ...EMPTY_GOAL })
  const recordList = ref(read(K.records, [])) // 饮食记录
  const recipeCollectIds = ref(read(K.collectRecipe, []))
  const articleCollectIds = ref(read(K.collectArticle, []))
  const articleLikeIds = ref(read(K.likeArticle, []))
  const articleReadList = ref(read(K.readArticle, []))
  const notifState = ref(read(K.notif, { read: [], deleted: [], remote: [], loaded: false }))
  const convos = ref(read(K.convos, [])) // AI 会话列表（后端拉取后的本地副本）
  const waterCups = ref(read(K.water, 4))

  /* ================= 持久化 =================
     任一状态变化就写回 localStorage，省掉每处手工同步。 */
  const persisted = [
    [session, K.session],
    [adminSession, K.adminSession],
    [healthInfo, K.health],
    [healthFilled, K.healthFilled],
    [preferences, K.pref],
    [goalInfo, K.goal],
    [goalFilled, K.goalFilled],
    [recordList, K.records],
    [recipeCollectIds, K.collectRecipe],
    [articleCollectIds, K.collectArticle],
    [articleLikeIds, K.likeArticle],
    [articleReadList, K.readArticle],
    [notifState, K.notif],
    [convos, K.convos],
    [waterCups, K.water]
  ]
  persisted.forEach(([source, key]) => {
    watch(source, (v) => write(key, v), { deep: true })
  })

  /* ================= 会话 ================= */
  const isLoggedIn = computed(() => !!session.value)
  const displayName = computed(() => session.value?.username || '朋友')
  /* 后台身份只看独立会话：用户端登录永远不会获得后台权限 */
  const isAdminLoggedIn = computed(
    () => !!adminSession.value && adminSession.value.role === 'admin'
  )
  const adminName = computed(() => adminSession.value?.username || '管理员')

  /**
   * 用接口返回的 data 建立会话 —— 登录和注册共用（后端注册成功会直接发 token）
   * data 形状：{ token, userId, username, email, phone, avatar, role }
   */
  function enter(data) {
    if (!data) return null
    session.value = {
      userId: data.userId,
      username: data.username,
      email: data.email,
      phone: data.phone || '',
      role: data.role || 'user',
      avatar: data.avatar || '',
      token: data.token
    }
    // watch 是异步落盘的，登录完马上跳转/发请求时 localStorage 里可能还没有它，
    // 而 http.js 就是靠 sh_session 取 token —— 这里同步补写一次，避免首批请求 401
    write(K.session, session.value)
    return session.value
  }

  function logout() {
    session.value = null
    // 同 enter()：同步清盘，别让 http.js 还拿着上一个账号的 token 发请求
    write(K.session, null)
  }

  /**
   * 建立后台会话。只接受 role=admin，普通账号在这里一律被拒。
   * 后台会话存在 sh_admin_session 里，和用户端的 sh_session 互不覆盖，
   * 所以同一个浏览器可以同时登录一个用户号和一个管理员号。
   */
  function enterAdmin(data) {
    if (!data || data.role !== 'admin') return null
    adminSession.value = {
      userId: data.userId,
      username: data.username,
      email: data.email,
      role: 'admin',
      token: data.token
    }
    write(K.adminSession, adminSession.value)
    return adminSession.value
  }
  function adminLogout() {
    adminSession.value = null
    write(K.adminSession, null)
  }
  function updateProfile(patch) {
    // TODO: 替换为 PUT /user/profile
    if (!session.value) return null
    session.value = Object.assign({}, session.value, patch)
    return session.value
  }

  /* ================= 健康档案 ================= */

  /**
   * 用后端返回的档案覆盖本地（唯一入口）。
   * be 为 null / 非对象 = 这个账号确实没填过 → 清空并标记未填，
   * 绝不回退到 emptyHealth() 那套 29 岁 / 170cm 的默认值。
   * extra：后端不存的本地字段（waist 等），保存后要把表单里的值带回来，否则会丢。
   */
  function applyHealthRemote(be, extra) {
    if (!be || typeof be !== 'object') {
      healthInfo.value = { ...EMPTY_HEALTH }
      healthFilled.value = false
      return false
    }
    const local = Object.assign({}, healthInfo.value, extra || {})
    healthInfo.value = toHealthInfo(be, local)
    healthFilled.value = true
    return true
  }

  /* ================= 饮食偏好 ================= */
  function savePreferences(patch) {
    /* 只做本地回显（真实保存由 userApi.savePreference 落到后端），
       这样保存后不必整页刷新就能让提示文案立刻用上新偏好。 */
    preferences.value = Object.assign({}, preferences.value, patch)
    return preferences.value
  }

  /* ================= 饮食目标 ================= */

  /**
   * 用后端返回的目标覆盖本地。be 为空 → 清空 + 标记未设。
   *
   * 后端 DietGoal 没有 startWeight / currentWeight（前端独有的进度概念）：
   *   currentWeight 用健康档案里的体重兜底；
   *   startWeight 没有就只能等于 currentWeight（进度显示 0%，不是假数据）。
   */
  function applyGoalRemote(be, extra) {
    if (!be || typeof be !== 'object') {
      goalInfo.value = { ...EMPTY_GOAL }
      goalFilled.value = false
      return false
    }
    const next = toGoalInfo(be, Object.assign({}, goalInfo.value, extra || {}))
    if (!next.currentWeight) next.currentWeight = Number(healthInfo.value.weight) || 0
    if (!next.startWeight) next.startWeight = next.currentWeight || 0
    goalInfo.value = next
    goalFilled.value = true
    return true
  }

  /* ================= 饮食记录 ================= */
  function recordsByDate(date) {
    return recordList.value.filter((r) => r.date === date)
  }
  function removeRecord(id) {
    // TODO: 替换为 DELETE /record/{recordId}（软删除）
    recordList.value = recordList.value.filter((r) => r.id !== id)
  }
  /** 某天的热量 / 三大营养素合计 */
  function totals(date) {
    const list = recordsByDate(date || TODAY)
    const sum = { kcal: 0, p: 0, c: 0, f: 0 }
    list.forEach((r) => {
      (r.items || []).forEach((i) => {
        sum.kcal += +i.kcal || 0
        sum.p += +i.p || 0
        sum.c += +i.c || 0
        sum.f += +i.f || 0
      })
    })
    sum.kcal = Math.round(sum.kcal)
    sum.p = +sum.p.toFixed(1)
    sum.c = +sum.c.toFixed(1)
    sum.f = +sum.f.toFixed(1)
    return sum
  }
  /* ================= 收藏 / 点赞 / 阅读 ================= */
  function isRecipeCollected(id) {
    return recipeCollectIds.value.includes(+id)
  }
  /**
   * 明确设置收藏状态（不翻转）。
   * 后端 POST/DELETE 是幂等的两次不同请求，没有 toggle 语义；
   * 用「翻转」去同步，一旦本地和后端不一致就会越翻越错。
   */
  function setRecipeCollected(id, on) {
    const n = +id
    const list = recipeCollectIds.value.slice()
    const i = list.indexOf(n)
    if (on && i === -1) list.push(n)
    else if (!on && i > -1) list.splice(i, 1)
    else return recipeCollectIds.value.includes(n)
    recipeCollectIds.value = list
    return on
  }
  /** 用后端返回的收藏 id 列表整体覆盖本地（登录 / 刷新后同步用） */
  function setCollectIds(ids) {
    recipeCollectIds.value = (ids || []).map(Number).filter((n) => !isNaN(n))
  }

  function isArticleCollected(id) {
    return articleCollectIds.value.includes(+id)
  }
  /** 用后端返回的状态覆盖本地（POST/DELETE 是幂等的两次请求，不能靠翻转同步） */
  function setArticleCollected(id, on) {
    const n = +id
    const list = articleCollectIds.value.slice()
    const i = list.indexOf(n)
    if (on && i === -1) list.push(n)
    else if (!on && i > -1) list.splice(i, 1)
    else return !!on
    articleCollectIds.value = list
    return !!on
  }
  function isArticleLiked(id) {
    return articleLikeIds.value.includes(+id)
  }
  function setArticleLiked(id, on) {
    const n = +id
    const list = articleLikeIds.value.slice()
    const i = list.indexOf(n)
    if (on && i === -1) list.push(n)
    else if (!on && i > -1) list.splice(i, 1)
    else return !!on
    articleLikeIds.value = list
    return !!on
  }
  /** 用后端列表整体覆盖（登录 / 刷新后同步用） */
  function setArticleCollectIds(ids) {
    articleCollectIds.value = (ids || []).map(Number).filter((n) => !isNaN(n))
  }
  function markArticleRead(id, duration) {
    // TODO: 替换为 POST /article/read/{id}
    const list = articleReadList.value.filter((r) => r.id !== +id)
    list.unshift({ id: +id, date: TODAY, duration: duration || 120, done: true })
    articleReadList.value = list.slice(0, 20)
  }

  /* ================= 通知 ================= */
  const notifications = computed(() => {
    const st = notifState.value
    // 只用后端拉回来的真实列表；还没拉到时就是空，不再拿本地种子顶替
    const base = st.remote || []
    const deleted = st.deleted || []
    const read = st.read || []
    return (st.extra || [])
      .concat(base)
      .filter((n) => !deleted.includes(n.id))
      .map((n) => Object.assign({}, n, { read: read.includes(n.id) || !!n.read }))
  })
  const unreadCount = computed(() => notifications.value.filter((n) => !n.read).length)

  /** 后端通知列表拉回来之后同步到 store */
  function setNotifications(list) {
    notifState.value = Object.assign({}, notifState.value, {
      remote: Array.isArray(list) ? list : [],
      loaded: true
    })
  }

  function markAllRead() {
    // 用推导后的列表，这样后台新发布的通知也能一起标记
    notifState.value = Object.assign({}, notifState.value, {
      read: notifications.value.map((n) => n.id)
    })
  }
  function markNotifRead(id) {
    if (notifState.value.read.includes(+id)) return
    notifState.value = Object.assign({}, notifState.value, {
      read: notifState.value.read.concat([+id])
    })
  }
  function removeNotif(id) {
    if (notifState.value.deleted.includes(+id)) return
    notifState.value = Object.assign({}, notifState.value, {
      deleted: notifState.value.deleted.concat([+id])
    })
  }
  /** 后台发布通知后调用，把新通知推到通知中心最前面（真实发布走 notificationApi） */
  function publishNotif({ type, title, content }) {
    const item = {
      id: 'p-' + Date.now(),
      type,
      title,
      content,
      time: now(),
      read: false,
      link: ''
    }
    notifState.value = Object.assign({}, notifState.value, {
      extra: [item].concat(notifState.value.extra || [])
    })
    return item
  }

  /* ================= AI 会话 ================= */
  function conversation(id) {
    return convos.value.find((c) => String(c.id) === String(id))
  }
  function saveConversation(conv) {
    const list = convos.value.slice()
    const i = list.findIndex((c) => String(c.id) === String(conv.id))
    if (i > -1) list[i] = conv
    else list.unshift(conv)
    convos.value = list
    return conv
  }
  function removeConversation(id) {
    convos.value = convos.value.filter((c) => String(c.id) !== String(id))
  }
  /**
   * 用后端会话列表整体覆盖。
   * 已经拉过历史消息的会话要把 messages 带过来，否则刷新列表会把聊天记录冲掉。
   */
  function setConversations(list) {
    const cache = {}
    convos.value.forEach((c) => {
      cache[String(c.id)] = c
    })
    convos.value = (Array.isArray(list) ? list : []).map((c) => {
      const old = cache[String(c.id)]
      return old && old.messagesLoaded
        ? Object.assign({}, c, { messages: old.messages, messagesLoaded: true })
        : c
    })
  }

  /* ================= 饮水 ================= */
  function addWater(cup) {
    waterCups.value = Math.min(8, Math.max(0, cup))
    return waterCups.value
  }

  /* ================= 工具 ================= */
  function now() {
    const d = new Date()
    return (
      d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) +
      ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes())
    )
  }
  function nowTime() {
    const d = new Date()
    return pad(d.getHours()) + ':' + pad(d.getMinutes())
  }
  function dateLabel(date) {
    if (date === TODAY) return '今天'
    const d = new Date(date + 'T00:00:00')
    const week = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    return d.getMonth() + 1 + '月' + d.getDate() + '日 · ' + week[d.getDay()]
  }

  return {
    // 状态
    session,
    adminSession,
    healthInfo,
    healthFilled,
    preferences,
    goalInfo,
    goalFilled,
    recordList,
    recipeCollectIds,
    articleCollectIds,
    articleLikeIds,
    articleReadList,
    convos,
    waterCups,
    // 推导
    isLoggedIn,
    isAdminLoggedIn,
    adminName,
    displayName,
    notifications,
    unreadCount,
    // 方法
    enter,
    logout,
    enterAdmin,
    adminLogout,
    updateProfile,
    applyHealthRemote,
    savePreferences,
    applyGoalRemote,
    recordsByDate,
    removeRecord,
    totals,
    isRecipeCollected,
    setRecipeCollected,
    setCollectIds,
    isArticleCollected,
    setArticleCollected,
    isArticleLiked,
    setArticleLiked,
    setArticleCollectIds,
    markArticleRead,
    markAllRead,
    markNotifRead,
    removeNotif,
    setNotifications,
    publishNotif,
    conversation,
    saveConversation,
    setConversations,
    removeConversation,
    addWater,
    now,
    nowTime,
    dateLabel
  }
})
