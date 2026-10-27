/* ============================================================
   services/adapters/recipe.js · 食谱字段适配层
   ------------------------------------------------------------
   存在的唯一理由：后端契约和前端页面用的是两套字段名 + 两套类型。
   这个文件负责「翻译」，页面和 api.js 都只认前端那一套。

   实测数据（2026-10-26，GET /recipe/list 共 193 条）暴露了三个
   **光改字段名解决不了**的问题，都在这里处理：

     1. instructions 是 JSON **字符串**
        "[\"藜麦煮熟备用\",\"鸡胸肉煎熟切片\"]"
        → 直接塞给 v-for 会被 Vue 按字符遍历，渲染出几十个单字。
        → 而且 193 条里有 1 条 JSON.parse 会抛，必须 try/catch。

     2. suitableFor 是顿号分隔的**长短语**，且值域和前端完全不同
        后端："减脂人群、健身人群" / "控脂降脂、老年养生"（18 种）
        前端：['减脂', '增肌', '控糖', '维持']
        → 不只是 split，还要做语义归一，否则筛选项永远筛不到东西。

     3. imageUrl **193 条全是 null**，后端根本没有图
        前端 img 要的是可直接渲染的地址
        → 统一走 placeholder.js 的占位符（不再轮换本地菜品照：
          「瘦牛肉饭配三文鱼图」这种图文不符比缺图更糟）。

   另外 cuisineType 有 11 种值（家常/清新/清蒸/清炖/养生/健身餐…），
   前端只有 中式/西式/轻食 三类，也要归一。
   ============================================================ */

import { http } from '@/services/http'
import { withFallbackImage } from './placeholder'

/* ---------------- 数值与图片 ---------------- */

/** 保留一位小数：后端 45.7 保留，403.4 → 403（热量取整更符合中文习惯） */
const dec1 = (v) => Math.round((Number(v) || 0) * 10) / 10

/* ---------------- 餐次 ---------------- */

const MEALS = ['早餐', '午餐', '晚餐']

/**
 * 后端 category：早餐 65 / 午餐 64 / 晚餐 63 / 空 1
 * 前端 MEAL_OPTIONS 还多一个「加餐」，但后端没有这个分类，选了会是空列表。
 */
function toMeal(category) {
  const s = String(category || '').trim()
  return MEALS.includes(s) ? s : '午餐'
}

/* ---------------- 菜系 ---------------- */

/**
 * 后端 11 种 → 前端 3 类
 *   轻食 27 + 健身餐 13            -> 轻食
 *   西式 12                        -> 西式
 *   家常 84 清新 18 清蒸 17 养生 9
 *   清炖 6 中式 5 空 1 脏数据 1     -> 中式
 */
function toCuisine(cuisineType) {
  const s = String(cuisineType || '')
  if (s.includes('西')) return '西式'
  if (s.includes('轻食') || s.includes('健身')) return '轻食'
  return '中式'
}

/* ---------------- 适宜人群 ---------------- */

/**
 * 后端 18 种长短语 → 前端 4 个短标签。
 * 一条 suitableFor 可能命中多个标签（"减脂人群、健身人群" → [减脂, 增肌]）。
 * 一个都命中不了的，兜底 ['维持'] —— 因为页面里 r.fit.includes() 和
 * r.fit.join() 都要求它是非空数组，空数组会让排序/展示出现空档。
 */
const FIT_RULES = [
  { tag: '减脂', kw: ['减脂', '减肥', '控脂', '降脂'] },
  { tag: '增肌', kw: ['增肌', '健身', '增重'] },
  { tag: '控糖', kw: ['控糖', '低糖', '糖尿病'] },
  { tag: '维持', kw: ['维持', '均衡', '养生', '家庭', '儿童', '孕妇', '低盐', '控压'] }
]

function toFit(suitableFor) {
  const raw = String(suitableFor || '')
  const tags = FIT_RULES.filter((r) => r.kw.some((k) => raw.includes(k))).map((r) => r.tag)
  return tags.length ? tags : ['维持']
}

/* ---------------- 制作步骤 ---------------- */

/** 把后端的 JSON 字符串解析成字符串数组；解析失败按换行/分号兜底切 */
function toSteps(instructions) {
  if (Array.isArray(instructions)) return instructions.map(String).filter(Boolean)
  const raw = String(instructions || '').trim()
  if (!raw) return []
  try {
    const arr = JSON.parse(raw)
    if (Array.isArray(arr)) return arr.map(String).filter(Boolean)
    if (typeof arr === 'string' && arr.trim()) return [arr.trim()]
  } catch (e) {
    // 193 条里有 1 条是坏 JSON，落到下面的兜底
  }
  return raw
    .split(/\r?\n|；|;/)
    .map((s) => s.trim())
    .filter(Boolean)
}

/* ---------------- 配料 ---------------- */

/**
 * 后端（关联表出来的）：{ name, quantity, quantityValue, unit, calories, protein... }
 * 前端配料表要的：       { name, amount, unit }
 */
function toIngredient(i) {
  const amount = i.quantity ?? i.quantityValue ?? ''
  return {
    name: i.name || '食材',
    amount: String(amount),
    unit: i.unit || 'g'
  }
}

/* ---------------- 主映射 ---------------- */

/**
 * 后端 Recipe（31 字段） → 前端食谱对象（页面只认这套）
 * @param {object} be           后端 recipe 对象
 * @param {array}  [ingredients] 详情接口才返回的配料数组
 */
export function toRecipe(be, ingredients) {
  const r = be || {}
  return {
    id: r.id,
    name: r.name || '未命名食谱',
    desc: r.description || '',

    // 枚举归一
    mealType: toMeal(r.category),
    cuisine: toCuisine(r.cuisineType),
    level: r.difficulty || '简单',
    fit: toFit(r.suitableFor),

    // 数值：后端是浮点，前端展示要整齐
    time: Number(r.cookingTime) || 20,
    servings: Number(r.servings) || 1,
    kcal: Math.round(Number(r.totalCalories) || 0),
    p: dec1(r.protein),
    c: dec1(r.carbs),
    f: dec1(r.fat),
    fiber: dec1(r.fiber),
    rating: dec1(r.score),

    // 这两个后端目前全是 0，如实显示
    views: Number(r.viewCount) || 0,
    collects: Number(r.collectCount) || 0,

    // 图片：后端 imageUrl 全为 null，一律给占位符；将来有图自动切换
    img: withFallbackImage(r.imageUrl),

    // 型转换
    steps: toSteps(r.instructions),
    tips: r.tips || '',
    ingredients: (ingredients || []).map(toIngredient),

    // 原始数据留着排查用，页面不使用
    _raw: r
  }
}

/* ---------------- 取数（带缓存） ---------------- */

/**
 * /recipe/list 是**全量、不带分页参数**的接口（193 条）。
 * 但页面 RecipesView 的 load() 是按分页循环拉的（最多 12 次）。
 * 所以这里缓存全量结果，12 次循环实际只打 1 次网络。
 */
let cache = null
let cacheAt = 0
const CACHE_TTL = 5 * 60 * 1000

/** 拉全部食谱（已映射成前端形状） */
export async function fetchAllRecipes({ force = false } = {}) {
  const now = Date.now()
  if (!force && cache && now - cacheAt < CACHE_TTL) {
    return { code: 200, message: 'ok', data: cache }
  }
  const res = await http.get('/recipe/list')
  if (res.code !== 200) return res
  const raw = Array.isArray(res.data) ? res.data : []
  cache = raw.filter((r) => r.status !== 0).map((r) => toRecipe(r))
  cacheAt = now
  return { code: 200, message: res.message, data: cache }
}

/** 拉食谱详情：后端返回 { recipe, ingredients }，这里拍平成前端要的单个对象 */
export async function fetchRecipeDetail(id) {
  const res = await http.get('/recipe/detail/' + id)
  if (res.code !== 200) return res
  const d = res.data || {}
  const be = d.recipe || d
  if (!be || be.id === undefined) {
    return { code: 404, message: '食谱不存在或已下架', data: null }
  }
  return { code: 200, message: res.message, data: toRecipe(be, d.ingredients) }
}

/**
 * 拉「我收藏的食谱」—— 后端 /recipe/collect/list 直接返回完整食谱数组
 * （已实测：收藏过 105 号，返回的是 31 字段的完整对象，不是 id 列表）。
 * 注意：这个接口**没有配料**，列表页用不到，不用管。
 */
export async function fetchCollectedRecipes() {
  const res = await http.get('/recipe/collect/list')
  if (res.code !== 200) return res
  const raw = Array.isArray(res.data) ? res.data : []
  return { code: 200, message: res.message, data: raw.map((r) => toRecipe(r)) }
}

/** 写操作后让缓存失效，下次 list 会重新拉 */
export function clearRecipeCache() {
  cache = null
  cacheAt = 0
}
