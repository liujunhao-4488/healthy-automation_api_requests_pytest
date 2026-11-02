/* ============================================================
   services/adapters/record.js · 饮食记录字段适配层
   ------------------------------------------------------------
   后端实测（2026-11-02，POST /record/submit、GET /record/list）
   与前端 RecordView 的差异，全部在这里吸收：

     1) 入参结构是 details[]，且**键名和前端完全不同**
        前端 items: [{ name, amount, unit, kcal, p, c, f }]
        后端 details: [{ foodName, amount, unit, calories,
                         protein, carbs, fat, ingredientId, recipeId }]

        ⚠️ 特别注意份量：后端 buildDetails 读的键是 **amount**，
        但写进实体的是 setQuantity()。也就是说
        「传 amount、收 quantity」，收发两头的键名不一样。
        早先按字段名（quantity）发过去，后端收不到，会走默认值 1.0，
        实测表现为记录里出现「燕麦片 1g」这种错误份量。

     2) 后端所有数值字段都用 Double.parseDouble(toString())
        传数字本身没问题，但传 '' 或 undefined 会抛 NumberFormatException。
        → 数字原样发，空值不发该键。

     3) 明细的 fiber / sugar / sodium / gi
        【已修复 2026-11-02】原本 DietRecordDetail 实体上这四字段标了
        @TableField(exist = false)，MyBatis-Plus 插入时直接跳过，
        实测提交 fiber=7.77 后重新 GET 回来一律 0.0。
        后端已补上数据库列并去掉注解，现在会正常落库。
        → 前端照常发送这些字段即可，不再需要规避。

     4) recordDate 回来是 "2026-11-02 00:00:00"
        前端要的是 "2026-11-02"。直接 slice(0,10)。

     5) 后端没有 time 字段
        前端按 time 排序与展示。后端有 createTime（真实提交时间），
        用它截出 HH:mm 顶上；拿不到就按 mealType 给个合理默认。

     6) /record/list 是**按时间倒序 + 分页**的
        前端 recordsByDate 要的是某一天的全部记录，
        → 调用时用 startDate=endDate=当天，并给足够大的 pageSize。

     7) 删除是软删除，DELETE /record/{recordId}
        mealType 前端四餐：早餐/午餐/晚餐/加餐，后端存字符串，原样用。
   ============================================================ */

/** 前端 → 后端：餐次。后端 mealType 是自由的字符串，直接沿用中文即可 */
const MEALS = ['早餐', '午餐', '晚餐', '加餐']

/** 后端没给时间时，按餐次给一个合理的默认时间 */
const MEAL_DEFAULT_TIME = { 早餐: '08:00', 午餐: '12:30', 晚餐: '18:30', 加餐: '15:30' }

/** "2026-11-02 00:00:00" / "2026-11-02T16:19:05" → "2026-11-02" */
export function toDateOnly(v) {
  const s = String(v || '').trim()
  if (!s) return ''
  return s.slice(0, 10)
}

/** "2026-11-02T16:19:05" → "16:19" */
function toClock(v) {
  const s = String(v || '').replace('T', ' ')
  const m = s.match(/\s(\d{2}):(\d{2})/)
  return m ? m[1] + ':' + m[2] : ''
}

/** 安全数字：后端 Double.parseDouble 不接受空串 */
function numOrNull(v) {
  if (v === undefined || v === null || v === '') return null
  const n = Number(v)
  return isFinite(n) ? n : null
}

/** 保留一位小数，避免浮点噪声（303.00000001 这种） */
const dec1 = (v) => Math.round((Number(v) || 0) * 10) / 10

/* ============================================================
   入参：前端表单 → 后端 details[]
   ============================================================ */

/**
 * 前端一条食材 → 后端 detail 对象
 * 键名必须与后端 buildDetails 读取的一致（注意份量是 amount 不是 quantity）。
 * fiber / sugar / sodium / gi 后端已支持落库，有值就一起发。
 */
export function toDetailDTO(item) {
  const d = {}
  d.foodName = String(item.name || '').trim()
  const amount = numOrNull(item.amount)
  // 键名必须是 amount：后端 setQuantity(get("amount"))，传 quantity 会被忽略并落成 1.0
  if (amount !== null) d.amount = amount
  d.unit = item.unit || 'g'
  const kcal = numOrNull(item.kcal)
  if (kcal !== null) d.calories = kcal
  const p = numOrNull(item.p)
  if (p !== null) d.protein = p
  const c = numOrNull(item.c)
  if (c !== null) d.carbs = c
  const f = numOrNull(item.f)
  if (f !== null) d.fat = f
  // 这四项后端 2026-11-02 起已支持落库（原先 exist=false 被丢弃）
  const fiber = numOrNull(item.fiber)
  if (fiber !== null) d.fiber = fiber
  const sugar = numOrNull(item.sugar)
  if (sugar !== null) d.sugar = sugar
  const sodium = numOrNull(item.sodium)
  if (sodium !== null) d.sodium = sodium
  const gi = numOrNull(item.gi)
  if (gi !== null) d.gi = gi
  // 有食材库 id 就带上，后端会用库里的营养值校正
  if (item.ingredientId != null && item.ingredientId !== '') {
    d.ingredientId = String(item.ingredientId)
  }
  if (item.recipeId != null && item.recipeId !== '') {
    d.recipeId = String(item.recipeId)
  }
  return d
}

/**
 * 前端 submit 参数 → 后端 POST /record/submit 的 body
 * @param {{date, mealType, note, items}} rec
 */
export function toSubmitDTO(rec) {
  const r = rec || {}
  const body = {
    // 后端按 yyyy-MM-dd 解析，格式不对会抛「日期格式错误」
    date: toDateOnly(r.date) || undefined,
    mealType: MEALS.includes(r.mealType) ? r.mealType : r.mealType || '早餐',
    details: (r.items || []).map(toDetailDTO),
    // 注意：后端读的键是 notes，不是 note
    notes: r.note || ''
  }
  if (!body.date) delete body.date
  return body
}

/* ============================================================
   出参：后端 DietRecord → 前端 record
   ============================================================ */

/** 后端 detail → 前端 item */
function toItem(be) {
  const d = be || {}
  return {
    id: d.id,
    name: d.foodName || '食材',
    amount: Number(d.quantity) > 0 ? Number(d.quantity) : 1,
    unit: d.unit || 'g',
    kcal: dec1(d.calories),
    p: dec1(d.protein),
    c: dec1(d.carbs),
    f: dec1(d.fat),
    // 后端已支持落库，正常返回；老数据可能为 null，dec1 会归成 0
    fiber: dec1(d.fiber),
    sugar: dec1(d.sugar),
    sodium: dec1(d.sodium),
    gi: dec1(d.gi)
  }
}

/**
 * 后端 DietRecord → 前端 record
 * 前端形状：{ id, date, time, mealType, note, items[], kcal, p, c, f }
 */
export function toRecord(be) {
  const r = be || {}
  const items = (r.details || []).map(toItem)
  const mealType = MEALS.includes(r.mealType) ? r.mealType : r.mealType || '加餐'

  // 优先用后端 createTime 的时分，其次按餐次兜底
  const time = toClock(r.createTime) || MEAL_DEFAULT_TIME[mealType] || '12:00'

  return {
    id: r.id,
    date: toDateOnly(r.recordDate),
    time,
    mealType,
    note: r.notes || '',
    items,
    // 明细里没有 quantity 时，用后端汇总值兜底，保证卡片上的热量不显示 0
    kcal: items.length
      ? Math.round(items.reduce((s, i) => s + (+i.kcal || 0), 0))
      : Math.round(Number(r.totalCalories) || 0),
    p: items.length ? dec1(items.reduce((s, i) => s + (+i.p || 0), 0)) : dec1(r.totalProtein),
    c: items.length ? dec1(items.reduce((s, i) => s + (+i.c || 0), 0)) : dec1(r.totalCarbs),
    f: items.length ? dec1(items.reduce((s, i) => s + (+i.f || 0), 0)) : dec1(r.totalFat),
    _raw: r
  }
}

/** 列表映射 —— 自动过滤软删除 */
export function toRecordList(beList) {
  if (!Array.isArray(beList)) return []
  return beList.filter((r) => r && r.isDeleted !== 1).map(toRecord)
}

/* ============================================================
   趋势：/record/analysis/trend → 图表数据
   ============================================================ */

/**
 * 实测返回：
 * { totalCarbs, totalFat, totalProtein, totalCalories, recordCount,
 *   dailyStats: { "2026-11-02": { calories, protein, carbs, fat, ... } } }
 *
 * 前端图表要的是按日期升序的 [{ date:'11-02', kcal, p, c, f }]，
 * 且缺的日子要补 0，否则折线会错位。
 */
export function toTrend(be, { days = 7 } = {}) {
  const daily = (be && be.dailyStats) || {}

  // 以「今天」为终点往前推，后端没数据的日子补 0
  const out = []
  const today = new Date()
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    const p = (x) => String(x).padStart(2, '0')
    const key = d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate())
    const s = daily[key] || {}
    out.push({
      date: p(d.getMonth() + 1) + '-' + p(d.getDate()),
      fullDate: key,
      kcal: Math.round(Number(s.calories) || 0),
      p: dec1(s.protein),
      c: dec1(s.carbs),
      f: dec1(s.fat)
    })
  }
  return out
}

/** 近 7 天的起止日期（后端这两个参数都是 @RequestParam 必填） */
export function last7Days() {
  const p = (x) => String(x).padStart(2, '0')
  const fmt = (d) => d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate())
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 6)
  return { startDate: fmt(start), endDate: fmt(end) }
}
