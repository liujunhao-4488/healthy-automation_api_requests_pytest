/* ============================================================
   services/api.js · 接口层
   ------------------------------------------------------------
   对应静态版的 js/api.js。签名 / 返回结构照原样保留，
   页面代码永远只认统一信封 { code, message, data }。

   ⭐ 现状（2026-10-26）：
      · 登录 / 注册          已接真接口  AUTH_USE_MOCK = false
      · 食谱列表 / 详情 / 营养 已接真接口  RECIPE_USE_MOCK = false
      · 其余模块              仍走本地 mock，接一个改一个。

   接法就两种状态：
     · MOCK  ：本地 setTimeout + DB 假数据（后端没起也能演示）
     · 真接口：http.js 发请求到 /api（vite 代理 → 127.0.0.1:8080）

   为什么按模块分开关而不是一个全局 USE_MOCK：
   只联调了登录就全局关 mock，其余页面会打到不存在的接口、整站崩。
   一个模块一个开关，「跑通一个关一个」最稳。
   ============================================================ */
import DB from '@/mock/db'
import { useAppStore, TODAY } from '@/stores/app'
import { request } from './http'
import {
  fetchAllRecipes,
  fetchRecipeDetail,
  fetchCollectedRecipes
} from './adapters/recipe'

/** 全局默认：没接后端的模块继续走 mock */
export const USE_MOCK = true

/** 食谱库：已接真实后端（列表 / 详情 / 营养）*/
export const RECIPE_USE_MOCK = false

const delay = (ms) => new Promise((r) => setTimeout(r, ms))
const ok = (data, message) => ({ code: 200, message: message || '操作成功', data })
const fail = (code, message) => ({ code, message, data: null })

const GOAL_LABEL = { 减脂: '减脂', 增肌: '增肌', 控糖: '控糖', 维持: '维持' }

// 后台内容管理：食谱 / 文章 / 食材共用的数据源与文案
const CONTENT_LABEL = { recipe: '食谱', article: '文章', ingredient: '食材' }
function contentOf(type) {
  if (type === 'recipe') return DB.recipes
  if (type === 'article') return DB.articles
  if (type === 'ingredient') return DB.ingredients
  return null
}

/** 推荐匹配分：目标契合 + 热量贴近 + 蛋白/纤维 + 评分 */
function matchScore(recipe, goal) {
  let s = 30
  if (recipe.fit.includes(GOAL_LABEL[goal.goalType] || '维持')) s += 22
  const kcalGap = Math.abs(recipe.kcal - goal.kcal / goal.meals)
  s += Math.max(0, 20 - kcalGap / 18)
  s += Math.min(12, recipe.p / 4)
  s += Math.min(8, recipe.fiber / 1.4)
  s += recipe.rating * 2
  return Math.min(96, Math.round(s))
}

/* ---------------- 账号与认证 FR-AUTH ---------------- */

/** 登录/注册是否走真实后端。设成 true 可退回本地假登录（后端没起时对照用） */
const AUTH_USE_MOCK = false

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
    if (!AUTH_USE_MOCK) {
      const res = await request('/auth/login', { method: 'POST', body: { email, password } })
      if (res.code !== 200) return res
      return ok(trimAvatar(res.data), res.message || '登录成功')
    }
    await delay(520)
    if (!email || !password) return fail(400, '请输入邮箱与密码')
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return fail(400, '邮箱格式不正确')
    if (password.length < 6) return fail(400, '密码错误（至少 6 位）')
    return ok(
      {
        token: 'mock-jwt',
        userId: DB.user.userId,
        username: DB.user.username,
        email,
        role: DB.user.role
      },
      '登录成功'
    )
  },
  // POST /auth/register → 后端注册成功会直接发 token，可以免二次登录
  async register({ username, email, password, phone }) {
    if (!AUTH_USE_MOCK) {
      const res = await request('/auth/register', {
        method: 'POST',
        body: { username, email, password, phone }
      })
      if (res.code !== 200) return res
      return ok(trimAvatar(res.data), res.message || '注册成功')
    }
    await delay(600)
    if (!username || !email || !password) return fail(400, '请完整填写注册信息')
    if (password.length < 6 || password.length > 50) return fail(400, '密码长度需在 6–50 位之间')
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return fail(400, '邮箱格式不正确')
    return ok({ token: 'mock-jwt', userId: DB.user.userId, username, role: 'user' }, '注册成功')
  }
}

/* ---------------- 健康档案 FR-HEALTH ---------------- */
export const healthApi = {
  // GET /health/info
  async get() {
    await delay(320)
    return ok(useAppStore().healthInfo)
  },
  // POST /health/info
  async save(patch) {
    await delay(560)
    if (!patch.height || !patch.weight) return fail(400, '身高与体重为必填项')
    return ok(useAppStore().saveHealth(patch), '健康档案已保存')
  },
  // GET /health/history
  async history() {
    await delay(280)
    return ok([
      { date: '09-01', weight: 71.2 },
      { date: '09-15', weight: 70.4 },
      { date: '10-01', weight: 69.2 },
      { date: '10-10', weight: 68.9 },
      { date: '10-20', weight: 68.4 }
    ])
  }
}

/* ---------------- 饮食目标 FR-GOAL ---------------- */
export const goalApi = {
  // GET /health/goal
  async get() {
    await delay(260)
    return ok(useAppStore().goalInfo)
  },
  // POST /health/goal
  async save(patch) {
    await delay(540)
    const pct = (+patch.proteinPct || 0) + (+patch.carbPct || 0) + (+patch.fatPct || 0)
    if (Math.abs(pct - 100) > 2) return fail(400, '三大营养素占比之和需为 100%')
    return ok(useAppStore().saveGoal(patch), '目标已更新')
  }
}

/* ---------------- 饮食记录 FR-RECORD ---------------- */
export const recordsApi = {
  // GET /record/list?page=&pageSize=&startDate=&endDate=
  async list({ date } = {}) {
    await delay(340)
    const store = useAppStore()
    const d = date || TODAY
    const list = store.recordsByDate(d)
    return ok({ list, total: list.length, date: d })
  },
  // POST /record/submit
  async submit(rec) {
    await delay(520)
    if (!rec.items || !rec.items.length) return fail(400, '请至少添加一项食物')
    return ok(useAppStore().addRecord(rec), '记录已保存')
  },
  // GET /record/analysis/trend
  async trend() {
    await delay(300)
    return ok(useAppStore().trend)
  },
  // GET /record/suggestions
  async suggestions() {
    await delay(420)
    const store = useAppStore()
    const t = store.totals(TODAY)
    const g = store.goalInfo
    const left = Math.max(0, g.kcal - t.kcal)
    const proteinLeft = Math.max(0, Math.round((g.kcal * g.proteinPct) / 100 / 4 - t.p))
    return ok([
      `距今日热量目标还可摄入约 ${left} kcal，晚餐建议控制在 500 kcal 以内。`,
      proteinLeft > 20
        ? `蛋白质还差约 ${proteinLeft}g，可补充鸡胸肉、豆腐或无糖希腊酸奶。`
        : '蛋白质摄入已接近目标，晚餐以蔬菜和适量主食为主即可。',
      '今日膳食纤维约 9g，低于建议的 25g，晚餐可增加一份深色蔬菜。'
    ])
  },
  // DELETE /record/{recordId}
  async remove(id) {
    await delay(300)
    useAppStore().removeRecord(id)
    return ok(null, '记录已删除')
  }
}

/* ---------------- 推荐 FR-RECO ---------------- */
export const recommendApi = {
  // GET /recommend/recipes?breakfastCount=&lunchCount=&dinnerCount=
  async daily() {
    await delay(680)
    const goal = useAppStore().goalInfo
    const pick = (type) =>
      DB.recipes
        .filter((r) => r.mealType === type && r.status !== 0)
        .map((r) => Object.assign({ score: matchScore(r, goal) }, r))
        .sort((a, b) => b.score - a.score)
    return ok({
      engine: 'v2',
      matchScore: 78,
      breakfast: pick('早餐').slice(0, 3),
      lunch: pick('午餐').slice(0, 3),
      dinner: pick('晚餐').slice(0, 3)
    })
  },
  // GET /recommend/recipes/today
  async today() {
    await delay(520)
    const goal = useAppStore().goalInfo
    const types = ['早餐', '午餐', '晚餐']
    const list = types
      .map((t) => {
        const pool = DB.recipes
          .filter((r) => r.mealType === t && r.status !== 0)
          .map((r) => Object.assign({ score: matchScore(r, goal) }, r))
          .sort((a, b) => b.score - a.score)
        return pool[0]
      })
      .filter(Boolean)
    return ok({ engine: 'v2', matchScore: 78, list })
  }
}

/* ---------------- 食材 FR-INGREDIENT ---------------- */
export const ingredientsApi = {
  // GET /ingredient/list?category=&keyword=
  async list({ cat, keyword } = {}) {
    await delay(380)
    let list = DB.ingredients.filter((i) => i.status !== 0)
    if (cat && cat !== '全部') list = list.filter((i) => i.cat === cat)
    if (keyword) list = list.filter((i) => i.name.includes(keyword))
    return ok({ list, total: list.length })
  },
  // POST /recommend/ingredient/substitute
  async substitute({ name, prompt }) {
    await delay(760)
    if (!name) return fail(400, '请先选择需要替代的食材')
    const MAP = {
      鸡胸肉: [
        { name: '北豆腐', kcal: 116, p: 12.2, f: 6.9, reason: '植物蛋白，脂肪低于鸡胸，适合清淡口味', tag: '推荐' },
        { name: '牛里脊', kcal: 125, p: 20.2, f: 3.6, reason: '蛋白接近鸡胸，脂肪低，含铁更丰富', tag: '高蛋白' },
        { name: '鹰嘴豆', kcal: 164, p: 8.9, f: 2.6, reason: '低 GI 且纤维高，替换时需减少主食量', tag: '低GI' }
      ],
      白米饭: [
        { name: '糙米饭', kcal: 112, p: 2.6, f: 0.8, reason: '保留麸皮，纤维更高，餐后血糖更平缓', tag: '低GI' },
        { name: '藜麦', kcal: 368, p: 14.1, f: 6.1, reason: '蛋白质与纤维同时提升，注意生重换算', tag: '高蛋白' },
        { name: '红薯', kcal: 86, p: 1.6, f: 0.1, reason: '热量更低、饱腹感强，适合减脂期', tag: '减脂' }
      ],
      牛奶: [
        { name: '无糖豆奶', kcal: 33, p: 3.3, f: 1.8, reason: '适合乳糖不耐人群，选择无添加糖款', tag: '乳糖不耐' },
        { name: '无糖希腊酸奶', kcal: 59, p: 10.2, f: 0.4, reason: '蛋白密度更高，可减少其他蛋白来源', tag: '高蛋白' }
      ]
    }
    const list = MAP[name] || [
      { name: '北豆腐', kcal: 116, p: 12.2, f: 6.9, reason: '通用低脂蛋白替代，口感中性易调味', tag: '推荐' },
      { name: '鹰嘴豆', kcal: 164, p: 8.9, f: 2.6, reason: '低 GI 主食型替代，增加纤维', tag: '低GI' }
    ]
    return ok({ source: name, prompt: prompt || '', list }, '已找到等价替代方案')
  },
  // POST /ingredient/nutrition
  async nutrition({ id, grams }) {
    await delay(240)
    const ing = DB.ingredients.find((i) => i.id === +id)
    if (!ing) return fail(404, '食材不存在')
    const k = (+grams || 100) / 100
    return ok({
      name: ing.name,
      grams: +grams || 100,
      kcal: Math.round(ing.kcal * k),
      p: +(ing.p * k).toFixed(1),
      c: +(ing.c * k).toFixed(1),
      f: +(ing.f * k).toFixed(1)
    })
  }
}

/* ---------------- 食谱 FR-RECIPE ---------------- */
export const recipesApi = {
  // GET /recipe/list
  async list({ mealType, fit, keyword, page = 1, pageSize = 6 } = {}) {
    /* ---- 真接口 ----
       后端 /recipe/list 是**全量、不带分页参数**的接口（实测 193 条），
       所以筛选和分页在这里做。adapter 里缓存了全量结果，
       RecipesView 的 load() 循环拉 12 页也只会打 1 次网络。 */
    if (!RECIPE_USE_MOCK) {
      const res = await fetchAllRecipes()
      if (res.code !== 200) return res
      // 下面这段筛选逻辑与 mock 分支逐行一致，两边行为不会走偏
      let list = res.data
      if (mealType && mealType !== '全部') list = list.filter((r) => r.mealType === mealType)
      if (fit && fit !== '全部') list = list.filter((r) => r.fit.includes(fit))
      const kw = String(keyword || '').trim()
      if (kw) list = list.filter((r) => r.name.includes(kw) || r.desc.includes(kw))
      const total = list.length
      const start = (page - 1) * pageSize
      return ok({ list: list.slice(start, start + pageSize), total, page, pageSize })
    }
    /* ---- 本地 mock ---- */
    await delay(460)
    let list = DB.recipes.filter((r) => r.status !== 0)
    if (mealType && mealType !== '全部') list = list.filter((r) => r.mealType === mealType)
    if (fit && fit !== '全部') list = list.filter((r) => r.fit.includes(fit))
    if (keyword) list = list.filter((r) => r.name.includes(keyword) || r.desc.includes(keyword))
    const total = list.length
    list = list.slice((page - 1) * pageSize, page * pageSize)
    return ok({ list, total, page, pageSize })
  },
  // GET /recipe/detail/{id}
  async get(id) {
    /* 后端返回 { recipe, ingredients }，adapter 拍平成页面要的单个对象 */
    if (!RECIPE_USE_MOCK) return fetchRecipeDetail(id)

    await delay(400)
    const r = DB.recipes.find((x) => x.id === +id) || useAppStore().getCustomRecipe(id)
    if (!r || r.status === 0) return fail(404, '食谱不存在或已下架')
    return ok(r)
  },
  // GET /recipe/nutrition/{id}
  async nutrition(id) {
    if (!RECIPE_USE_MOCK) {
      const res = await fetchAllRecipes()
      if (res.code !== 200) return res
      const r = res.data.find((x) => x.id === +id)
      return ok(r ? { kcal: r.kcal, p: r.p, c: r.c, f: r.f, fiber: r.fiber } : null)
    }

    await delay(260)
    const r = DB.recipes.find((x) => x.id === +id) || useAppStore().getCustomRecipe(id)
    return ok(r ? { kcal: r.kcal, p: r.p, c: r.c, f: r.f, fiber: r.fiber } : null)
  },
  // POST /recipe/collect/{recipeId} · DELETE /recipe/collect/{recipeId}
  async collect(id) {
    /* 后端的收藏不是 toggle：POST 收藏、DELETE 取消，两个独立请求。
       所以先看本地已知状态决定发哪个，再用后端返回的 collected 作准。 */
    if (!RECIPE_USE_MOCK) {
      const store = useAppStore()
      const on = store.isRecipeCollected(id)
      const res = await request('/recipe/collect/' + id, { method: on ? 'DELETE' : 'POST' })
      if (res.code !== 200) return res
      const collected = !!(res.data && res.data.collected)
      store.setRecipeCollected(id, collected)
      return ok({ collected }, res.message || '收藏状态已更新')
    }

    await delay(260)
    return ok({ collected: useAppStore().toggleRecipeCollect(id) }, '收藏状态已更新')
  },
  // GET /recipe/collect/list 我收藏的食谱（后端直接返回完整食谱，不是 id 列表）
  async collected() {
    if (!RECIPE_USE_MOCK) return fetchCollectedRecipes()

    await delay(220)
    const store = useAppStore()
    return ok(DB.recipes.filter((r) => store.recipeCollectIds.includes(r.id)))
  },
  // GET /recipe/custom 本人创建的自定义食谱
  async custom() {
    await delay(240)
    const store = useAppStore()
    return ok(store.customRecipeList.slice())
  },
  // POST /recipe/save · PUT /recipe/update/{id}
  async save(payload) {
    await delay(480)
    if (!payload.name || !payload.name.trim()) return fail(400, '请填写食谱名称')
    if (!payload.mealType) return fail(400, '请选择餐次')
    if (!(+payload.kcal > 0)) return fail(400, '请填写大于 0 的热量')
    if (!payload.steps || !payload.steps.length) return fail(400, '请至少填写一个制作步骤')
    const saved = useAppStore().saveCustomRecipe(payload)
    return ok(saved, payload.id ? '自定义食谱已更新' : '自定义食谱已保存')
  },
  // DELETE /recipe/delete/{id}
  async remove(id) {
    await delay(320)
    const store = useAppStore()
    if (!store.getCustomRecipe(id)) return fail(404, '自定义食谱不存在')
    store.removeCustomRecipe(id)
    return ok({ id: +id }, '自定义食谱已删除')
  }
}

/* ---------------- 文章 FR-ARTICLE ---------------- */
export const articlesApi = {
  // GET /article/list?category=&tag=&keyword=&page=
  async list({ cat, tag, keyword, page = 1, pageSize = 5 } = {}) {
    await delay(480)
    let list = DB.articles.filter((a) => a.status !== 0)
    if (cat && cat !== '全部') list = list.filter((a) => a.cat === cat)
    if (tag) list = list.filter((a) => a.tags.includes(tag))
    if (keyword) list = list.filter((a) => a.title.includes(keyword) || a.summary.includes(keyword))
    const total = list.length
    list = list.slice((page - 1) * pageSize, page * pageSize)
    return ok({ list, total, page, pageSize })
  },
  // GET /article/detail/{id}
  async get(id) {
    await delay(420)
    const a = DB.articles.find((x) => x.id === +id)
    if (!a || a.status === 0) return fail(404, '文章不存在或已下架')
    return ok(a)
  },
  // POST /article/comment
  async comment({ articleId, content }) {
    await delay(500)
    if (!content || content.trim().length < 2) return fail(400, '评论内容太短')
    return ok({ id: 'c-' + Date.now(), content: content.trim(), time: '刚刚' }, '评论已发布')
  }
}

/* ---------------- AI 助手 FR-ASSISTANT ---------------- */
export const assistantApi = {
  // GET /assistant/conversations
  async conversations() {
    await delay(220)
    return ok(useAppStore().convos)
  },

  /**
   * POST /assistant/chat（SSE 流式）
   * 真实实现：fetch + ReadableStream 读取 event-stream，逐段回调 onChunk
   */
  async chatStream(prompt, { onStart, onChunk, onDone } = {}) {
    const text = (prompt || '').trim()
    const result = buildReply(text)
    if (onStart) onStart()

    if (result.blocked) {
      await delay(420)
      if (onDone) onDone(result)
      return result
    }

    await delay(360)
    const full =
      result.text +
      (result.list ? '\n\n' + result.list.map((x, i) => i + 1 + '. ' + x).join('\n') : '') +
      (result.note ? '\n\n' + result.note : '')
    let shown = ''
    for (let i = 0; i < full.length; i += 2) {
      shown += full.slice(i, i + 2)
      if (onChunk) onChunk(shown, result)
      await delay(16)
    }
    if (onDone) onDone(result)
    return result
  }
}

/* ---------------- 通知 FR-NOTIFY ---------------- */
export const notificationsApi = {
  // GET /notification/list
  async list() {
    await delay(240)
    return ok(useAppStore().notifications)
  },
  // POST /notification/admin/publish
  async publish({ type, title, content, userId, all }) {
    await delay(620)
    if (!title || !content) return fail(400, '标题与内容不能为空')
    const target = all ? '全部启用用户' : '用户 #' + (userId || '—')
    return ok({ type, title, target }, '通知已发布至' + target)
  }
}

/* ---------------- 后台 FR-ADMIN ---------------- */
export const adminApi = {
  // GET /admin/overview
  async overview() {
    await delay(560)
    return ok({
      stats: DB.admin.overview,
      trend: DB.admin.trend7,
      activities: DB.admin.activities,
      topRecipes: DB.recipes.slice().sort((a, b) => b.views - a.views).slice(0, 5),
      topArticles: DB.articles.slice().sort((a, b) => b.views - a.views).slice(0, 5)
    })
  },
  // GET /user/admin/list
  async users({ keyword } = {}) {
    await delay(380)
    let list = DB.admin.users.slice()
    if (keyword) list = list.filter((u) => u.name.includes(keyword) || u.email.includes(keyword))
    return ok({ list, total: list.length })
  },
  // PUT /user/admin/{userId}/status?status=0
  async toggleUser(id, status) {
    await delay(320)
    const u = DB.admin.users.find((x) => x.id === +id)
    if (u) u.status = status
    return ok({ id, status }, status ? '用户已启用' : '用户已禁用')
  },
  // GET /admin/{type}/list  type: recipe | article | ingredient
  async contentList(type, { keyword, cat, status } = {}) {
    await delay(340)
    const list = contentOf(type)
    if (!list) return fail(404, '未知的内容类型')
    let out = list.slice()
    if (keyword) out = out.filter((x) => (x.name || x.title || '').indexOf(keyword) > -1)
    if (cat) out = out.filter((x) => (x.mealType || x.cat) === cat)
    if (status === 'on') out = out.filter((x) => x.status !== 0)
    if (status === 'off') out = out.filter((x) => x.status === 0)
    return ok({ list: out, total: out.length })
  },
  // POST /admin/{type}/create · PUT /admin/{type}/{id}
  async contentSave(type, payload) {
    await delay(420)
    const list = contentOf(type)
    if (!list) return fail(404, '未知的内容类型')
    const label = CONTENT_LABEL[type]
    if (!payload.name && !payload.title) return fail(400, '名称 / 标题不能为空')
    if (payload.id) {
      const item = list.find((x) => x.id === +payload.id)
      if (!item) return fail(404, '内容不存在')
      Object.assign(item, payload, { id: item.id })
      return ok({ id: item.id }, label + '已更新')
    }
    const id = list.reduce((m, x) => Math.max(m, x.id), 0) + 1
    list.unshift(Object.assign({ status: 1 }, payload, { id }))
    return ok({ id }, label + '已创建')
  },
  // PUT /admin/{type}/{id}/status?status=0
  async contentToggle(type, id, status) {
    await delay(300)
    const list = contentOf(type)
    if (!list) return fail(404, '未知的内容类型')
    const item = list.find((x) => x.id === +id)
    if (item) item.status = status
    return ok({ id, status }, CONTENT_LABEL[type] + (status ? '已上架' : '已下架'))
  }
}

/* ---------------- 离线回复生成（规则 + 固定文案） ---------------- */
function buildReply(text) {
  const len = text.length
  const abuse = ['傻', '滚', '垃圾', '白痴', '智障', '妈的', 'fuck']
  const medical = ['诊断', '开药', '处方', '吃什么药', '能治', '治愈', '替代医嘱']

  if (len > 1000) {
    return {
      blocked: true,
      intent: 'blocked',
      source: 'guardrail',
      text: '输入内容超过 1000 字，已触发长度护栏。请精简问题后再试。'
    }
  }
  if (medical.some((w) => text.includes(w))) {
    return {
      blocked: true,
      intent: 'medical',
      source: 'guardrail',
      text: '我只能提供饮食与营养方面的通用建议，不能进行医疗诊断或开具处方。如有相关需求，请咨询医生或临床营养师，并遵医嘱。'
    }
  }
  if (abuse.some((w) => text.toLowerCase().includes(w))) {
    return {
      blocked: true,
      intent: 'abuse',
      source: 'guardrail',
      text: '请保持友善的交流方式，我会继续为你提供饮食建议。'
    }
  }

  if (/替代|换成|代替/.test(text)) {
    return {
      intent: 'advice',
      source: 'ingredient',
      text: '可以按「热量接近、蛋白不低于原食材、脂肪更低」三个条件来替换。以鸡胸肉 100g 为例，以下方案比较接近：',
      list: [
        '北豆腐 120g：热量更低，植物蛋白，适合清淡口味',
        '牛里脊 95g：蛋白接近，脂肪低且含铁更丰富',
        '鹰嘴豆 100g（熟）：低 GI，但需相应减少主食约 40g'
      ],
      note: '替换后记得同步调整用量，保持这一餐蛋白质总量不变。'
    }
  }
  if (/高血脂|血脂|胆固醇|糖尿病|血糖|痛风|尿酸|高血压/.test(text)) {
    return {
      intent: 'knowledge',
      source: 'authority',
      text: '结合权威食养指南的通用原则，可以从这几个方向调整：',
      list: [
        '减少饱和脂肪：肥肉、黄油、奶油点心，烹调油换成橄榄油或菜籽油',
        '每周 2 次深海鱼，每天一小把原味坚果（约 10g）',
        '主食一半换成全谷物或杂豆，增加可溶性膳食纤维',
        '每天蔬菜 300–500g，深色蔬菜占一半',
        '限制含糖饮料与精制甜点，添加糖控制在 25g 以内'
      ],
      note: '以上为通用营养建议，不构成诊断或处方，具体方案请遵医嘱。'
    }
  }
  if (/热量|多少卡|卡路里|GI|嘌呤|蛋白质|碳水|脂肪/.test(text)) {
    return {
      intent: 'knowledge',
      source: 'ingredient',
      text: '我先在食材库里做精确查表，避免给出模糊估算：',
      list: [
        '白米饭（熟）100g ≈ 116 kcal，碳水 25.9g，GI 83',
        '鸡胸肉 100g ≈ 165 kcal，蛋白质 31g，脂肪 3.6g',
        '西兰花 100g ≈ 34 kcal，膳食纤维 1.6g',
        '牛油果 100g ≈ 160 kcal，脂肪 14.7g（热量密度高，注意份量）'
      ],
      note: '数值来自食材库每 100g 均值，实际会因品种与烹调方式浮动。'
    }
  }
  if (/推荐|食谱|吃什么|搭配|早餐|午餐|晚餐|减脂|增肌/.test(text)) {
    const goal = useAppStore().goalInfo
    const cards = DB.recipes.slice(0, 3).map((r) => ({
      title: r.name,
      sub: r.kcal + ' kcal · 蛋白 ' + r.p + 'g',
      img: r.img,
      to: '/recipes/' + r.id
    }))
    return {
      intent: 'recipe',
      source: 'recipe',
      text: '结合你的目标（' + goal.goalType + '，每日 ' + goal.kcal + ' kcal）与健康档案，今天推荐这三份：',
      cards,
      note: '推荐结果会随你的记录与偏好更新；可在「食谱库」查看更多候选。'
    }
  }
  return {
    intent: 'chat',
    source: 'model',
    text: '我可以帮你做这几类事：① 估算食物热量与营养；② 按目标推荐三餐；③ 给食材做等价替代；④ 解释营养概念与慢病饮食原则。你可以直接说「今天晚餐吃什么」「米饭多少卡」这样的问题。',
    note: '涉及诊断、用药与处方的问题，我会拒绝回答并建议你咨询医生。'
  }
}
