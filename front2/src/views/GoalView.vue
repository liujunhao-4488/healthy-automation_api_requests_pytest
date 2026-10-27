<script setup>
/* ============================================================
   GoalView.vue · 饮食目标
   ------------------------------------------------------------
   对应静态版 pages/goal.html。这个页面联动最多，重点有三处：
   1) 目标类型切换 → 建议热量与提示文案跟着变
   2) 三大营养素拖动 → 其余两项按原比例自动补齐到 100%
   3) 改体重/热量 → 摘要卡（环形进度、预计达成日）实时重算
   ============================================================ */
import { ref, reactive, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useAppStore, TODAY } from '@/stores/app'
import { goalApi } from '@/services/api'
import { toast } from '@/composables/useToast'
import SvgIcon from '@/components/SvgIcon.vue'

const store = useAppStore()

const health = computed(() => store.healthInfo)
const saved = computed(() => store.goalInfo)
const bmr = computed(() => health.value.bmr)

/* 各目标类型的推荐系数与说明 */
const TYPE_CFG = {
  减脂: {
    factor: 1.3,
    delta: -300,
    note: '减脂期建议每日热量缺口约 300 kcal，配合每周 150 分钟中等强度运动'
  },
  增肌: {
    factor: 1.3,
    delta: 300,
    note: '增肌期建议温和热量盈余，配合规律力量训练，每周增重 0.25–0.5kg'
  },
  控糖: {
    factor: 1.2,
    delta: 0,
    note: '控糖期控制总热量与餐后血糖波动，主食优先选择低 GI 食材'
  },
  维持: {
    factor: 1.3,
    delta: 0,
    note: '维持期热量接近日常消耗，重点是结构均衡与长期坚持'
  }
}
const GOAL_TYPES = Object.keys(TYPE_CFG)

/* ---------------- 表单状态 ---------------- */
const form = reactive({
  goalType: saved.value.goalType || '减脂',
  startWeight: saved.value.startWeight,
  currentWeight: saved.value.currentWeight,
  targetWeight: saved.value.targetWeight,
  kcal: saved.value.kcal,
  water: saved.value.water,
  reminderTime: saved.value.reminderTime || '07:30',
  meals: +saved.value.meals || 3,
  snack: !!saved.value.snack,
  reminderEnabled: !!saved.value.reminderEnabled
})
const macros = reactive({
  p: +saved.value.proteinPct || 30,
  c: +saved.value.carbPct || 45,
  f: +saved.value.fatPct || 25
})
const saving = ref(false)
/** 拖动过 sliders 标记，用于在 change 时提示一次 */
let macroAdjusted = false

/* ---------------- 建议热量 ---------------- */
const suggestedKcal = computed(() => {
  const cfg = TYPE_CFG[form.goalType] || TYPE_CFG['维持']
  return Math.round((bmr.value * cfg.factor + cfg.delta) / 50) * 50
})
const currentKcal = computed(() =>
  form.kcal >= 1000 && form.kcal <= 4000 ? +form.kcal : saved.value.kcal
)
const typeNote = computed(() => (TYPE_CFG[form.goalType] || TYPE_CFG['维持']).note)
const typeHint = computed(
  () =>
    '建议每日 ' +
    suggestedKcal.value.toLocaleString('zh-CN') +
    ' kcal（区间 ' +
    (suggestedKcal.value - 100).toLocaleString('zh-CN') +
    '–' +
    (suggestedKcal.value + 100).toLocaleString('zh-CN') +
    '）· ' +
    typeNote.value
)
const suggestRange = computed(
  () =>
    (suggestedKcal.value - 100).toLocaleString('zh-CN') +
    '–' +
    (suggestedKcal.value + 100).toLocaleString('zh-CN')
)

/* ---------------- 体重进度 ---------------- */
const weightState = computed(() => {
  const start = +form.startWeight || 0
  const cur = +form.currentWeight || 0
  const target = +form.targetWeight || 0
  // 目标低于起始体重＝减重，否则＝增重
  const losing = target <= start
  const done = losing ? Math.max(0, start - cur) : Math.max(0, cur - start)
  const total = Math.abs(start - target) || 1
  const left = Math.abs(cur - target)
  return {
    start,
    cur,
    target,
    losing,
    done: +done.toFixed(1),
    left: +left.toFixed(1),
    pct: Math.min(100, Math.max(0, Math.round((done / total) * 100)))
  }
})

/* ---------------- 摘要卡 ---------------- */
const RING_C = 2 * Math.PI * 50
const ringOffset = ref(RING_C)

function fmtDate(d) {
  const p = (n) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate())
}

const summary = computed(() => {
  const s = weightState.value
  const reached = s.losing ? s.cur <= s.target : s.cur >= s.target
  if (reached) {
    return {
      badge: '已达成目标',
      badgeCls: 'badge',
      expectDate: '已达成',
      expectWeeks: '保持当前饮食与运动节奏'
    }
  }
  const weeks = Math.ceil(s.left / 0.5)
  const d = new Date(TODAY + 'T00:00:00')
  d.setDate(d.getDate() + weeks * 7)
  return {
    badge: '剩余 ' + weeks + ' 周',
    badgeCls: 'badge amber',
    expectDate: fmtDate(d),
    expectWeeks: '约 ' + weeks + ' 周 · 每周 0.5kg'
  }
})

const summaryLine = computed(
  () =>
    form.goalType +
    ' · 目标 ' + weightState.value.target.toFixed(1) + ' kg · ' +
    (weightState.value.losing ? '已减 ' : '已增 ') +
    weightState.value.done.toFixed(1) + ' kg'
)

/* ---------------- 三大营养素 ---------------- */
const macroGrams = computed(() => {
  const kcal = currentKcal.value
  return {
    p: Math.round((kcal * macros.p) / 100 / 4),
    c: Math.round((kcal * macros.c) / 100 / 4),
    f: Math.round((kcal * macros.f) / 100 / 9)
  }
})
const macroSum = computed(() => macros.p + macros.c + macros.f)

const macroRows = [
  { key: 'p', name: '蛋白质', label: '蛋白质占比' },
  { key: 'c', name: '碳水化合物', label: '碳水化合物占比' },
  { key: 'f', name: '脂肪', label: '脂肪占比' }
]

/**
 * 拖动某一项后，把剩下的百分比按「另外两项原有比例」重新分配，
 * 这样三项加起来恒为 100%，且另外两项的相对关系不变。
 */
function onMacroInput(key, e) {
  macros[key] = +e.target.value
  const rest = 100 - macros[key]
  const others = ['p', 'c', 'f'].filter((k) => k !== key)
  const aOld = macros[others[0]]
  const bOld = macros[others[1]]
  const total = aOld + bOld
  const a = total > 0 ? (rest * aOld) / total : rest / 2
  const av = Math.max(5, Math.min(rest - 5, Math.round(a)))
  macros[others[0]] = av
  macros[others[1]] = rest - av
  macroAdjusted = true
}

function onMacroChange() {
  if (!macroAdjusted) return
  toast('已按比例修正其余两项，三大营养素合计保持 100%')
  macroAdjusted = false
}

function useSuggest() {
  form.kcal = suggestedKcal.value
  toast('已采用建议热量值 ' + suggestedKcal.value.toLocaleString('zh-CN') + ' kcal')
}

/* ---------------- 餐次 / 饮水 / 提醒 ---------------- */
const mealHint = computed(() => {
  const per = Math.round(currentKcal.value / form.meals)
  return (
    '每日 ' + form.meals + ' 餐' + (form.snack ? '，另加 1 次加餐' : '') +
    ' · 正餐每餐约 ' + per.toLocaleString('zh-CN') + ' kcal'
  )
})
const waterHint = computed(() => Math.round((+form.currentWeight || health.value.weight) * 30))

/* ---------------- 保存 ---------------- */
async function saveGoal() {
  const cur = +form.currentWeight
  const target = +form.targetWeight
  const kcal = +form.kcal
  const water = +form.water

  if (!(cur >= 30 && cur <= 200) || !(target >= 30 && target <= 200)) {
    toast('体重需在 30–200kg 之间', 'error')
    return
  }
  if (!(kcal >= 1000 && kcal <= 4000)) {
    toast('每日热量目标需在 1000–4000 kcal 之间', 'error')
    return
  }
  if (!(water >= 800 && water <= 5000)) {
    toast('饮水目标需在 800–5000ml 之间', 'error')
    return
  }
  if (form.reminderEnabled && !form.reminderTime) {
    toast('请设置提醒时间', 'error')
    return
  }
  if (macroSum.value !== 100) {
    toast('三大营养素占比之和需为 100%', 'error')
    return
  }

  saving.value = true
  const res = await goalApi.save({
    goalType: form.goalType,
    currentWeight: cur,
    targetWeight: target,
    kcal,
    proteinPct: macros.p,
    carbPct: macros.c,
    fatPct: macros.f,
    water,
    meals: form.meals,
    snack: form.snack,
    reminderEnabled: form.reminderEnabled,
    reminderTime: form.reminderTime || saved.value.reminderTime
  })
  saving.value = false
  if (res.code !== 200) {
    toast(res.message, 'error')
    return
  }
  toast(res.message || '目标已更新')
}

/* 环形进度：挂载后一次性动画到位 */
onMounted(() => {
  setTimeout(() => {
    ringOffset.value = RING_C * (1 - weightState.value.pct / 100)
  }, 80)
})
</script>

<template>
  <header class="page-head reveal">
    <div>
      <p class="eyebrow">Goal Setting</p>
      <h1 class="page-title">饮食目标</h1>
      <p class="page-sub">目标决定推荐结果，建议每 4 周复盘一次</p>
    </div>
    <div class="page-actions">
      <RouterLink class="btn btn-outline" to="/health">
        <SvgIcon name="heart-pulse" />健康档案
      </RouterLink>
      <button class="btn btn-primary" :disabled="saving" @click="saveGoal">
        <SvgIcon name="check" />{{ saving ? '保存中' : '保存目标' }}
      </button>
    </div>
  </header>

  <section class="grid split">
    <div class="col" style="gap: 20px">
      <!-- 目标类型 -->
      <article class="card card-pad reveal d1">
        <div class="row-between" style="align-items: flex-start">
          <div>
            <p class="eyebrow" style="margin: 0">Goal Type</p>
            <h3 style="font-family: var(--font-display); font-size: 19px; margin-top: 6px">目标类型</h3>
          </div>
          <span class="badge">{{ form.goalType }}</span>
        </div>
        <div class="seg mt-16">
          <button
            v-for="t in GOAL_TYPES"
            :key="t"
            type="button"
            :class="{ on: form.goalType === t }"
            @click="form.goalType = t"
          >
            {{ t }}
          </button>
        </div>
        <p class="small muted mt-12">{{ typeHint }}</p>
      </article>

      <!-- 体重目标 -->
      <article class="card reveal d2">
        <div class="card-hd">
          <h3>体重目标</h3>
          <span class="small muted">起始体重来自首次建档，不可修改</span>
        </div>
        <div class="card-bd">
          <div class="g-grid">
            <div class="field">
              <label>起始体重（kg）</label>
              <input :value="Number(form.startWeight).toFixed(1)" class="input num" type="number" disabled />
            </div>
            <div class="field">
              <label>当前体重（kg）</label>
              <input v-model.number="form.currentWeight" class="input num" type="number" min="30" max="200" step="0.1" />
            </div>
            <div class="field">
              <label>目标体重（kg）</label>
              <input v-model.number="form.targetWeight" class="input num" type="number" min="30" max="200" step="0.1" />
            </div>
          </div>
          <div class="bar mt-16"><i :style="{ width: weightState.pct + '%' }" /></div>
          <div class="row-between small muted mt-8">
            <span>
              {{ weightState.losing ? '已减' : '已增' }}
              <b class="num">{{ weightState.done.toFixed(1) }}</b> kg
            </span>
            <span>
              {{ weightState.losing ? '待减' : '待增' }}
              <b class="num">{{ weightState.left.toFixed(1) }}</b> kg
            </span>
            <span class="num">{{ weightState.pct }}%</span>
          </div>
        </div>
      </article>

      <!-- 热量目标 -->
      <article class="card card-pad reveal d3">
        <p class="eyebrow" style="margin: 0">Calorie Target</p>
        <div class="row-between mt-12" style="align-items: flex-end; gap: 16px; flex-wrap: wrap">
          <div class="field" style="max-width: 210px; flex: 1; min-width: 160px">
            <label>每日热量目标</label>
            <div class="input-affix">
              <input v-model.number="form.kcal" class="input num" type="number" min="1000" max="4000" step="50" />
              <span>kcal</span>
            </div>
          </div>
          <div class="grow" style="min-width: 230px">
            <p class="small muted">
              Mifflin-St Jeor 估算基础代谢
              <b class="num">{{ bmr.toLocaleString('zh-CN') }}</b> kcal/日
            </p>
            <p class="small" style="color: var(--green-700); margin-top: 4px">
              建议区间 <b class="num">{{ suggestRange }}</b> kcal
            </p>
            <p class="small muted" style="margin-top: 2px">{{ typeNote }}</p>
          </div>
          <button class="btn btn-soft btn-sm" @click="useSuggest">
            <SvgIcon name="refresh" />采用建议值
          </button>
        </div>
      </article>

      <!-- 三大营养素 -->
      <article class="card card-pad reveal d4">
        <div class="row-between">
          <p class="eyebrow" style="margin: 0">Macros · 三大营养素</p>
          <span class="small muted">合计 {{ macroSum }}%</span>
        </div>
        <div class="col mt-16" style="gap: 16px">
          <div v-for="row in macroRows" :key="row.key" class="slider-row">
            <span class="name">{{ row.name }}</span>
            <input
              type="range"
              min="5"
              max="60"
              step="1"
              :value="macros[row.key]"
              :aria-label="row.label"
              @input="onMacroInput(row.key, $event)"
              @change="onMacroChange"
            />
            <span class="val num">{{ macros[row.key] }}% · {{ macroGrams[row.key] }}g</span>
          </div>
        </div>
        <p class="small muted mt-12">拖动任一项时，其余两项按原比例自动修正，确保总和恒为 100%。</p>
      </article>

      <!-- 饮食节奏 -->
      <article class="card card-pad reveal d5">
        <p class="eyebrow" style="margin: 0">Habits · 饮食节奏</p>
        <div class="g-grid mt-12">
          <div class="field">
            <label>饮水目标</label>
            <div class="input-affix">
              <input v-model.number="form.water" class="input num" type="number" min="800" max="5000" step="100" />
              <span>ml</span>
            </div>
            <p class="field-hint">
              按体重 ×30ml 估算约 <span class="num">{{ waterHint.toLocaleString('zh-CN') }}</span> ml
            </p>
          </div>
          <div class="field">
            <label>提醒时间</label>
            <input
              v-model="form.reminderTime"
              class="input"
              type="time"
              :disabled="!form.reminderEnabled"
            />
            <p class="field-hint">
              {{ form.reminderEnabled ? '提醒开启后，将在此时间推送用餐提醒' : '提醒已关闭，不会推送通知' }}
            </p>
          </div>
        </div>
        <div class="row-between mt-16 wrap" style="gap: 20px">
          <div>
            <p class="field-label">每日餐次</p>
            <div class="seg">
              <button
                v-for="n in [2, 3, 4, 5]"
                :key="n"
                type="button"
                :class="{ on: form.meals === n }"
                @click="form.meals = n"
              >
                {{ n }} 餐
              </button>
            </div>
          </div>
          <label class="switch">
            <input v-model="form.snack" type="checkbox" />
            <span class="track" />
            <span class="switch-text">安排加餐</span>
          </label>
          <label class="switch">
            <input v-model="form.reminderEnabled" type="checkbox" />
            <span class="track" />
            <span class="switch-text">用餐提醒</span>
          </label>
        </div>
        <p class="small muted mt-12">{{ mealHint }}</p>
      </article>
    </div>

    <aside class="col" style="gap: 20px">
      <!-- 目标摘要 -->
      <article class="card card-pad reveal d3">
        <p class="eyebrow" style="margin: 0">Summary · 目标摘要</p>
        <div class="row mt-16" style="gap: 18px">
          <div class="goal-ring">
            <svg width="120" height="120" viewBox="0 0 120 120">
              <circle class="ring-track" cx="60" cy="60" r="50" fill="none" stroke-width="10" />
              <circle
                class="ring-val"
                cx="60"
                cy="60"
                r="50"
                fill="none"
                stroke-width="10"
                stroke-linecap="round"
                :stroke-dasharray="RING_C"
                :stroke-dashoffset="ringOffset"
                style="transition: stroke-dashoffset 0.9s var(--ease)"
              />
            </svg>
            <div class="goal-ring-center">
              <b class="num">{{ weightState.pct }}%</b>
              <span>目标进度</span>
            </div>
          </div>
          <div class="grow">
            <div class="metric">
              <span class="v num">{{ currentKcal.toLocaleString('zh-CN') }}</span>
              <span class="u">kcal / 日</span>
            </div>
            <p class="small muted mt-8">{{ summaryLine }}</p>
            <span class="mt-8" :class="summary.badgeCls">{{ summary.badge }}</span>
          </div>
        </div>
        <div class="mt-16">
          <div class="row-between small muted">
            <span>当前进度</span>
            <span class="num">{{ weightState.pct }}%</span>
          </div>
          <div class="bar mt-8"><i :style="{ width: weightState.pct + '%' }" /></div>
        </div>
        <div
          class="row-between mt-16"
          style="padding-top: 14px; border-top: 1px dashed var(--border)"
        >
          <div class="kpi">
            <span class="kpi-label">预计达成日期</span>
            <span class="kpi-value" style="font-size: 18px">{{ summary.expectDate }}</span>
          </div>
          <span class="small muted">{{ summary.expectWeeks }}</span>
        </div>
      </article>

      <!-- 小贴士 -->
      <article class="card card-pad reveal d4">
        <p class="eyebrow" style="margin: 0">Tips · 小贴士</p>
        <ul class="tip-list mt-12">
          <li>每 4 周复盘一次：体重连续两周不变时，先检查记录完整度，再考虑增加运动量。</li>
          <li>蛋白质建议按体重 1.2–1.6g/kg 分配，减脂期不宜低于 1.2g/kg，可分到每餐。</li>
          <li>饮水按体重 ×30ml 估算，运动日或天气炎热时可额外补充 300–500ml。</li>
        </ul>
        <RouterLink class="btn btn-soft btn-sm btn-block mt-16" to="/knowledge/3">
          <SvgIcon name="book-open" />蛋白质该吃多少
        </RouterLink>
      </article>

      <div class="alert-inline green reveal d5">
        <SvgIcon name="info" />
        <span>目标调整会同步影响首页推荐与每日营养配比，保存后立即生效。</span>
      </div>
    </aside>
  </section>

  <p class="small muted mt-32" style="text-align: center">
    热量建议基于 Mifflin-St Jeor 公式与通用营养原则，慢病人群请结合医生或临床营养师意见调整。
  </p>
</template>

<style scoped>
.g-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
.slider-row {
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr) 112px;
  gap: 12px;
  align-items: center;
}
.slider-row .name {
  font-size: 12.5px;
  color: var(--text-2);
}
.slider-row .val {
  font-size: 11.5px;
  color: var(--text-3);
  text-align: right;
}
.goal-ring {
  position: relative;
  width: 120px;
  height: 120px;
  flex: none;
}
.goal-ring svg {
  transform: rotate(-90deg);
}
.goal-ring .ring-track {
  stroke: var(--border);
}
.goal-ring .ring-val {
  stroke: var(--green-800);
}
.goal-ring-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  line-height: 1.2;
}
.goal-ring-center b {
  font-family: var(--font-num);
  font-size: 24px;
  color: var(--green-950);
}
.goal-ring-center span {
  font-size: 10.5px;
  color: var(--text-3);
}
.tip-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-size: 12.5px;
  color: var(--text-2);
  line-height: 1.7;
}
.tip-list li {
  padding-left: 14px;
  position: relative;
}
.tip-list li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--green-600);
}
@media (max-width: 720px) {
  .g-grid {
    grid-template-columns: minmax(0, 1fr);
  }
  .slider-row {
    grid-template-columns: 56px minmax(0, 1fr);
    row-gap: 4px;
  }
  .slider-row .val {
    grid-column: 2;
    text-align: left;
  }
}
</style>
