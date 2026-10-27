<script setup>
/* ============================================================
   HealthView.vue · 健康档案
   ------------------------------------------------------------
   对应静态版 pages/health.html。
   静态版要手动 querySelector + 改 className，这里全部交给模板：
   KPI 徽标文案、BMI 指针位置、体重折线图坐标都由 computed 算好。
   ============================================================ */
import { ref, reactive, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { healthApi } from '@/services/api'
import { toast } from '@/composables/useToast'
import SvgIcon from '@/components/SvgIcon.vue'

const store = useAppStore()

/* ---------------- 可选项常量 ---------------- */
const DIET = ['清淡', '低脂', '高蛋白', '低GI', '低碳水', '地中海', '素食']
const ALLERGENS = ['花生', '海鲜', '乳糖', '麸质', '鸡蛋', '大豆']
const DISLIKES = ['香菜', '动物内脏', '洋葱', '苦瓜', '芹菜', '肥肉']
const LIKES = ['鸡胸肉', '三文鱼', '蓝莓', '燕麦', '西兰花', '北豆腐']
const CHRONIC = ['高血脂', '高血压', '糖尿病', '高尿酸', '脂肪肝']
const ACTIVITIES = ['久坐', '轻度活动', '中度活动', '高强度']

/* ---------------- 表单状态 ---------------- */
const health = computed(() => store.healthInfo)

const form = reactive({
  gender: health.value.gender,
  age: health.value.age,
  height: health.value.height,
  weight: health.value.weight,
  waist: health.value.waist,
  activity: health.value.activity,
  exerciseMin: health.value.exerciseMin,
  exerciseType: health.value.exerciseType || ''
})
const chronic = ref((health.value.chronic || []).slice())

/** 字段级错误，对应原来的 .has-error */
const errs = reactive({
  age: false,
  height: false,
  weight: false,
  waist: false,
  exerciseMin: false
})
const saving = ref(false)

/* ---------------- KPI 派生值 ---------------- */
function bmiBadge(bmi) {
  if (bmi < 18.5) return { text: '偏低', cls: 'badge gray' }
  if (bmi < 24) return { text: '正常', cls: 'badge' }
  return { text: '偏高', cls: 'badge amber' }
}
/** 把 BMI 映射到刻度条上的百分比位置 */
function bmiPos(bmi) {
  const segs = [
    [15, 18.5, 0, 20],
    [18.5, 24, 20, 30],
    [24, 28, 50, 30],
    [28, 35, 80, 20]
  ]
  const b = Math.max(15, Math.min(35, bmi))
  for (let i = 0; i < segs.length; i++) {
    const s = segs[i]
    if (b <= s[1] || i === segs.length - 1) {
      const f = Math.max(0, Math.min(1, (b - s[0]) / (s[1] - s[0])))
      return (s[2] + f * s[3]).toFixed(2)
    }
  }
  return '0'
}
function bpBadge(bp) {
  const parts = String(bp).split('/').map(Number)
  const sys = parts[0] || 0
  const dia = parts[1] || 0
  if (sys < 120 && dia < 80) return { text: '正常', cls: 'badge' }
  if (sys < 140 && dia < 90) return { text: '正常高值', cls: 'badge amber' }
  return { text: '偏高', cls: 'badge clay' }
}
function sugarBadge(v) {
  if (v < 3.9) return { text: '偏低', cls: 'badge clay' }
  if (v <= 6.1) return { text: '正常', cls: 'badge' }
  return { text: '偏高', cls: 'badge amber' }
}

const kpi = computed(() => {
  const h = health.value
  const bmrOk = h.bmr >= 1000 && h.bmr <= 2000
  return {
    sub: '最近更新 ' + h.updatedAt + ' · 档案数据用于生成推荐与营养目标',
    bmi: Number(h.bmi).toFixed(1),
    bmiBadge: bmiBadge(h.bmi),
    bmiPos: bmiPos(h.bmi) + '%',
    bmiFoot: '身高 ' + h.height + 'cm · 体重 ' + h.weight + 'kg',
    bmr: Number(h.bmr).toLocaleString('zh-CN'),
    bmrBadge: bmrOk ? { text: '正常范围', cls: 'badge' } : { text: '需关注', cls: 'badge amber' },
    bp: h.bloodPressure,
    bpBadge: bpBadge(h.bloodPressure),
    sugar: Number(h.bloodSugar).toFixed(1),
    sugarBadge: sugarBadge(h.bloodSugar)
  }
})

/* ---------------- chips 多选 ---------------- */
function toggleInList(listRef, val) {
  const list = listRef.value.slice()
  const i = list.indexOf(val)
  if (i > -1) list.splice(i, 1)
  else list.push(val)
  listRef.value = list
}

/* ---------------- 保存身体数据 ---------------- */
function setErr(key, on) {
  errs[key] = !!on
}

async function saveHealth() {
  const invalid = []
  if (!(form.height >= 120 && form.height <= 220)) {
    setErr('height', true)
    invalid.push('身高')
  } else setErr('height', false)
  if (!(form.weight >= 30 && form.weight <= 200)) {
    setErr('weight', true)
    invalid.push('体重')
  } else setErr('weight', false)
  if (!(form.age >= 18 && form.age <= 90)) {
    setErr('age', true)
    invalid.push('年龄')
  } else setErr('age', false)
  if (!(form.waist >= 50 && form.waist <= 150)) {
    setErr('waist', true)
    invalid.push('腰围')
  } else setErr('waist', false)
  if (!(form.exerciseMin >= 0 && form.exerciseMin <= 300)) {
    setErr('exerciseMin', true)
    invalid.push('运动时长')
  } else setErr('exerciseMin', false)

  if (invalid.length) {
    toast(invalid.join('、') + '填写有误，请检查标注字段', 'error')
    return
  }

  saving.value = true
  const res = await healthApi.save({
    gender: form.gender,
    age: +form.age,
    height: +form.height,
    weight: +form.weight,
    waist: +form.waist,
    activity: form.activity,
    exerciseMin: +form.exerciseMin,
    exerciseType: form.exerciseType.trim(),
    chronic: chronic.value
  })
  saving.value = false
  if (res.code !== 200) {
    toast(res.message, 'error')
    return
  }
  toast(res.message || '健康档案已保存')
}

/* ---------------- 体重趋势图 ---------------- */
const history = ref([])
const chartLoading = ref(true)

async function loadHistory() {
  chartLoading.value = true
  const res = await healthApi.history()
  chartLoading.value = false
  if (res.code === 200 && res.data && res.data.length) history.value = res.data
}
loadHistory()

/**
 * 把体重数据算成 SVG 的网格线、折线路径、圆点、坐标标签。
 * 算法与静态版 renderChart() 完全一致，只是从「拼字符串」改成「算对象」。
 */
const chart = computed(() => {
  const points = history.value
  if (!points.length) return null

  const W = 340
  const H = 214
  const pl = 38
  const pr = 16
  const pt = 18
  const pb = 34
  const iw = W - pl - pr
  const ih = H - pt - pb

  const weights = points.map((p) => p.weight)
  let min = Math.floor(Math.min(...weights) - 1)
  let max = Math.ceil(Math.max(...weights) + 1)
  if (max - min < 4) max = min + 4

  const x = (i) => pl + (points.length === 1 ? iw / 2 : (i * iw) / (points.length - 1))
  const y = (v) => pt + ((max - v) / (max - min)) * ih

  // 4 条横向网格线 + 左侧刻度
  const grid = []
  for (let i = 0; i <= 4; i++) {
    const val = min + ((max - min) * i) / 4
    const yy = y(val)
    grid.push({ y: yy.toFixed(1), label: val.toFixed(1), labelY: (yy + 3).toFixed(1) })
  }

  const coords = points.map((p, i) => [x(i), y(p.weight)])
  const line = 'M' + coords.map((c) => c[0].toFixed(1) + ' ' + c[1].toFixed(1)).join(' L')
  const bottom = (pt + ih).toFixed(1)
  const area =
    line +
    ' L' + coords[coords.length - 1][0].toFixed(1) + ' ' + bottom +
    ' L' + coords[0][0].toFixed(1) + ' ' + bottom + ' Z'

  const dots = points.map((p, i) => ({
    cx: coords[i][0].toFixed(1),
    cy: coords[i][1].toFixed(1),
    r: i === points.length - 1 ? 4 : 3,
    last: i === points.length - 1,
    title: p.date + ' · ' + p.weight + 'kg',
    labelX: coords[i][0].toFixed(1),
    label: p.date
  }))

  const lastC = coords[coords.length - 1]
  return {
    W,
    H,
    pl,
    pr,
    labelY: H - 12,
    grid,
    line,
    area,
    dots,
    valueLabel: {
      x: (lastC[0] - 8).toFixed(1),
      y: (lastC[1] - 10).toFixed(1),
      text: points[points.length - 1].weight.toFixed(1) + ' kg'
    }
  }
})

/* ---------------- 目标提示 ---------------- */
const targetNote = computed(() => {
  const g = store.goalInfo
  const diff = +(g.currentWeight - g.targetWeight).toFixed(1)
  if (diff <= 0) {
    return '目标体重 ' + g.targetWeight.toFixed(1) + ' kg · 当前已达到目标，注意保持即可。'
  }
  const weeks = Math.ceil(diff / 0.5)
  return (
    '目标体重 ' + g.targetWeight.toFixed(1) + ' kg · 距当前还需减 ' +
    diff + ' kg，按每周 0.5kg 估算约 ' + weeks + ' 周。'
  )
})

/* ---------------- 饮食偏好 ---------------- */
const prefs = reactive({
  dietType: (store.preferences.dietType || []).slice(),
  allergens: (store.preferences.allergens || []).slice(),
  dislikes: (store.preferences.dislikes || []).slice(),
  likes: (store.preferences.likes || []).slice()
})
const prefSaving = ref(false)

const prefGroups = [
  { key: 'dietType', label: '饮食类型（可多选）', options: DIET },
  { key: 'allergens', label: '过敏原（推荐中硬性排除）', options: ALLERGENS },
  { key: 'dislikes', label: '不喜食材', options: DISLIKES },
  { key: 'likes', label: '常吃食材', options: LIKES }
]

function togglePref(key, val) {
  const list = prefs[key].slice()
  const i = list.indexOf(val)
  if (i > -1) list.splice(i, 1)
  else list.push(val)
  prefs[key] = list
}

function savePref() {
  prefSaving.value = true
  store.savePreferences({
    dietType: prefs.dietType,
    allergens: prefs.allergens,
    dislikes: prefs.dislikes,
    likes: prefs.likes
  })
  setTimeout(() => {
    prefSaving.value = false
    toast('饮食偏好已保存，下次推荐将按新偏好过滤')
  }, 480)
}

/* ---------------- 滚到表单 ---------------- */
const bodyCard = ref(null)
const ageInput = ref(null)
function onEditProfile() {
  bodyCard.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  setTimeout(() => ageInput.value?.focus(), 380)
}

onMounted(() => {
  // 进页面时从 store 同步一次（localStorage 里的值优先）
  const h = health.value
  Object.assign(form, {
    gender: h.gender,
    age: h.age,
    height: h.height,
    weight: h.weight,
    waist: h.waist,
    activity: h.activity,
    exerciseMin: h.exerciseMin,
    exerciseType: h.exerciseType || ''
  })
})
</script>

<template>
  <header class="page-head reveal">
    <div>
      <p class="eyebrow">Health Profile</p>
      <h1 class="page-title">健康档案</h1>
      <p class="page-sub">{{ kpi.sub }}</p>
    </div>
    <div class="page-actions">
      <button class="btn btn-outline" @click="onEditProfile">
        <SvgIcon name="edit" />更新档案
      </button>
      <RouterLink class="btn btn-primary" to="/goal">
        <SvgIcon name="target" />饮食目标
      </RouterLink>
    </div>
  </header>

  <section class="grid g4 reveal d1">
    <article class="card card-pad kpi">
      <div class="row-between" style="align-items: flex-start">
        <span class="kpi-label">BMI · 身体质量指数</span>
        <span :class="kpi.bmiBadge.cls">{{ kpi.bmiBadge.text }}</span>
      </div>
      <span class="kpi-value">{{ kpi.bmi }}</span>
      <div class="bmi-scale">
        <i /><i /><i /><i />
        <span class="bmi-marker" :style="{ left: kpi.bmiPos }" />
      </div>
      <p class="kpi-foot">{{ kpi.bmiFoot }}</p>
    </article>

    <article class="card card-pad kpi">
      <div class="row-between" style="align-items: flex-start">
        <span class="kpi-label">基础代谢 BMR</span>
        <span :class="kpi.bmrBadge.cls">{{ kpi.bmrBadge.text }}</span>
      </div>
      <span class="kpi-value">
        {{ kpi.bmr }}
        <span class="small muted" style="font-family: var(--font-body)">kcal</span>
      </span>
      <p class="kpi-foot">Mifflin-St Jeor 公式估算 · 静息状态每日消耗</p>
    </article>

    <article class="card card-pad kpi">
      <div class="row-between" style="align-items: flex-start">
        <span class="kpi-label">血压</span>
        <span :class="kpi.bpBadge.cls">{{ kpi.bpBadge.text }}</span>
      </div>
      <span class="kpi-value">
        {{ kpi.bp }}
        <span class="small muted" style="font-family: var(--font-body)">mmHg</span>
      </span>
      <p class="kpi-foot">参考范围 &lt;120/80 mmHg · 建议每周固定时间测量</p>
    </article>

    <article class="card card-pad kpi">
      <div class="row-between" style="align-items: flex-start">
        <span class="kpi-label">空腹血糖</span>
        <span :class="kpi.sugarBadge.cls">{{ kpi.sugarBadge.text }}</span>
      </div>
      <span class="kpi-value">
        {{ kpi.sugar }}
        <span class="small muted" style="font-family: var(--font-body)">mmol/L</span>
      </span>
      <p class="kpi-foot">参考 3.9–6.1 mmol/L · 空腹 8 小时以上测量</p>
    </article>
  </section>

  <section class="mt-24 reveal d2">
    <div class="alert-inline">
      <SvgIcon name="alert" />
      <div class="grow">
        <strong>风险提示 · 血脂偏高</strong>
        <p class="small" style="margin-top: 4px">
          档案记录「高血脂」，推荐引擎已按低饱和脂肪规则调整。优先执行以下两条饮食调整：
        </p>
        <ul class="risk-list small">
          <li>1. 每日烹调油控制在 25g 以内，用橄榄油或菜籽油替代动物油，少吃肥肉与奶油点心。</li>
          <li>2. 每周安排 2 次深海鱼（如三文鱼 150g），主食一半换成燕麦、糙米或杂豆。</li>
        </ul>
        <RouterLink
          to="/knowledge/2"
          style="color: inherit; font-weight: 600; display: inline-flex; align-items: center; gap: 4px; margin-top: 6px"
        >
          查看《高血脂人群的饮食清单》
          <SvgIcon name="arrow-right" style="width: 14px; height: 14px" />
        </RouterLink>
      </div>
    </div>
  </section>

  <section class="grid split mt-24 reveal d2">
    <article ref="bodyCard" class="card">
      <div class="card-hd">
        <h3>身体数据</h3>
        <span class="small muted">用于计算 BMI / BMR 与营养目标</span>
      </div>
      <div class="card-bd">
        <div class="form-grid">
          <div class="field">
            <label>性别</label>
            <div class="seg">
              <button
                v-for="g in ['女', '男']"
                :key="g"
                type="button"
                :class="{ on: form.gender === g }"
                @click="form.gender = g"
              >
                {{ g }}
              </button>
            </div>
          </div>
          <div class="field" :class="{ 'has-error': errs.age }">
            <label>年龄（岁）</label>
            <input
              ref="ageInput"
              v-model="form.age"
              class="input num"
              type="number"
              min="18"
              max="90"
              step="1"
            />
            <p class="field-error">年龄需在 18–90 岁之间</p>
          </div>
          <div class="field" :class="{ 'has-error': errs.height }">
            <label>身高（cm）</label>
            <input v-model="form.height" class="input num" type="number" min="120" max="220" step="0.1" />
            <p class="field-error">身高需在 120–220cm 之间</p>
          </div>
          <div class="field" :class="{ 'has-error': errs.weight }">
            <label>体重（kg）</label>
            <input v-model="form.weight" class="input num" type="number" min="30" max="200" step="0.1" />
            <p class="field-error">体重需在 30–200kg 之间</p>
          </div>
          <div class="field" :class="{ 'has-error': errs.waist }">
            <label>腰围（cm）</label>
            <input v-model="form.waist" class="input num" type="number" min="50" max="150" step="0.1" />
            <p class="field-error">腰围需在 50–150cm 之间</p>
          </div>
          <div class="field">
            <label>日常活动量</label>
            <select v-model="form.activity" class="select">
              <option v-for="a in ACTIVITIES" :key="a">{{ a }}</option>
            </select>
          </div>
          <div class="field" :class="{ 'has-error': errs.exerciseMin }">
            <label>每日运动时长（分钟）</label>
            <input v-model="form.exerciseMin" class="input num" type="number" min="0" max="300" step="5" />
            <p class="field-error">运动时长需在 0–300 分钟之间</p>
          </div>
          <div class="field">
            <label>主要运动形式</label>
            <input v-model="form.exerciseType" class="input" type="text" placeholder="如：快走 / 拉伸" />
          </div>
          <div class="field span-2">
            <label>慢病与特殊情况</label>
            <div class="row wrap">
              <button
                v-for="c in CHRONIC"
                :key="c"
                type="button"
                class="chip"
                :class="{ on: chronic.includes(c) }"
                @click="toggleInList(chronic, c)"
              >
                {{ c }}
              </button>
            </div>
            <p class="field-hint">可多选，将用于推荐护栏与营养提醒；不构成医疗诊断。</p>
          </div>
        </div>
      </div>
      <div class="card-ft row-between">
        <span class="small muted">身高 120–220cm · 体重 30–200kg</span>
        <button class="btn btn-primary" :disabled="saving" @click="saveHealth">
          <SvgIcon name="check" />{{ saving ? '保存中' : '保存身体数据' }}
        </button>
      </div>
    </article>

    <aside class="col" style="gap: 20px">
      <article class="card">
        <div class="card-hd">
          <h3>体重趋势</h3>
          <span class="badge gray">近 2 个月</span>
        </div>
        <div class="card-bd">
          <div class="weight-chart">
            <p v-if="chartLoading" class="small muted">正在加载体重趋势…</p>
            <svg
              v-else-if="chart"
              :viewBox="'0 0 ' + chart.W + ' ' + chart.H"
              role="img"
              aria-label="体重趋势折线图"
            >
              <defs>
                <linearGradient id="weightArea" x1="0" y1="0" x2="0" y2="1">
                  <stop class="area-top" offset="0%" stop-opacity="0.22" />
                  <stop class="area-bot" offset="100%" stop-opacity="0" />
                </linearGradient>
              </defs>
              <line
                v-for="(g, i) in chart.grid"
                :key="'g' + i"
                class="c-grid"
                :x1="chart.pl"
                :y1="g.y"
                :x2="chart.W - chart.pr"
                :y2="g.y"
              />
              <text
                v-for="(g, i) in chart.grid"
                :key="'gt' + i"
                :x="chart.pl - 7"
                :y="g.labelY"
                text-anchor="end"
              >
                {{ g.label }}
              </text>
              <path :d="chart.area" fill="url(#weightArea)" />
              <path class="c-line" :d="chart.line" />
              <circle
                v-for="(d, i) in chart.dots"
                :key="'d' + i"
                class="c-dot"
                :class="{ now: d.last }"
                :cx="d.cx"
                :cy="d.cy"
                :r="d.r"
              >
                <title>{{ d.title }}</title>
              </circle>
              <text
                v-for="(d, i) in chart.dots"
                :key="'dl' + i"
                :x="d.labelX"
                :y="chart.labelY"
                text-anchor="middle"
              >
                {{ d.label }}
              </text>
              <text
                class="c-label"
                :x="chart.valueLabel.x"
                :y="chart.valueLabel.y"
                text-anchor="end"
              >
                {{ chart.valueLabel.text }}
              </text>
            </svg>
            <p v-else class="small muted">暂无体重数据</p>
          </div>
          <div class="alert-inline green mt-16">
            <SvgIcon name="info" />
            <span>{{ targetNote }}</span>
          </div>
        </div>
      </article>

      <article class="card card-pad">
        <p class="eyebrow" style="margin: 0">Metrics · 指标解读</p>
        <div class="col mt-12" style="gap: 10px">
          <div class="row-between small">
            <span class="muted">BMI 参考区间</span><span class="num">18.5–23.9</span>
          </div>
          <div class="row-between small">
            <span class="muted">腰围参考（女性）</span><span class="num">&lt; 80 cm</span>
          </div>
          <div class="row-between small">
            <span class="muted">血压参考</span><span class="num">&lt; 120/80 mmHg</span>
          </div>
        </div>
        <p class="small muted mt-12">
          BMI 与腰围仅作初筛，肌肉量较高人群可能出现 BMI 偏高但体脂正常的情况。
        </p>
      </article>
    </aside>
  </section>

  <section class="card mt-24 reveal d3">
    <div class="card-hd">
      <h3>饮食偏好</h3>
      <span class="small muted">用于推荐过滤与食材替换</span>
    </div>
    <div class="card-bd">
      <div class="grid g2 pref-groups">
        <div v-for="g in prefGroups" :key="g.key" class="field">
          <label>{{ g.label }}</label>
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
        </div>
      </div>
    </div>
    <div class="card-ft row-between">
      <span class="small muted">偏好调整后，下次刷新推荐即可生效。</span>
      <button class="btn btn-primary" :disabled="prefSaving" @click="savePref">
        <SvgIcon name="check" />{{ prefSaving ? '保存中' : '保存偏好' }}
      </button>
    </div>
  </section>

  <p class="small muted mt-32" style="text-align: center">
    健康档案仅用于个性化饮食建议，不构成医疗诊断。慢病管理与用药调整请遵医嘱。
  </p>
</template>

<style scoped>
/* 原来写在 health.html <head> 里的页面级样式，搬到这里由 scoped 隔离 */
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
.form-grid .span-2 {
  grid-column: 1 / -1;
}
.pref-groups {
  gap: 20px 24px;
}
.risk-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 6px;
}
.weight-chart {
  margin-top: 2px;
}
.weight-chart svg {
  display: block;
  width: 100%;
  height: auto;
}
.weight-chart text {
  font-family: var(--font-num);
  font-size: 9.5px;
  fill: var(--text-3);
}
.weight-chart .c-grid {
  stroke: var(--border);
  stroke-width: 1;
  stroke-dasharray: 3 5;
}
.weight-chart .c-line {
  fill: none;
  stroke: var(--green-700);
  stroke-width: 2.2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.weight-chart .c-dot {
  fill: var(--surface);
  stroke: var(--green-700);
  stroke-width: 2;
}
.weight-chart .c-dot.now {
  fill: var(--green-800);
  stroke: var(--surface);
  stroke-width: 2.5;
}
.weight-chart .c-label {
  fill: var(--green-900);
  font-size: 10.5px;
  font-weight: 600;
}
.weight-chart .area-top,
.weight-chart .area-bot {
  stop-color: var(--green-700);
}
@media (max-width: 720px) {
  .form-grid {
    grid-template-columns: minmax(0, 1fr);
  }
  .form-grid .span-2 {
    grid-column: auto;
  }
}
</style>
