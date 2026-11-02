/* ============================================================
   services/adapters/ingredient.js · 食材字段适配层
   ------------------------------------------------------------
   后端实测（2026-11-02，GET /ingredient/list 共 125 条、
   POST /ingredient/nutrition、POST /ingredient/substitute）：

     1) 字段全带 Per100g 后缀，且改名
        前端       后端
        cat     ← category
        kcal    ← caloriesPer100g
        p       ← proteinPer100g
        c       ← carbsPer100g
        f       ← fatPer100g
        fiber   ← fiberPer100g
        sugar   ← sugarPer100g
        sodium  ← sodiumPer100g
        gi      ← giValue
        chol    ← cholesterolPer100g
        desc    ← description

     2) 后端多出前端没有的分类
        实测分布：蔬菜32 主食21 肉类19 水果17 豆制品9 乳制品9
                  坚果8 蛋类5 调味4 测试分类1
        前端 CATS = 全部/主食/蔬菜/肉类/蛋类/乳制品/水果/坚果/豆制品
        「调味」不在其中，「测试分类」是脏数据。
        → 分类筛选时把这二者归入「全部」兜底，不让它们凭空消失。
        （不擅自改页面上的分类按钮，那是产品决策。）

     3) nutrition 接口的 unit 参数**后端根本不读**
        calculateNutrition(id, quantity, unit) 里 unit 传进去但没用，
        2 碗米饭会被算成 2 克米饭（2/100 份）。
        → 前端只按「克」调用，单位一律传 g。

     4) nutrition 返回值是裸浮点
        实测 { fiber: 0.6000000000000001, carbs: 38.400000000000006 }
        直接渲染会出现一长串小数。
        → 统一保留一位小数，热量取整。

     5) ⚠️ /ingredient/substitute 是**硬编码假数据**
        实测无论传什么 ingredientName，都返回固定的
        [西兰花 similarity 0.9, 花椰菜 similarity 0.8]。
        而且返回结构是 [{name, similarity, reason}]，
        没有前端要的 kcal/p/f/tag（页面会渲染成空白/undefined）。
        → 本适配层把 similarity 映射成 tag，用食材库补齐营养值。
        但这依然是假数据，只适合演示，不能当真实推荐。
   ============================================================ */

/** 后端食材分类（实测存在但在前端 CATS 之外的） */
export const EXTRA_CATS = ['调味', '测试分类']

/** 保留一位小数，去掉浮点噪声 */
const dec1 = (v) => Math.round((Number(v) || 0) * 10) / 10
const int0 = (v) => Math.round(Number(v) || 0)

/**
 * 后端 Ingredient → 前端食材对象
 */
export function toIngredient(be) {
  const i = be || {}
  return {
    id: i.id,
    name: i.name || '未命名食材',
    cat: i.category || '其他',
    subCat: i.subCategory || '',
    kcal: int0(i.caloriesPer100g),
    p: dec1(i.proteinPer100g),
    c: dec1(i.carbsPer100g),
    f: dec1(i.fatPer100g),
    fiber: dec1(i.fiberPer100g),
    sugar: dec1(i.sugarPer100g),
    sodium: dec1(i.sodiumPer100g),
    gi: int0(i.giValue),
    chol: i.cholesterolPer100g == null ? null : dec1(i.cholesterolPer100g),
    desc: i.description || '',
    // 后端 imageUrl 全为 null，页面用 emoji/占位，不需要处理
    img: i.imageUrl || '',
    status: i.status,
    _raw: i
  }
}

/** 列表映射 + 过滤下架 */
export function toIngredientList(beList) {
  if (!Array.isArray(beList)) return []
  return beList.filter((x) => x && x.status !== 0).map(toIngredient)
}

/**
 * 前端筛选：分类 + 关键字
 * 和后端 mock 分支逻辑保持一致，方便对照。
 *
 * 注意「调味 / 测试分类」不在前端 CATS 里：
 * 选「全部」时它们要能出现（否则用户会发现库里 125 条只显示 120 条），
 * 所以这里不做剔除，只按分类精确匹配。
 */
export function filterIngredients(list, { cat, keyword } = {}) {
  let out = list
  if (cat && cat !== '全部') out = out.filter((i) => i.cat === cat)
  const kw = String(keyword || '').trim()
  if (kw) out = out.filter((i) => i.name.includes(kw) || i.cat.includes(kw))
  return out
}

/**
 * 前端计算请求 → 后端 POST /ingredient/nutrition 的参数
 * 后端 unit 无效，只按克算，这里固定传 g。
 */
export function toNutritionParams({ id, grams }) {
  const g = Math.max(1, Math.min(1000, Math.round(Number(grams) || 100)))
  return { ingredientId: String(id), quantity: g, unit: 'g' }
}

/**
 * 后端 nutrition 返回 → 前端预览结构
 * 后端：{ calories, protein, carbs, fat, fiber, sugar, sodium, gi }
 * 前端：{ name, grams, kcal, p, c, f }
 */
export function toNutrition(be, { name, grams } = {}) {
  const n = be || {}
  return {
    name: name || '',
    grams: Number(grams) || 100,
    kcal: int0(n.calories),
    p: dec1(n.protein),
    c: dec1(n.carbs),
    f: dec1(n.fat),
    fiber: dec1(n.fiber),
    sugar: dec1(n.sugar),
    sodium: dec1(n.sodium)
  }
}

/**
 * 替代建议映射。
 *
 * 【已修复 2026-11-02】后端 /ingredient/substitute 原先是硬编码假数据
 * （固定返回西兰花 / 花椰菜两条，ingredientName 参数完全没用）。
 * 现在后端按营养构成相似度真实计算，返回：
 *   { id, name, category, similarity, reason,
 *     calories, protein, carbs, fat, fiber, gi }
 *
 * 所以营养值直接用后端给的，不再需要从食材库补齐；
 * allIngredients 只作为兜底（例如后端旧版本没返回营养字段时）。
 */
export function toSubstitutes(beList, allIngredients, { source, prompt } = {}) {
  const pool = Array.isArray(allIngredients) ? allIngredients : []
  const dec1 = (v) => Math.round((Number(v) || 0) * 10) / 10
  const int0 = (v) => Math.round(Number(v) || 0)

  const list = (Array.isArray(beList) ? beList : []).map((s) => {
    const name = (s.name || '').trim()
    const found = pool.find((x) => x.name === name)
    // 后端是否给了营养字段（calories 存在即视为给了）
    const fromBE = s.calories !== undefined && s.calories !== null
    const hasData = fromBE || !!found

    const kcal = fromBE ? int0(s.calories) : found ? found.kcal : null
    const p = fromBE ? dec1(s.protein) : found ? found.p : null
    const c = fromBE ? dec1(s.carbs) : found ? found.c : null
    const f = fromBE ? dec1(s.fat) : found ? found.f : null

    const sim = Number(s.similarity)
    return {
      id: s.id,
      name: name || '未知食材',
      cat: s.category || (found ? found.cat : ''),
      hasData,
      kcal,
      p,
      c,
      f,
      fiber: fromBE ? dec1(s.fiber) : found ? found.fiber : null,
      gi: fromBE ? int0(s.gi) : found ? found.gi : null,
      reason: s.reason || '',
      tag: isFinite(sim) && sim > 0 ? '相似度 ' + Math.round(sim * 100) + '%' : '替代'
    }
  })
  return { source: source || '', prompt: prompt || '', list }
}
