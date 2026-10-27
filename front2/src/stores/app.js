/* ============================================================
   stores/app.js · 全局状态层（Pinia）
   ------------------------------------------------------------
   对应静态版的 js/store.js，职责完全一致：
   会话 / 健康档案 / 饮食偏好 / 饮食目标 / 饮食记录 /
   收藏点赞阅读 / 通知 / AI 会话 / 饮水

   三点变化：
   1) 原来是普通对象 + 每次读 localStorage；现在用 ref 存内存，
      再用 watch 自动写回 localStorage（改数据页面就会自动更新）
   2) 原来是函数 Store.health()；现在是状态 healthInfo，
      访问方式变成 store.healthInfo
   3) 推导值（通知列表、未读数、趋势）用 computed，不再每次重算
   ============================================================ */
import { ref, computed, watch } from 'vue'
import { defineStore } from 'pinia'
import DB from '@/mock/db'
import recipeChickenImg from '@/assets/recipe-chicken.jpg'

const PREFIX = 'sh_'
const K = {
  session: PREFIX + 'session',
  health: PREFIX + 'health',
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

/** 首次访问时把种子数据灌进 localStorage（静态版的 seed()） */
function seed() {
  if (!read(K.records)) {
    write(
      K.records,
      DB.records.map((r) => Object.assign({}, r, { date: TODAY }))
    )
  }
  if (!read(K.collectRecipe)) write(K.collectRecipe, [1, 3])
  if (!read(K.customRecipe)) {
    write(K.customRecipe, [
      {
        id: 1001,
        custom: true,
        name: '番茄鸡胸意面',
        desc: '自己常做的低脂高蛋白快手午餐，20 分钟出锅。',
        mealType: '午餐',
        cuisine: '西式',
        time: 20,
        level: '简单',
        servings: 1,
        kcal: 486,
        p: 39,
        c: 52,
        f: 11,
        fiber: 6.2,
        fit: ['减脂', '增肌'],
        img: recipeChickenImg,
        rating: 0,
        views: 0,
        collects: 0,
        ingredients: [
          { name: '全麦意面', amount: '70', unit: 'g' },
          { name: '鸡胸肉', amount: '120', unit: 'g' },
          { name: '番茄', amount: '2', unit: '个' }
        ],
        steps: ['意面下沸水煮 8 分钟，捞出备用。', '鸡胸切条用黑胡椒腌 5 分钟，少油煎熟。', '番茄炒出汁，倒入意面与鸡胸翻匀即可。'],
        tips: '用不粘锅可把用油控制在 5g 以内。',
        createdAt: TODAY,
        updatedAt: TODAY
      }
    ])
  }
  if (!read(K.collectArticle)) write(K.collectArticle, [2])
  if (!read(K.likeArticle)) write(K.likeArticle, [1])
  if (!read(K.readArticle)) {
    write(K.readArticle, [{ id: 2, date: '2026-10-21', duration: 186, done: true }])
  }
  if (!read(K.notif)) {
    write(K.notif, {
      read: DB.notifications.filter((n) => n.read).map((n) => n.id),
      deleted: []
    })
  }
  if (!read(K.convos)) write(K.convos, DB.conversations)
  if (!read(K.water)) write(K.water, 4)
}
seed()

export const useAppStore = defineStore('app', () => {
  /* ================= 状态 ================= */
  const session = ref(read(K.session, null)) // 登录态
  const healthInfo = ref(read(K.health, DB.health)) // 健康档案
  const preferences = ref(read(K.pref, DB.preferences)) // 饮食偏好
  const goalInfo = ref(read(K.goal, DB.goal)) // 饮食目标
  const recordList = ref(read(K.records, [])) // 饮食记录
  const recipeCollectIds = ref(read(K.collectRecipe, []))
  const customRecipeList = ref(read(K.customRecipe, []))
  const articleCollectIds = ref(read(K.collectArticle, []))
  const articleLikeIds = ref(read(K.likeArticle, []))
  const articleReadList = ref(read(K.readArticle, []))
  const notifState = ref(read(K.notif, { read: [], deleted: [] }))
  const convos = ref(read(K.convos, DB.conversations))
  const waterCups = ref(read(K.water, 4))

  /* ================= 持久化 =================
     任一状态变化就写回 localStorage，省掉每处手工同步。 */
  const persisted = [
    [session, K.session],
    [healthInfo, K.health],
    [preferences, K.pref],
    [goalInfo, K.goal],
    [recordList, K.records],
    [recipeCollectIds, K.collectRecipe],
    [customRecipeList, K.customRecipe],
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
  const isAdmin = computed(() => session.value?.role === 'admin')
  const displayName = computed(() => session.value?.username || '朋友')

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

  /**
   * ⚠️ 仅「本地体验」用：不请求后端，直接造一个假会话。
   * 真实登录请用 authApi.login() + enter(res.data)。
   * 保留它是因为后端没起的时候还得能点进系统看界面。
   */
  function login(email, password) {
    const user = DB.user
    session.value = {
      userId: user.userId,
      username: user.username,
      email: email || user.email,
      role: user.role,
      token: 'mock-jwt-' + Date.now()
    }
    return session.value
  }
  function logout() {
    session.value = null
    // 同 enter()：同步清盘，别让 http.js 还拿着上一个账号的 token 发请求
    write(K.session, null)
  }
  function updateProfile(patch) {
    // TODO: 替换为 PUT /user/profile
    if (!session.value) return null
    session.value = Object.assign({}, session.value, patch)
    return session.value
  }

  /* ================= 健康档案 ================= */
  function saveHealth(patch) {
    // TODO: 替换为 POST /health/info
    const next = Object.assign({}, healthInfo.value, patch, { updatedAt: now() })
    // 同时给了身高体重时，顺手把 BMI / 基础代谢算出来
    if (patch.height && patch.weight) {
      const h = patch.height / 100
      next.bmi = +(patch.weight / (h * h)).toFixed(1)
      next.bmr = Math.round(
        10 * patch.weight +
          6.25 * patch.height -
          5 * (patch.age || 29) +
          (patch.gender === '男' ? 5 : -161)
      )
    }
    healthInfo.value = next
    return next
  }

  /* ================= 饮食偏好 ================= */
  function savePreferences(patch) {
    // TODO: 替换为 PUT /user/preferences
    preferences.value = Object.assign({}, preferences.value, patch)
    return preferences.value
  }

  /* ================= 饮食目标 ================= */
  function saveGoal(patch) {
    // TODO: 替换为 POST /health/goal
    goalInfo.value = Object.assign({}, goalInfo.value, patch)
    return goalInfo.value
  }

  /* ================= 饮食记录 ================= */
  function recordsByDate(date) {
    return recordList.value.filter((r) => r.date === date)
  }
  function addRecord(rec) {
    // TODO: 替换为 POST /record/submit（主记录 + 明细数组）
    const item = Object.assign(
      {
        id: 'r-' + Date.now(),
        date: rec.date || TODAY,
        time: rec.time || nowTime(),
        note: rec.note || '',
        items: rec.items || []
      },
      rec
    )
    const sum = (k) =>
      +item.items.reduce((s, i) => s + (+i[k] || 0), 0).toFixed(1)
    item.kcal = Math.round(sum('kcal'))
    item.p = sum('p')
    item.c = sum('c')
    item.f = sum('f')
    recordList.value = recordList.value.concat([item])
    return item
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
  /** 近 7 日趋势：前 6 天取假数据，最后一天用今天真实记录 */
  const trend = computed(() => {
    // TODO: 替换为 GET /record/analysis/trend
    const t = DB.trend7.slice(0, 6).map((d) => Object.assign({}, d))
    const todayTotals = totals(TODAY)
    t.push({
      date: '今天',
      kcal: todayTotals.kcal,
      p: todayTotals.p,
      c: todayTotals.c,
      f: todayTotals.f
    })
    return t
  })

  /* ================= 收藏 / 点赞 / 阅读 ================= */
  function isRecipeCollected(id) {
    return recipeCollectIds.value.includes(+id)
  }
  function toggleRecipeCollect(id) {
    // 仅 mock 模式使用。接真接口后由 api.js 调 setRecipeCollected
    const list = recipeCollectIds.value.slice()
    const i = list.indexOf(+id)
    if (i > -1) list.splice(i, 1)
    else list.push(+id)
    recipeCollectIds.value = list
    return i === -1
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
  /* ---------------- 自定义食谱 ---------------- */
  function getCustomRecipe(id) {
    return customRecipeList.value.find((r) => r.id === +id)
  }
  function saveCustomRecipe(data) {
    // TODO: 替换为 POST /recipe/save（新建） / PUT /recipe/update/{id}（编辑）
    const list = customRecipeList.value.slice()
    if (data.id) {
      const i = list.findIndex((r) => r.id === +data.id)
      if (i > -1) {
        list[i] = Object.assign({}, list[i], data, { id: +data.id, updatedAt: TODAY })
        customRecipeList.value = list
        return list[i]
      }
    }
    const next = list.reduce((m, r) => Math.max(m, r.id), 1000) + 1
    const item = Object.assign(
      { custom: true, rating: 0, views: 0, collects: 0, createdAt: TODAY, updatedAt: TODAY },
      data,
      { id: next }
    )
    list.unshift(item)
    customRecipeList.value = list
    return item
  }
  function removeCustomRecipe(id) {
    // TODO: 替换为 DELETE /recipe/delete/{id}
    customRecipeList.value = customRecipeList.value.filter((r) => r.id !== +id)
    recipeCollectIds.value = recipeCollectIds.value.filter((x) => x !== +id)
  }

  function isArticleCollected(id) {
    return articleCollectIds.value.includes(+id)
  }
  function toggleArticleCollect(id) {
    const list = articleCollectIds.value.slice()
    const i = list.indexOf(+id)
    if (i > -1) list.splice(i, 1)
    else list.push(+id)
    articleCollectIds.value = list
    return i === -1
  }
  function isArticleLiked(id) {
    return articleLikeIds.value.includes(+id)
  }
  function toggleArticleLike(id) {
    const list = articleLikeIds.value.slice()
    const i = list.indexOf(+id)
    if (i > -1) list.splice(i, 1)
    else list.push(+id)
    articleLikeIds.value = list
    return i === -1
  }
  function markArticleRead(id, duration) {
    // TODO: 替换为 POST /article/read/{id}
    const list = articleReadList.value.filter((r) => r.id !== +id)
    list.unshift({ id: +id, date: TODAY, duration: duration || 120, done: true })
    articleReadList.value = list.slice(0, 20)
  }

  /* ================= 通知 ================= */
  const notifications = computed(() =>
    // extra 是后台「发布通知」当场推送的，排在种子数据前面
    (notifState.value.extra || [])
      .concat(DB.notifications)
      .filter((n) => !notifState.value.deleted.includes(n.id))
      .map((n) => Object.assign({}, n, { read: notifState.value.read.includes(n.id) }))
  )
  const unreadCount = computed(() => notifications.value.filter((n) => !n.read).length)

  function markAllRead() {
    // 用推导后的列表而不是 DB，这样后台新发布的通知也能一起标记
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
  /** 后台发布通知后调用，把新通知推到通知中心最前面 */
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
    return convos.value.find((c) => c.id === id)
  }
  function saveConversation(conv) {
    const list = convos.value.slice()
    const i = list.findIndex((c) => c.id === conv.id)
    if (i > -1) list[i] = conv
    else list.unshift(conv)
    convos.value = list
    return conv
  }
  function removeConversation(id) {
    convos.value = convos.value.filter((c) => c.id !== id)
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
    healthInfo,
    preferences,
    goalInfo,
    recordList,
    recipeCollectIds,
    articleCollectIds,
    articleLikeIds,
    articleReadList,
    convos,
    waterCups,
    // 推导
    isLoggedIn,
    isAdmin,
    displayName,
    notifications,
    unreadCount,
    trend,
    // 方法
    login,
    enter,
    logout,
    updateProfile,
    saveHealth,
    savePreferences,
    saveGoal,
    recordsByDate,
    addRecord,
    removeRecord,
    totals,
    isRecipeCollected,
    toggleRecipeCollect,
    setRecipeCollected,
    setCollectIds,
    customRecipeList,
    getCustomRecipe,
    saveCustomRecipe,
    removeCustomRecipe,
    isArticleCollected,
    toggleArticleCollect,
    isArticleLiked,
    toggleArticleLike,
    markArticleRead,
    markAllRead,
    markNotifRead,
    removeNotif,
    publishNotif,
    conversation,
    saveConversation,
    removeConversation,
    addWater,
    now,
    nowTime,
    dateLabel
  }
})
