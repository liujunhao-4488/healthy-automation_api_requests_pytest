/* ============================================================
   services/api.js · 接口层
   ------------------------------------------------------------
   对应静态版的 js/api.js。签名 / 返回结构照原样保留，
   页面代码永远只认统一信封 { code, message, data }。

   ⭐ 2026-11-06：全部模块都走真实后端，本地 mock 已整体移除。
     · 请求经 http.js 发到 /api（vite 代理 → 127.0.0.1:8081）
     · 后端没起 / 接口报错时如实返回失败码（-1 网络、-2 超时…），
       由页面按失败处理，不再用假数据顶替成功。
     没有「离线演示模式」了：要看界面先把后端跑起来。
   ============================================================ */
import { useAppStore, TODAY } from '@/stores/app'
import { request } from './http'
import {
  fetchAllRecipes,
  fetchRecipeDetail,
  fetchCollectedRecipes,
  fetchCustomRecipes,
  saveCustomRecipe,
  removeCustomRecipe
} from './adapters/recipe'
import {
  toHealthDTO,
  toHistoryList,
  toGoalDTO
} from './adapters/health'
import {
  toSubmitDTO,
  toRecord,
  toRecordList,
  toTrend,
  last7Days
} from './adapters/record'
import {
  toIngredientList,
  filterIngredients,
  toNutritionParams,
  toNutrition,
  toSubstitutes
} from './adapters/ingredient'
import { toMealList, toMealGroups } from './adapters/recommend'
import {
  fetchArticleList,
  fetchArticleDetail,
  fetchArticleComments,
  postArticleComment,
  fetchArticleRecommend,
  fetchArticleTags,
  publishArticle,
  fetchCollectedArticles,
  fetchArticleReadHistory,
  recordArticleRead,
  setArticleLike,
  setArticleCollect
} from './adapters/article'
import {
  fetchConversations,
  fetchConversationMessages,
  deleteConversation,
  chatStream as assistantChatStream
} from './adapters/assistant'
import {
  fetchProfile,
  saveProfile,
  fetchDietPreference,
  saveDietPreference
} from './adapters/user'
import { toNotification } from './adapters/notification'
import {
  toAdminOverview,
  toAdminUser,
  toAdminContentRows
} from './adapters/admin'

const ok = (data, message) => ({ code: 200, message: message || '操作成功', data })
const fail = (code, message) => ({ code, message, data: null })

/* ---------------- 账号与认证 FR-AUTH ---------------- */

/**
 * 后端登录返回的 avatar 是 base64 头像（实测几十 KB 起），
 * 而整个会话要写进 localStorage（配额 5MB），塞进去迟早撑爆。
 * 第二版的头像位用的都是姓名首字，所以超长的直接丢掉；
 * 将来后端改成返回短 URL 时会自动保留。
 */
function trimAvatar(data) {
  if (!data || typeof data.avatar !== 'string' || data.avatar.length <= 8192) return data
  const copy = Object.assign({}, data)
  delete copy.avatar
  return copy
}

export const authApi = {
  // POST /auth/login → { token, userId, username, email, phone, avatar, role }
  async login({ email, password }) {
    const res = await request('/auth/login', { method: 'POST', body: { email, password } })
    if (res.code !== 200) return res
    return ok(trimAvatar(res.data), res.message || '登录成功')
  },
  // POST /auth/register → 后端注册成功会直接发 token，可以免二次登录
  async register({ username, email, password, phone }) {
    const res = await request('/auth/register', {
      method: 'POST',
      body: { username, email, password, phone }
    })
    if (res.code !== 200) return res
    return ok(trimAvatar(res.data), res.message || '注册成功')
  }
}

/* ---------------- 个人资料 / 饮食偏好 ---------------- */
export const userApi = {
  // GET /user/profile
  async profile() {
    return fetchProfile()
  },

  // PUT /user/profile（只支持用户名 / 手机号 / 头像，邮箱不可改）
  async updateProfile(patch) {
    return saveProfile(patch)
  },

  // GET /user/diet-preference
  async preference() {
    return fetchDietPreference()
  },

  // PUT /user/diet-preference
  async savePreference(prefs) {
    return saveDietPreference(prefs)
  }
}

/* ---------------- 健康档案 FR-HEALTH ---------------- */
export const healthApi = {
  // GET /health/info
  async get() {
    const res = await request('/health/info')
    /* 失败就如实返回失败信封 —— 以前这里会 return ok(emptyHealth())，
       等于把「29 岁 / 170cm / 120/80」这套默认值当成用户数据，
       调用方还以为成功了。现在由调用方决定：失败保留本地缓存、不清空。 */
    if (res.code !== 200) return res
    // 后端没有档案时 data 为 null，原样交给调用方走空态
    if (!res.data) return ok(null, res.message || '尚未填写健康档案')
    /* 这里必须返回「后端原始对象」，不能先 toHealthInfo 一次：
       store.applyHealthRemote() 还要拿它做适配，适配两遍会把
       targetCalories→kcal、male→男 这类只映射一次的字段弄丢。 */
    return ok(res.data, res.message || '获取健康信息成功')
  },
  // POST /health/info
  async save(patch) {
    const body = toHealthDTO(patch)
    const res = await request('/health/info', { method: 'POST', body })
    if (res.code !== 200) return res
    const store = useAppStore()
    // 用后端返回的实体回填（bmi 是后端算的），waist 等后端不存的字段从 patch 带回来
    if (!store.applyHealthRemote(res.data, patch)) return fail(500, '保存失败，请稍后重试')
    return ok(store.healthInfo, res.message || '健康档案已保存')
  },
  // GET /health/history
  async history() {
    const res = await request('/health/history')
    if (res.code !== 200) return res
    return ok(toHistoryList(res.data), res.message)
  }
}

/* ---------------- 饮食目标 FR-GOAL ---------------- */
export const goalApi = {
  // GET /health/goal
  async get() {
    const res = await request('/health/goal')
    // 失败如实返回，不再拿本地值冒充「获取成功」
    if (res.code !== 200) return res
    // 新用户后端返回 data:null —— 交给调用方标记「未设目标」，不补默认 1800kcal
    if (!res.data) return ok(null, res.message || '尚未设置饮食目标')
    // 同 healthApi.get：返回原始对象，适配统一由 store.applyGoalRemote 做
    return ok(res.data, res.message || '获取饮食目标成功')
  },
  // POST /health/goal
  async save(patch) {
    const pct = (+patch.proteinPct || 0) + (+patch.carbPct || 0) + (+patch.fatPct || 0)
    if (Math.abs(pct - 100) > 2) return fail(400, '三大营养素占比之和需为 100%')

    const body = toGoalDTO(Object.assign({}, useAppStore().goalInfo, patch))
    const res = await request('/health/goal', { method: 'POST', body })
    if (res.code !== 200) return res
    const store = useAppStore()
    if (!store.applyGoalRemote(res.data, patch)) return fail(500, '保存失败，请稍后重试')
    return ok(store.goalInfo, res.message || '目标已更新')
  }
}

/* ---------------- 饮食记录 FR-RECORD ---------------- */
export const recordsApi = {
  // GET /record/list?page=&pageSize=&startDate=&endDate=
  async list({ date } = {}) {
    const d = date || TODAY
    /* 后端是分页的，前端要「某一天全部记录」，所以把 start/end 都钉死在那天，
       并给一个足够大的 pageSize（一天最多也就十几餐）。
       后端返回按时间倒序，页面自己按 mealType 分组和排序，不用重新排。 */
    const res = await request('/record/list', {
      query: { date: undefined, startDate: d, endDate: d, page: 1, pageSize: 100 }
    })
    if (res.code !== 200) return res
    const list = toRecordList(res.data)
    // 直接刷进 store，页面 recordsByDate() 就能读到
    const store = useAppStore()
    const others = store.recordList.filter((r) => r.date !== d)
    store.recordList = others.concat(list)
    return ok({ list, total: list.length, date: d }, res.message)
  },
  // POST /record/submit
  async submit(rec) {
    if (!rec.items || !rec.items.length) return fail(400, '请至少添加一项食物')

    const body = toSubmitDTO(rec)
    const res = await request('/record/submit', { method: 'POST', body })
    if (res.code !== 200) return res
    /* submit 的响应里 details 是 null，拿不到明细，
       所以再拉一次当天列表，保证页面和数据库一致（也能拿到后端生成的 id）。 */
    const saved = toRecord(res.data)
    await recordsApi.list({ date: saved.date })
    return ok(saved, res.message || '记录已保存')
  },
  // GET /record/analysis/trend?startDate=&endDate=（两个参数都必填）
  async trend() {
    const { startDate, endDate } = last7Days()
    const res = await request('/record/analysis/trend', {
      query: { startDate, endDate }
    })
    if (res.code !== 200) return res
    return ok(toTrend(res.data, { days: 7 }), res.message)
  },
  // GET /record/suggestions
  async suggestions() {
    const res = await request('/record/suggestions')
    if (res.code !== 200) return res
    const list = Array.isArray(res.data) ? res.data : []
    return ok(list, res.message)
  },
  // DELETE /record/{recordId}
  async remove(id) {
    const target = useAppStore().recordList.find((r) => String(r.id) === String(id))
    const res = await request('/record/' + id, { method: 'DELETE' })
    if (res.code !== 200) return res
    // 后端是软删除，本地同步移除，再拉一次当天列表对齐
    useAppStore().removeRecord(id)
    if (target) await recordsApi.list({ date: target.date })
    return ok(null, res.message || '记录已删除')
  }
}

/* ---------------- 推荐 FR-RECO ---------------- */
export const recommendApi = {
  // GET /recommend/recipes?breakfastCount=&lunchCount=&dinnerCount=
  async daily() {
    /* 后端返回按餐次分组的对象 { breakfast, lunch, dinner }，
       toMealList 负责拍平成页面要的一维数组。 */
    const res = await request('/recommend/recipes', {
      query: { breakfastCount: 3, lunchCount: 3, dinnerCount: 3 }
    })
    if (res.code !== 200) return res
    const list = toMealList(res.data)
    /* 取所有建议里的最高分代表整体匹配度；
       后端没给 engine 字段，这里如实标注数据来源为后端推荐。 */
    const top = list.reduce((m, x) => Math.max(m, x.score), 0)
    return ok({ engine: 'v2', matchScore: top, list }, res.message)
  },
  // GET /recommend/recipes?breakfastCount=&lunchCount=&dinnerCount=
  /* 配餐计划：counts 就是需要的天数，1/7/30 天各取对应数量后按天排列 */
  async plan({ breakfastCount = 3, lunchCount = 3, dinnerCount = 3 } = {}) {
    const res = await request('/recommend/recipes', {
      query: { breakfastCount, lunchCount, dinnerCount }
    })
    if (res.code !== 200) return res
    return ok({ groups: toMealGroups(res.data) }, res.message)
  },
  // GET /recommend/recipes/today
  async today() {
    const res = await request('/recommend/recipes/today')
    if (res.code !== 200) return res
    const list = toMealList(res.data)
    const top = list.reduce((m, x) => Math.max(m, x.score), 0)
    return ok({ engine: 'v2', matchScore: top, list }, res.message)
  }
}

/* ---------------- 食材 FR-INGREDIENT ---------------- */

/**
 * 食材全量缓存。
 * /ingredient/list 一次返回 125 条（45KB），而食材页会因筛选、输入关键字反复调用；
 * RecipesView 那套「缓存全量 + 本地筛选」的做法在这里同样适用。
 */
let ingCache = null
let ingCacheAt = 0
const ING_TTL = 5 * 60 * 1000

async function fetchAllIngredients({ force = false } = {}) {
  const now = Date.now()
  if (!force && ingCache && now - ingCacheAt < ING_TTL) {
    return { code: 200, message: 'ok', data: ingCache }
  }
  const res = await request('/ingredient/list')
  if (res.code !== 200) return res
  ingCache = toIngredientList(res.data)
  ingCacheAt = now
  return { code: 200, message: res.message, data: ingCache }
}

export const ingredientsApi = {
  // GET /ingredient/list?category=&keyword=
  async list({ cat, keyword } = {}) {
    const res = await fetchAllIngredients()
    if (res.code !== 200) return res
    // 后端 list 是全量、不带筛选参数，筛选在本地做
    const list = filterIngredients(res.data, { cat, keyword })
    return ok({ list, total: list.length }, res.message)
  },
  // POST /recommend/ingredient/substitute
  async substitute({ name, prompt }) {
    if (!name) return fail(400, '请先选择需要替代的食材')
    /* 后端按营养构成相似度真实计算（2026-11-02 修复，原先为硬编码假数据）。
       返回每项已带营养字段，前端直接渲染即可。 */
    const res = await request('/ingredient/substitute', {
      method: 'POST',
      body: { ingredientName: name, prompt: prompt || '', limit: 4 }
    })
    if (res.code !== 200) return res
    const all = await fetchAllIngredients()
    const pool = all.code === 200 ? all.data : []
    return ok(
      toSubstitutes(res.data, pool, { source: name, prompt }),
      res.message || '已找到等价替代方案'
    )
  },
  // POST /ingredient/nutrition
  async nutrition({ id, grams }) {
    const params = toNutritionParams({ id, grams })
    const res = await request('/ingredient/nutrition', { method: 'POST', body: params })
    if (res.code !== 200) return res
    // 后端返回裸浮点（0.6000000000000001），toNutrition 会规整
    const all = await fetchAllIngredients()
    const pool = all.code === 200 ? all.data : []
    const found = pool.find((x) => String(x.id) === String(id))
    return ok(
      toNutrition(res.data, { name: found ? found.name : '', grams: params.quantity }),
      res.message
    )
  }
}

/* ---------------- 食谱 FR-RECIPE ---------------- */
export const recipesApi = {
  // GET /recipe/list
  async list({ mealType, fit, keyword, page = 1, pageSize = 6 } = {}) {
    /* 后端 /recipe/list 是**全量、不带分页参数**的接口（实测 193 条），
       所以筛选和分页在这里做。adapter 里缓存了全量结果，
       RecipesView 的 load() 循环拉 12 页也只会打 1 次网络。 */
    const res = await fetchAllRecipes()
    if (res.code !== 200) return res
    let list = res.data
    if (mealType && mealType !== '全部') list = list.filter((r) => r.mealType === mealType)
    if (fit && fit !== '全部') list = list.filter((r) => r.fit.includes(fit))
    const kw = String(keyword || '').trim()
    if (kw) list = list.filter((r) => r.name.includes(kw) || r.desc.includes(kw))
    const total = list.length
    const start = (page - 1) * pageSize
    return ok({ list: list.slice(start, start + pageSize), total, page, pageSize })
  },
  // GET /recipe/detail/{id}
  async get(id) {
    /* 后端返回 { recipe, ingredients }，adapter 拍平成页面要的单个对象 */
    return fetchRecipeDetail(id)
  },
  // GET /recipe/nutrition/{id}
  async nutrition(id) {
    const res = await fetchAllRecipes()
    if (res.code !== 200) return res
    const r = res.data.find((x) => x.id === +id)
    return ok(r ? { kcal: r.kcal, p: r.p, c: r.c, f: r.f, fiber: r.fiber } : null)
  },
  // POST /recipe/collect/{recipeId} · DELETE /recipe/collect/{recipeId}
  async collect(id) {
    /* 后端的收藏不是 toggle：POST 收藏、DELETE 取消，两个独立请求。
       所以先看本地已知状态决定发哪个，再用后端返回的 collected 作准。 */
    const store = useAppStore()
    const on = store.isRecipeCollected(id)
    const res = await request('/recipe/collect/' + id, { method: on ? 'DELETE' : 'POST' })
    if (res.code !== 200) return res
    const collected = !!(res.data && res.data.collected)
    store.setRecipeCollected(id, collected)
    return ok({ collected }, res.message || '收藏状态已更新')
  },
  // GET /recipe/collect/list 我收藏的食谱（后端直接返回完整食谱，不是 id 列表）
  async collected() {
    return fetchCollectedRecipes()
  },
  // GET /recipe/custom 本人创建的自定义食谱
  async custom() {
    return fetchCustomRecipes()
  },
  // POST /recipe/save · PUT /recipe/update
  async save(payload) {
    if (!payload.name || !payload.name.trim()) return fail(400, '请填写食谱名称')
    if (!payload.mealType) return fail(400, '请选择餐次')
    if (!(+payload.kcal > 0)) return fail(400, '请填写大于 0 的热量')
    if (!payload.steps || !payload.steps.length) return fail(400, '请至少填写一个制作步骤')

    return saveCustomRecipe(payload)
  },
  // DELETE /recipe/delete/{id}
  async remove(id) {
    return removeCustomRecipe(id)
  }
}

/* ---------------- 文章 FR-ARTICLE ---------------- */
export const articlesApi = {
  // GET /article/list?category=&tag=&keyword=&page=&sort=
  async list({ cat, tag, keyword, page = 1, pageSize = 5, sort = 'recommend' } = {}) {
    return fetchArticleList({
      category: cat && cat !== '全部' ? cat : undefined,
      tag,
      keyword,
      page,
      pageSize,
      sort
    })
  },
  // GET /article/detail/{id}
  async get(id) {
    return fetchArticleDetail(id)
  },
  // GET /article/recommend?excludeId=
  async recommend({ excludeId, page = 1, pageSize = 3 } = {}) {
    return fetchArticleRecommend({ excludeId, page, pageSize })
  },
  // GET /article/tags  全部标签（实测返回纯字符串数组，54 个）
  async tags() {
    return fetchArticleTags()
  },
  // GET /article/comment/list/{articleId}
  async comments(articleId) {
    return fetchArticleComments(articleId, useAppStore().session?.userId)
  },
  // POST /article/comment/{articleId}
  async comment({ articleId, content, parentId }) {
    return postArticleComment(articleId, content, parentId)
  },
  // POST / DELETE /article/like/{articleId}
  async toggleLike(articleId, next) {
    return setArticleLike(articleId, next)
  },
  // POST / DELETE /article/collect/{articleId}
  async toggleCollect(articleId, next) {
    return setArticleCollect(articleId, next)
  },
  // GET /article/collect/list
  async collected() {
    return fetchCollectedArticles()
  },
  // GET /article/read/history
  async history(limit = 20) {
    return fetchArticleReadHistory(limit)
  },
  // POST /article/read/{articleId}
  async read(articleId, payload) {
    return recordArticleRead(articleId, payload)
  },
  // POST /article/publish  用户发帖（后端直接上架 status=1）
  async publish(payload) {
    return publishArticle(payload)
  }
}

/* ---------------- AI 助手 FR-ASSISTANT ---------------- */
export const assistantApi = {
  // GET /assistant/conversations
  async conversations() {
    return fetchConversations()
  },

  // GET /assistant/conversations/{id}/messages
  async messages(conversationId) {
    return fetchConversationMessages(conversationId)
  },

  // DELETE /assistant/conversations/{id}
  async remove(conversationId) {
    return deleteConversation(conversationId)
  },

  /**
   * POST /assistant/chat/stream（SSE）
   * 真实实现见 adapters/assistant.js：逐事件回调 onStart / onChunk，
   * 流结束后把结果放在统一信封里返回（text / intent / source / blocked / cards）。
   */
  async chatStream(prompt, { conversationId, onStart, onChunk } = {}) {
    return assistantChatStream(prompt, { conversationId, onStart, onChunk })
  }
}

/* ---------------- 通知 FR-NOTIFY ---------------- */
export const notificationsApi = {
  // GET /notification/list
  async list() {
    const res = await request('/notification/list')
    if (res.code !== 200) return res
    const raw = Array.isArray(res.data) ? res.data : []
    return { code: 200, message: res.message, data: raw.map(toNotification) }
  },
  // PUT /notification/read/{id}
  async markRead(id) {
    return request('/notification/read/' + id, { method: 'PUT' })
  },
  // PUT /notification/delete/{id}
  async remove(id) {
    return request('/notification/delete/' + id, { method: 'PUT' })
  },
  // POST /notification/admin/publish
  async publish({ type, title, content, userId, all }) {
    if (!title || !content) return fail(400, '标题与内容不能为空')
    const res = await request('/notification/admin/publish', {
      method: 'POST',
      body: {
        type,
        title,
        content,
        userId: all ? null : Number(userId)
      }
    })
    if (res.code !== 200) return res
    const target = all ? '全部启用用户' : '用户 #' + (userId || '—')
    return { code: 200, message: '通知已发布至' + target, data: res.data }
  }
}

/* ---------------- 后台 FR-ADMIN ---------------- */
export const adminApi = {
  // GET /admin/overview
  async overview() {
    const res = await request('/admin/overview')
    if (res.code !== 200) return res
    return { code: 200, message: res.message, data: toAdminOverview(res.data) }
  },
  // GET /user/admin/list
  async users({ keyword } = {}) {
    const res = await request('/user/admin/list')
    if (res.code !== 200) return res
    let list = (Array.isArray(res.data) ? res.data : []).map(toAdminUser)
    if (keyword) {
      list = list.filter((u) => u.name.includes(keyword) || u.email.includes(keyword))
    }
    return { code: 200, message: res.message, data: { list, total: list.length } }
  },
  // PUT /user/admin/{userId}/status?status=0
  async toggleUser(id, status) {
    return request('/user/admin/' + id + '/status', { method: 'PUT', query: { status } })
  },
  // GET /admin/{type}/list  type: recipe | article | ingredient
  async contentList(type, { keyword, cat, status } = {}) {
    const res = await request('/admin/' + type + '/list', {
      query: { keyword, cat, status }
    })
    if (res.code !== 200) return res
    const raw = res.data && Array.isArray(res.data.list) ? res.data.list : []
    const list = toAdminContentRows(type, raw)
    return { code: 200, message: res.message, data: { list, total: list.length } }
  },
  // POST /admin/{type} · PUT /admin/{type}/{id}
  async contentSave(type, payload) {
    if (!payload.name && !payload.title) return fail(400, '名称 / 标题不能为空')
    return payload.id
      ? request('/admin/' + type + '/' + payload.id, { method: 'PUT', body: payload })
      : request('/admin/' + type, { method: 'POST', body: payload })
  },
  // PUT /admin/{type}/{id}/status?status=0
  async contentToggle(type, id, status) {
    return request('/admin/' + type + '/' + id + '/status', {
      method: 'PUT',
      query: { status }
    })
  }
}

