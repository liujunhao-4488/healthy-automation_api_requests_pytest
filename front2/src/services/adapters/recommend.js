/* ============================================================
   services/adapters/recommend.js · 推荐模块字段适配层
   ------------------------------------------------------------
   后端实测（2026-11-02，GET /recommend/recipes、/recommend/recipes/today）：

     1) 结构是「按餐次分组的对象」，不是列表
        { breakfast: [...], lunch: [...], dinner: [...] }
        而 HomeView 要的是扁平数组 res.data.list —— 必须拍平。

     2) mealType 是英文
        后端："breakfast" / "lunch" / "dinner"
        前端页面：直接显示「记入 breakfast」这种文案，要转成中文。

     3) 字段改名
        前端       后端
        kcal    ← totalCalories
        p       ← protein
        c       ← carbs
        f       ← fat
        time    ← cookingTime
        img     ← 后端没有，用占位符

     4) 没有 fit 数组
        页面模板里有 `r.fit.join(' / ')`，后端给的是 tags 数组
        （内含「早餐」「高蛋白」「低脂」等），直接拿来用最省事。
        但 tags 里混着餐次，展示时最好剔除餐次词。

     5) steps 是 JSON 字符串被拆坏的老问题
        已在后端 splitInstructions 修复（优先按 JSON 数组解析）。

     6) 后端推荐依赖 Python 算法服务（:5000）
        服务未启动时，后端会退回本地降级算法（getLocalRecommendedRecipes）。
        两种来源的结构一致，前端无需区分。
   ============================================================ */

import { NO_IMAGE } from './placeholder'

/** 英文餐次 → 中文 */
const MEAL_CN = { breakfast: '早餐', lunch: '午餐', dinner: '晚餐', snack: '加餐' }
const MEAL_ORDER = ['早餐', '午餐', '晚餐', '加餐']

const dec1 = (v) => Math.round((Number(v) || 0) * 10) / 10
const int0 = (v) => Math.round(Number(v) || 0)

/**
 * 后端单条推荐 → 前端食谱卡片
 */
export function toRecommendItem(be, fallbackMeal) {
  const r = be || {}
  const mealType = MEAL_CN[r.mealType] || MEAL_CN[fallbackMeal] || r.mealType || '午餐'

  // tags 里包含餐次词，展示用的 fit 剔除掉，避免和 mealType 标签重复
  const tags = Array.isArray(r.tags) ? r.tags.filter(Boolean) : []
  const fit = tags.filter((t) => !MEAL_ORDER.includes(t) && t !== '均衡饮食')

  return {
    id: r.id,
    name: r.name || '未命名食谱',
    desc: r.description || '',
    mealType,
    time: Number(r.cookingTime) || 20,
    level: r.difficulty || '简单',

    kcal: int0(r.totalCalories),
    p: dec1(r.protein),
    c: dec1(r.carbs),
    f: dec1(r.fat),
    fiber: dec1(r.fiber),

    // 页面没有真实图片，统一占位符
    img: NO_IMAGE,

    // 推荐相关：分数与理由
    score: int0(r.matchScore),
    target: int0(r.targetCalories),
    reason: r.recommendationReason || '',

    /* 份量个性化：Python 算法会把整份营养按 servingFactor 缩放，
       但详情页读的是数据库里的原始食谱，所以必须把因子带到详情页，
       否则会出现「推荐 500 kcal，详情/记录 400 kcal」的断层。
       recommendedServings 是缩放过后的总份数（标准份数 × 因子）。 */
    servingFactor: Number(r.servingFactor) || 1,
    recommendedServings: Number(r.recommendedServings) || 0,
    standardServings: Number(r.standardServings) || 0,
    servingNote: r.servingNote || '',

    // fit 供页面渲染徽章；为空时给个兜底，避免 r.fit.join 报错
    fit: fit.length ? fit.slice(0, 3) : ['推荐'],

    steps: Array.isArray(r.steps) ? r.steps : [],
    ingredients: Array.isArray(r.ingredients) ? r.ingredients : [],
    _raw: r
  }
}

/**
 * 推荐卡片 → 详情页地址。
 * 带上 sf（份量因子）、rs（推荐总份数）以及卡片实际展示的 k/p/c/f，
 * 详情页据此还原推荐份量的热量、营养和食材用量。
 * 未调整份量时不加参数，保持普通食谱链接干净。
 */
export function toRecipeLink(item) {
  const r = item || {}
  const base = '/recipes/' + r.id
  const query = new URLSearchParams()
  const sf = Number(r.servingFactor)
  if (Number.isFinite(sf) && sf > 0 && Math.abs(sf - 1) >= 0.01) {
    query.set('sf', String(sf))
  }
  if (Number(r.recommendedServings) > 0) {
    query.set('rs', String(r.recommendedServings))
  }
  /* 关键：把卡片上实际展示的营养值一起带过去。
     只带 sf 时，一旦后端没有返回 servingFactor（本地降级算法、老版本接口），
     详情页就会退回数据库原始热量，出现「外面 647、里面 479」。
     带了 k/p/c/f，详情页以推荐值为准，和卡片逐字一致。 */
  const fields = [
    ['k', r.kcal],
    ['p', r.p],
    ['c', r.c],
    ['f', r.f]
  ]
  for (const [key, value] of fields) {
    const n = Number(value)
    if (Number.isFinite(n) && n > 0) query.set(key, String(n))
  }
  const qs = query.toString()
  return qs ? base + '?' + qs : base
}

/**
 * 后端 { breakfast:[], lunch:[], dinner:[] } → 扁平数组
 * 按 早→午→晚 的顺序拼接，页面按顺序渲染。
 */
export function toMealList(data) {
  const d = data || {}
  const out = []
  for (const key of ['breakfast', 'lunch', 'dinner', 'snack']) {
    const arr = d[key]
    if (!Array.isArray(arr)) continue
    for (const item of arr) {
      out.push(toRecommendItem(item, key))
    }
  }
  return out
}

/**
 * 分餐次返回，供「一日三餐」分区的页面使用
 */
export function toMealGroups(data) {
  const d = data || {}
  return ['breakfast', 'lunch', 'dinner'].map((key) => ({
    key,
    label: MEAL_CN[key],
    list: (Array.isArray(d[key]) ? d[key] : []).map((x) => toRecommendItem(x, key))
  }))
}
