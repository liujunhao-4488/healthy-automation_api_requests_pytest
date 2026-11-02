/* ============================================================
   services/adapters/health.js · 健康档案 / 饮食目标 字段适配层
   ------------------------------------------------------------
   和 adapters/recipe.js 同一个理由：后端契约和前端页面是两套字段名。

   后端实测（2026-11-02，GET/POST /health/info、/health/goal）的坑：

     1) gender 只收 male / female
        HealthInfoDTO 上挂着 @Pattern(regexp="male|female")，
        前端页面按钮上写的是「男 / 女」。直接透传必然 400
        （实测报错：性别取值不合法，只能是 male 或 female）。
        → 出参转中文给页面，入参转英文给后端。

     2) 必填项和前端校验范围不一致
        后端 @NotNull：age / gender / height / weight，且 goal 的
        goalType / targetCalories / startDate 也必填（实测 startDate
        为空直接 400「开始日期不能为空」）。
        → 转换时补齐默认值，不能把 undefined 发过去。

     3) 新用户 data 为 null
        /health/info 和 /health/goal 在用户还没建档时返回 data:null，
        而页面拿 health.value.bmi 直接做 Number(...).toFixed(1)，
        null 会炸成 "NaN" 甚至运行时报错。
        → 这里统一补成前端完整形状的默认对象。

     4) bmr 后端不计算，恒为 null
        bmi 后端会算（weight / (height/100)^2），bmr 不会。
        → bmi 用后端的，bmr 在前端按 Mifflin-St Jeor 自己算。

     5) /health/info 的 analysis 在**信封外面**
        形状是 { code, data, message, analysis }，不是 data.analysis。
        → 单独从 res.analysis 取，别去 data 里找。

     6) 字段改名对照
        前端           后端
        activity    → activityLevel
        exerciseMin → exerciseDuration
        chronic[]   → chronicDiseases（顿号/逗号分隔的字符串）
        waist       → 后端没有这个字段，存本地
        kcal        → targetCalories
        proteinPct  → proteinRatio
        carbPct     → carbsRatio   （注意是 carbs，多了个 s）
        fatPct      → fatRatio
        water       → waterTarget
        startDate   → startDate / endDate（后端必填）
   ============================================================ */

/** 后端 → 前端：性别 */
const GENDER_TO_CN = { male: '男', female: '女' }
/** 前端 → 后端：性别 */
const GENDER_TO_BE = { 男: 'male', 女: 'female' }

/** 列表 ↔ 顿号字符串（后端 chronicDiseases 是 "高血脂、高血压" 这种） */
function arrToStr(v) {
  if (Array.isArray(v)) return v.filter(Boolean).join('、')
  return v == null ? '' : String(v)
}
function strToArr(v) {
  if (Array.isArray(v)) return v.filter(Boolean)
  const s = String(v || '').trim()
  return s ? s.split(/[、,，;；\s]+/).filter(Boolean) : []
}

/** 前后端都缺省时给数值兜底，别把 undefined 塞进去算 */
const num = (v, d) => {
  const n = Number(v)
  return isFinite(n) && n > 0 ? n : d
}

/** 后端时间串 "2026-11-02T16:04:19.468" / "2026-11-02 16:04:19" → "2026-11-02 16:04" */
function fmtTime(v) {
  if (!v) return ''
  const s = String(v).replace('T', ' ')
  return s.slice(0, 16)
}

/** 今天，YYYY-MM-DD（后端 LocalDate 要这个格式） */
export function todayISO() {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate())
}

/** 今天往后推 n 个月，YYYY-MM-DD */
function plusMonths(n) {
  const d = new Date()
  d.setMonth(d.getMonth() + n)
  const p = (x) => String(x).padStart(2, '0')
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate())
}

/**
 * BMR（Mifflin-St Jeor）。后端不返回 bmr，前端必须自己算，
 * 否则 HealthView 的 kpi.bmr 会显示 NaN。
 */
function calcBmr({ weight, height, age, gender }) {
  const w = Number(weight)
  const h = Number(height)
  const a = Number(age)
  if (!(w > 0 && h > 0 && a > 0)) return 0
  return Math.round(10 * w + 6.25 * h - 5 * a + (gender === '男' ? 5 : -161))
}

/* ============================================================
   健康档案
   ============================================================ */

/**
 * 前端完整形状的健康档案默认值。
 * 新用户后端返回 null 时用它，保证页面所有字段都有值。
 */
export function emptyHealth() {
  return {
    age: 29,
    gender: '男',
    height: 170,
    weight: 65,
    bmi: 22.5,
    bmr: 1600,
    bloodPressure: '120/80',
    bloodSugar: 5.0,
    activity: '轻度活动',
    exerciseMin: 30,
    exerciseType: '',
    chronic: [],
    waist: 80,
    updatedAt: ''
  }
}

/**
 * 后端 HealthInfo → 前端 healthInfo
 * @param {object} be  后端 data（可能为 null）
 * @param {object} [local] 本地缓存，用来补后端没有的字段（waist / updatedAt）
 */
export function toHealthInfo(be, local) {
  const base = Object.assign(emptyHealth(), local || {})
  if (!be || typeof be !== 'object') return base

  const height = num(be.height, base.height)
  const weight = num(be.weight, base.weight)
  const age = num(be.age, base.age)
  const gender = GENDER_TO_CN[be.gender] || base.gender

  return {
    age,
    gender,
    height,
    weight,
    // 后端会算 bmi，用它；没有就本地算
    bmi: Number(be.bmi) > 0 ? Number(be.bmi) : +(weight / Math.pow(height / 100, 2)).toFixed(1),
    // 后端恒为 null，本地算
    bmr: Number(be.bmr) > 0 ? Number(be.bmr) : calcBmr({ weight, height, age, gender }),
    bloodPressure: be.bloodPressure || base.bloodPressure,
    bloodSugar: num(be.bloodSugar, base.bloodSugar),
    activity: be.activityLevel || base.activity,
    exerciseMin: Number(be.exerciseDuration) >= 0 ? Number(be.exerciseDuration) : base.exerciseMin,
    exerciseType: be.exerciseType || '',
    chronic: strToArr(be.chronicDiseases),
    // 后端没有 waist 字段，沿用本地
    waist: num(base.waist, 80),
    updatedAt: fmtTime(be.updateTime) || base.updatedAt || ''
  }
}

/**
 * 前端表单 → 后端 HealthInfoDTO
 * 注意 gender 必须翻译成 male/female，否则 400。
 */
export function toHealthDTO(front) {
  const f = front || {}
  return {
    // 后端 @NotNull
    age: Math.round(num(f.age, 29)),
    gender: GENDER_TO_BE[f.gender] || 'male',
    height: num(f.height, 170),
    weight: num(f.weight, 65),
    // 下面都可空
    bloodPressure: f.bloodPressure || '',
    bloodSugar: num(f.bloodSugar, 0) || null,
    activityLevel: f.activity || '',
    exerciseDuration: Number(f.exerciseMin) >= 0 ? Math.round(Number(f.exerciseMin)) : 0,
    exerciseType: f.exerciseType || '',
    chronicDiseases: arrToStr(f.chronic)
  }
}

/**
 * 后端 /health/history → 图表要的 [{ date, weight }]
 * 实测形状：{ id, userId, weight, bmi, exerciseDuration, recordDate, createTime }
 * 页面图表用的是 p.date 和 p.weight，所以这里改名并格式化日期。
 */
export function toHistoryList(beList) {
  if (!Array.isArray(beList)) return []
  return beList
    .filter((x) => x && Number(x.weight) > 0)
    .map((x) => ({
      // 图表 x 轴只放「月-日」，和 mock 的 '09-01' 一致
      date: String(x.recordDate || '').slice(5) || String(x.createTime || '').slice(5, 10),
      weight: Number(x.weight),
      bmi: Number(x.bmi) || 0
    }))
    .reverse() // 后端按时间倒序，图表要正序
}

/* ============================================================
   饮食目标
   ============================================================ */

/**
 * 前端完整形状的饮食目标默认值（新用户后端返回 null 时用）
 */
export function emptyGoal() {
  return {
    goalType: '减脂',
    startWeight: 0,
    currentWeight: 0,
    targetWeight: 62,
    kcal: 1800,
    proteinPct: 30,
    carbPct: 45,
    fatPct: 25,
    water: 2000,
    meals: 3,
    snack: true,
    startDate: todayISO(),
    endDate: plusMonths(3),
    status: 1,
    reminderEnabled: true,
    reminderTime: '07:30'
  }
}

/**
 * 后端 DietGoal → 前端 goalInfo
 */
export function toGoalInfo(be, local) {
  const base = Object.assign(emptyGoal(), local || {})
  if (!be || typeof be !== 'object') return base

  return {
    goalType: be.goalType || base.goalType,
    startWeight: num(base.startWeight, 0),
    currentWeight: num(base.currentWeight, 0),
    targetWeight: num(be.targetWeight, base.targetWeight),
    kcal: Math.round(num(be.targetCalories, base.kcal)),
    proteinPct: num(be.proteinRatio, base.proteinPct),
    carbPct: num(be.carbsRatio, base.carbPct), // 后端是 carbsRatio
    fatPct: num(be.fatRatio, base.fatPct),
    water: num(be.waterTarget, base.water),
    // 后端没有 meals / snack，沿用本地
    meals: num(base.meals, 3),
    snack: base.snack !== false,
    // 后端必填，读回来原样用
    startDate: be.startDate || base.startDate,
    endDate: be.endDate || base.endDate,
    status: be.status == null ? 1 : be.status,
    reminderEnabled: be.reminderEnabled == null ? true : !!be.reminderEnabled,
    reminderTime: be.reminderTime ? String(be.reminderTime).slice(0, 5) : base.reminderTime
  }
}

/**
 * 前端表单 → 后端 DietGoalDTO
 *
 * 三个必填（实测缺 startDate 会 400「开始日期不能为空」）：
 *   goalType / targetCalories / startDate
 * 营养目标克数后端可空，但填了更完整，这里按热量 × 占比算出来一起发。
 */
export function toGoalDTO(front) {
  const f = front || {}
  const kcal = Math.round(num(f.kcal, 1800))
  const pp = num(f.proteinPct, 30)
  const cp = num(f.carbPct, 45)
  const fp = num(f.fatPct, 25)

  // 结束日期：还没设置就默认 3 个月后，后端接受 null 但给了更好
  const startDate = f.startDate || todayISO()
  const endDate = f.endDate || plusMonths(3)

  return {
    goalType: f.goalType || '维持', // @NotBlank
    targetCalories: kcal, // @NotNull
    startDate, // @NotNull
    endDate,
    targetWeight: num(f.targetWeight, 0) || null,
    // 后端是 percentage 数值：30 / 45 / 25
    proteinRatio: pp,
    carbsRatio: cp,
    fatRatio: fp,
    // 克数换算：蛋白/碳水 4 kcal/g，脂肪 9 kcal/g
    proteinTarget: Math.round((kcal * pp) / 100 / 4),
    carbsTarget: Math.round((kcal * cp) / 100 / 4),
    fatTarget: Math.round((kcal * fp) / 100 / 9),
    waterTarget: Math.round(num(f.water, 2000)),
    reminderEnabled: f.reminderEnabled ? 1 : 0,
    reminderTime: /^\d{2}:\d{2}/.test(String(f.reminderTime || ''))
      ? String(f.reminderTime).slice(0, 5) + ':00'
      : null
  }
}
