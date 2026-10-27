<script setup>
/* ============================================================
   RecordView.vue · 饮食记录
   ------------------------------------------------------------
   对应静态版 pages/record.html，是全站交互最多的页面：
     · 按日期翻看（前一天 / 今天 / 后一天）
     · 四餐分区展示 + 删除
     · 添加记录弹窗：食材搜索 → 实时营养预览 → 加入本餐 → 保存
     · 近 7 日趋势图（柱＝热量，折线＝蛋白质）

   原版每个动作都调 renderAll() 重绘整页；
   这里数据在 store 里，改完页面对应部分自动更新，只在
   「AI 建议」这类服务端结果需要重新拉取时才显式调用。
   ============================================================ */
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useAppStore, TODAY } from '@/stores/app'
import DB from '@/mock/db'
import { recordsApi, ingredientsApi } from '@/services/api'
import { toast } from '@/composables/useToast'
import { confirmDialog } from '@/composables/useConfirm'
import SvgIcon from '@/components/SvgIcon.vue'

const store = useAppStore()

const MEALS = [
  { name: '早餐', icon: 'sun' },
  { name: '午餐', icon: 'bowl' },
  { name: '晚餐', icon: 'utensils' },
  { name: '加餐', icon: 'apple' }
]
const MEAL_NAMES = MEALS.map((m) => m.name)
const RING_C = 2 * Math.PI * 50

/* ---------------- 日期切换 ---------------- */
const offset = ref(0)

function dateByOffset(n) {
  const d = new Date(TODAY + 'T00:00:00')
  d.setDate(d.getDate() + n)
  const p = (x) => String(x).padStart(2, '0')
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate())
}
const currentDate = computed(() => dateByOffset(offset.value))

function switchDate(delta) {
  offset.value = delta === 0 ? 0 : offset.value + delta
}

/* ---------------- 汇总 ---------------- */
const dayRecords = computed(() => store.recordsByDate(currentDate.value))
const dayTotals = computed(() => store.totals(currentDate.value))
const goal = computed(() => store.goalInfo)

const kcalPct = computed(() =>
  goal.value.kcal ? Math.round((dayTotals.value.kcal / goal.value.kcal) * 100) : 0
)
const ringOffset = ref(RING_C)
watch(
  kcalPct,
  (v) => {
    ringOffset.value = RING_C * (1 - Math.min(100, v) / 100)
  },
  { flush: 'post' }
)

const subText = computed(
  () => store.dateLabel(currentDate.value) + ' · 已记录 ' + dayRecords.value.length + ' 餐'
)

const macroBars = computed(() => {
  const t = dayTotals.value
  const g = goal.value
  return [
    { name: '蛋白质', val: t.p, target: Math.round((g.kcal * g.proteinPct) / 100 / 4), cls: '' },
    { name: '碳水', val: t.c, target: Math.round((g.kcal * g.carbPct) / 100 / 4), cls: ' amber' },
    { name: '脂肪', val: t.f, target: Math.round((g.kcal * g.fatPct) / 100 / 9), cls: ' clay' }
  ].map((m) => ({
    ...m,
    pct: m.target ? Math.min(100, Math.round((m.val / m.target) * 100)) : 0
  }))
})

/** 四餐分区：每餐的记录按时间排序 */
const mealSections = computed(() =>
  MEALS.map((m) => ({
    ...m,
    list: dayRecords.value
      .filter((r) => r.mealType === m.name)
      .sort((a, b) => String(a.time).localeCompare(String(b.time)))
  }))
)

function recordKcal(r) {
  return Math.round((r.items || []).reduce((s, i) => s + (+i.kcal || 0), 0))
}
function recordNames(r) {
  return (r.items || []).map((i) => i.name + ' ' + i.amount + (i.unit || '')).join(' · ')
}

async function removeRecord(r) {
  const label = (r.items || []).map((i) => i.name).join('、') || r.mealType
  const ok = await confirmDialog('删除「' + label + '」这条记录？删除后当日汇总会同步更新。', {
    title: '删除记录',
    okText: '删除',
    danger: true
  })
  if (!ok) return
  const res = await recordsApi.remove(r.id)
  if (res.code !== 200) {
    toast(res.message, 'error')
    return
  }
  toast('记录已删除')
  loadSuggestions()
}

/* ---------------- 近 7 日趋势图 ---------------- */
const trend = computed(() => store.trend)

const chart = computed(() => {
  const data = trend.value
  if (!data || !data.length) return null

  const W = 620
  const H = 258
  const pl = 40
  const pr = 38
  const pt = 18
  const pb = 34
  const iw = W - pl - pr
  const ih = H - pt - pb

  const maxK = Math.ceil(Math.max(2000, ...data.map((d) => d.kcal)) / 500) * 500
  const maxP = Math.ceil(Math.max(120, ...data.map((d) => d.p)) / 40) * 40
  const slot = iw / data.length
  const barW = Math.min(34, slot * 0.46)
  const yK = (v) => pt + ih - (v / maxK) * ih
  const yP = (v) => pt + ih - (v / maxP) * ih

  const grid = []
  for (let i = 0; i <= 4; i++) {
    const y = yK((maxK / 4) * i)
    grid.push({
      y: y.toFixed(1),
      labelY: (y + 3).toFixed(1),
      leftLabel: Math.round((maxK / 4) * i),
      rightLabel: Math.round((maxP / 4) * i)
    })
  }

  const bars = data.map((d, i) => {
    const x = pl + slot * i + (slot - barW) / 2
    const y = yK(d.kcal)
    return {
      x: x.toFixed(1),
      y: y.toFixed(1),
      w: barW.toFixed(1),
      h: Math.max(0, pt + ih - y).toFixed(1),
      today: i === data.length - 1,
      title: d.date + ' · ' + d.kcal + ' kcal'
    }
  })

  const dots = data.map((d, i) => ({
    cx: (pl + slot * i + slot / 2).toFixed(1),
    cy: yP(d.p).toFixed(1)
  }))
  const line = 'M' + dots.map((p) => p.cx + ' ' + p.cy).join(' L')

  const labels = data.map((d, i) => ({
    x: (pl + slot * i + slot / 2).toFixed(1),
    text: d.date,
    today: i === data.length - 1
  }))

  return { W, H, pl, pr, labelY: H - 12, grid, bars, dots, line, labels }
})

/* ---------------- AI 建议 ---------------- */
const suggestions = ref([])
const suggestLoading = ref(true)

async function loadSuggestions() {
  suggestLoading.value = true
  const res = await recordsApi.suggestions()
  suggestLoading.value = false
  if (res.code !== 200) return
  suggestions.value = res.data
}
loadSuggestions()

/* ============================================================
   添加记录弹窗
   ============================================================ */
const modalOpen = ref(false)
const meal = ref('早餐')
const staged = ref([])
const note = ref('')
const saving = ref(false)

/* 食材搜索 */
const keyword = ref('')
const candOpen = ref(false)
const candidates = computed(() => {
  const kw = keyword.value.trim()
  if (!kw) return []
  return DB.ingredients
    .filter((i) => i.name.indexOf(kw) > -1 || i.cat.indexOf(kw) > -1)
    .slice(0, 8)
})

let searchTimer = null
function onSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    candOpen.value = !!keyword.value.trim()
  }, 140)
}

/* 选中的食材 + 克数 + 营养预览 */
const selectedIng = ref(null)
const grams = ref(100)
const preview = ref(null)
const previewLoading = ref(false)
/** 请求序号：只认最后一次请求的结果，避免快速改克数时旧结果覆盖新结果 */
let nutReq = 0

function pickIng(ing) {
  selectedIng.value = ing
  keyword.value = ing.name
  candOpen.value = false
  updatePreview()
}

async function updatePreview() {
  if (!selectedIng.value) {
    preview.value = null
    return
  }
  const g = Math.max(1, Math.min(1000, Math.round(+grams.value || 100)))
  const req = ++nutReq
  previewLoading.value = true
  const res = await ingredientsApi.nutrition({ id: selectedIng.value.id, grams: g })
  if (req !== nutReq) return // 已经有更新的请求了，丢弃这次结果
  previewLoading.value = false
  preview.value = res.code === 200 ? res.data : { error: res.message }
}

let gramTimer = null
function onGramsInput() {
  clearTimeout(gramTimer)
  gramTimer = setTimeout(updatePreview, 220)
}

const stagedKcal = computed(() =>
  Math.round(staged.value.reduce((s, i) => s + (+i.kcal || 0), 0))
)

async function addItem() {
  if (!selectedIng.value) {
    toast('请先搜索并选择一种食材', 'error')
    return
  }
  const g = Math.round(+grams.value || 0)
  if (g < 1 || g > 1000) {
    toast('食用量需在 1–1000g 之间', 'error')
    return
  }
  const res = await ingredientsApi.nutrition({ id: selectedIng.value.id, grams: g })
  if (res.code !== 200) {
    toast(res.message, 'error')
    return
  }
  const d = res.data
  staged.value = staged.value.concat([
    { name: d.name, amount: d.grams, unit: 'g', kcal: d.kcal, p: d.p, c: d.c, f: d.f }
  ])
  selectedIng.value = null
  nutReq++
  keyword.value = ''
  grams.value = 100
  preview.value = null
  toast('已加入 ' + d.name + ' ' + d.grams + 'g')
}

function removeItem(index) {
  staged.value = staged.value.filter((_, i) => i !== index)
}

/** 按当前时间猜该记哪一餐 */
function guessMeal() {
  const h = new Date().getHours()
  if (h < 10) return '早餐'
  if (h < 15) return '午餐'
  if (h < 20) return '晚餐'
  return '加餐'
}

function openRecord(targetMeal) {
  staged.value = []
  selectedIng.value = null
  preview.value = null
  note.value = ''
  keyword.value = ''
  grams.value = 100
  candOpen.value = false
  meal.value = targetMeal || guessMeal()
  modalOpen.value = true
  setTimeout(() => document.getElementById('foodSearch')?.focus(), 160)
}

function closeRecord() {
  modalOpen.value = false
}

async function saveRecord() {
  if (!staged.value.length) {
    toast('请至少添加一项食材', 'error')
    return
  }
  saving.value = true
  const res = await recordsApi.submit({
    date: currentDate.value,
    mealType: meal.value,
    time: store.nowTime(),
    note: note.value.trim(),
    items: staged.value.map((it) => ({
      name: it.name,
      amount: it.amount,
      unit: it.unit,
      kcal: it.kcal,
      p: it.p,
      c: it.c,
      f: it.f
    }))
  })
  saving.value = false
  if (res.code !== 200) {
    toast(res.message, 'error')
    return
  }
  modalOpen.value = false
  toast('已保存到' + store.dateLabel(currentDate.value) + ' · ' + meal.value)
  loadSuggestions()
}

/* 弹窗打开时锁背景滚动，ESC 关闭 */
watch(modalOpen, (open) => {
  document.body.style.overflow = open ? 'hidden' : ''
})
function onKeydown(e) {
  if (e.key === 'Escape' && modalOpen.value) closeRecord()
}
/* 点空白处收起候选框 */
function onDocClick(e) {
  if (!e.target.closest?.('.search-box')) candOpen.value = false
}
onMounted(() => {
  document.addEventListener('keydown', onKeydown)
  document.addEventListener('click', onDocClick)
})
onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
  document.removeEventListener('click', onDocClick)
  document.body.style.overflow = ''
})

/* ---------------- 快捷入口 ---------------- */
const quickLinks = [
  { to: '/recipes', icon: 'book-open', title: '找低脂食谱', sub: '按目标筛选' },
  { to: '/goal', icon: 'target', title: '调整热量目标', sub: '热量与配比' },
  { to: '/ingredients', icon: 'apple', title: '查食材热量', sub: '每 100g 数据' },
  { to: '/knowledge/1', icon: 'news', title: '今日科普', sub: '低 GI 主食怎么选' }
]

/* 首屏让环动画一次 */
onMounted(() => {
  setTimeout(() => {
    ringOffset.value = RING_C * (1 - Math.min(100, kcalPct.value) / 100)
  }, 80)
})
</script>

<template>
  <header class="page-head reveal">
    <div>
      <p class="eyebrow">Food Log</p>
      <h1 class="page-title">饮食记录</h1>
      <p class="page-sub">{{ subText }}</p>
    </div>
    <div class="page-actions">
      <div class="seg">
        <button type="button" @click="switchDate(-1)">
          <SvgIcon name="chevron-left" />前一天
        </button>
        <button type="button" :class="{ on: offset === 0 }" @click="switchDate(0)">今天</button>
        <button type="button" @click="switchDate(1)">后一天<SvgIcon name="chevron-right" /></button>
      </div>
      <button class="btn btn-primary" @click="openRecord()">
        <SvgIcon name="plus" />添加记录
      </button>
    </div>
  </header>

  <!-- 当日汇总 -->
  <section class="card card-pad reveal d1">
    <div class="row" style="gap: 28px; flex-wrap: wrap; align-items: center">
      <div class="log-ring">
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
        <div class="log-ring-center">
          <b class="num">{{ dayTotals.kcal.toLocaleString('zh-CN') }}</b>
          <span>已摄入 kcal</span>
        </div>
      </div>

      <div class="grow" style="min-width: 260px">
        <div class="row-between" style="align-items: flex-start; margin-bottom: 14px">
          <div>
            <p class="eyebrow" style="margin: 0">Daily Intake</p>
            <p class="small muted mt-8">
              目标 {{ goal.kcal.toLocaleString('zh-CN') }} kcal · 剩余
              {{ Math.max(0, goal.kcal - dayTotals.kcal).toLocaleString('zh-CN') }} kcal
            </p>
          </div>
          <span :class="dayTotals.kcal > goal.kcal ? 'badge amber' : 'badge'">
            {{ dayRecords.length }} 餐
          </span>
        </div>
        <div class="macro-row">
          <div v-for="m in macroBars" :key="m.name" class="macro-item">
            <span class="name">{{ m.name }}</span>
            <span class="bar" :class="m.cls"><i :style="{ width: m.pct + '%' }" /></span>
            <span class="val">{{ m.val }} / {{ m.target }}g</span>
          </div>
        </div>
        <div class="row-between small muted mt-12">
          <span>已摄入 / 目标</span>
          <span class="num">{{ kcalPct }}%</span>
        </div>
      </div>
    </div>
  </section>

  <div v-if="!dayRecords.length" class="alert-inline green mt-16">
    <SvgIcon name="info" />
    <span>{{ store.dateLabel(currentDate) }} 暂无记录，点击任一餐次的「添加」开始记录。</span>
  </div>

  <!-- 四餐分区 -->
  <section class="grid g2 mt-24 reveal d2">
    <article v-for="m in mealSections" :key="m.name" class="card">
      <div class="card-hd">
        <div class="row" style="gap: 8px">
          <SvgIcon :name="m.icon" style="color: var(--green-700)" />
          <h3>{{ m.name }}</h3>
          <span class="badge gray">{{ m.list.length }} 条</span>
        </div>
        <button class="btn btn-sm btn-soft" @click="openRecord(m.name)">
          <SvgIcon name="plus" />添加
        </button>
      </div>
      <div class="card-bd" style="padding: 6px 24px 12px">
        <template v-if="m.list.length">
          <div v-for="r in m.list" :key="r.id" class="log-row">
            <span class="small muted num">{{ r.time }}</span>
            <div class="grow">
              <strong style="font-size: 12.5px">{{ recordNames(r) }}</strong>
              <p v-if="r.note" class="small muted">{{ r.note }}</p>
            </div>
            <span class="num small" style="color: var(--green-800)">{{ recordKcal(r) }} kcal</span>
            <button class="icon-btn plain" title="删除记录" @click="removeRecord(r)">
              <SvgIcon name="trash" />
            </button>
          </div>
        </template>
        <div v-else class="meal-empty">
          <p class="small muted">还没有{{ m.name }}记录</p>
          <button class="btn btn-sm btn-soft" @click="openRecord(m.name)">
            <SvgIcon name="plus" />添加
          </button>
        </div>
      </div>
    </article>
  </section>

  <!-- 趋势 + 建议 -->
  <section class="grid split mt-32 reveal d3">
    <article class="card">
      <div class="card-hd">
        <h3>近 7 日摄入趋势</h3>
        <div class="chart-legend">
          <span><i />热量 kcal</span>
          <span><i class="amber" />蛋白质 g</span>
        </div>
      </div>
      <div class="card-bd">
        <svg
          v-if="chart"
          class="trend-svg"
          :viewBox="'0 0 ' + chart.W + ' ' + chart.H"
          role="img"
          aria-label="近七天热量与蛋白质趋势"
        >
          <line
            v-for="(g, i) in chart.grid"
            :key="'g' + i"
            class="t-grid"
            :x1="chart.pl"
            :y1="g.y"
            :x2="chart.W - chart.pr"
            :y2="g.y"
          />
          <text
            v-for="(g, i) in chart.grid"
            :key="'gl' + i"
            :x="chart.pl - 8"
            :y="g.labelY"
            text-anchor="end"
          >
            {{ g.leftLabel }}
          </text>
          <text
            v-for="(g, i) in chart.grid"
            :key="'gr' + i"
            class="t-ptext"
            :x="chart.W - chart.pr + 8"
            :y="g.labelY"
            text-anchor="start"
          >
            {{ g.rightLabel }}
          </text>
          <rect
            v-for="(b, i) in chart.bars"
            :key="'b' + i"
            class="t-bar"
            :class="{ today: b.today }"
            :x="b.x"
            :y="b.y"
            :width="b.w"
            :height="b.h"
            rx="4"
          >
            <title>{{ b.title }}</title>
          </rect>
          <path class="t-line" :d="chart.line" />
          <circle
            v-for="(d, i) in chart.dots"
            :key="'d' + i"
            class="t-dot"
            :cx="d.cx"
            :cy="d.cy"
            r="3"
          />
          <text
            v-for="(l, i) in chart.labels"
            :key="'l' + i"
            :class="{ 't-today': l.today }"
            :x="l.x"
            :y="chart.labelY"
            text-anchor="middle"
          >
            {{ l.text }}
          </text>
        </svg>
        <p v-else class="small muted">暂无趋势数据</p>
        <p class="small muted mt-12">
          柱状为每日热量（左轴 kcal），折线为蛋白质（右轴 g）。今日数据随记录实时更新。
        </p>
      </div>
    </article>

    <aside class="col" style="gap: 20px">
      <article class="card">
        <div class="card-hd">
          <h3>AI 饮食建议</h3>
          <span class="badge"><SvgIcon name="sparkles" />基于今日</span>
        </div>
        <div class="card-bd">
          <div class="col" style="gap: 14px">
            <template v-if="suggestLoading">
              <div class="sk" style="height: 14px; width: 90%" />
              <div class="sk" style="height: 14px; width: 78%" />
              <div class="sk" style="height: 14px; width: 66%" />
            </template>
            <div
              v-for="(text, i) in suggestions"
              :key="i"
              class="row"
              style="align-items: flex-start; gap: 10px; font-size: 12.5px; color: var(--text-2); line-height: 1.75"
            >
              <span class="badge gray">{{ i + 1 }}</span><span>{{ text }}</span>
            </div>
          </div>
          <RouterLink class="btn btn-soft btn-sm btn-block mt-16" to="/assistant">
            <SvgIcon name="sparkles" />继续问 AI 助手
          </RouterLink>
        </div>
      </article>

      <div class="quick-grid">
        <RouterLink v-for="q in quickLinks" :key="q.to" class="quick" :to="q.to">
          <span class="q-ico"><SvgIcon :name="q.icon" /></span>
          <strong>{{ q.title }}</strong>
          <span>{{ q.sub }}</span>
        </RouterLink>
      </div>
    </aside>
  </section>

  <p class="small muted mt-32" style="text-align: center">
    营养数据为食材库估算值，实际会因品种、部位与烹调方式浮动。健康建议不构成医疗诊断。
  </p>

  <!-- ===================== 添加记录弹窗 ===================== -->
  <div class="overlay" :class="{ open: modalOpen }" @click.self="closeRecord">
    <div class="modal wide">
      <div class="modal-hd">
        <div>
          <h3>添加饮食记录</h3>
          <p>记录日期 · {{ store.dateLabel(currentDate) }}（{{ currentDate }}）</p>
        </div>
        <button type="button" class="modal-close" aria-label="关闭" @click="closeRecord">
          <SvgIcon name="x" />
        </button>
      </div>
      <div class="modal-bd">
        <div class="field">
          <label>餐次</label>
          <div class="seg">
            <button
              v-for="m in MEAL_NAMES"
              :key="m"
              type="button"
              :class="{ on: meal === m }"
              @click="meal = m"
            >
              {{ m }}
            </button>
          </div>
        </div>

        <div class="field mt-16">
          <label for="foodSearch">搜索食材</label>
          <div class="search-box">
            <SvgIcon name="search" />
            <input
              id="foodSearch"
              v-model="keyword"
              class="input"
              type="text"
              placeholder="输入食材名称，如鸡胸肉、燕麦、西兰花"
              autocomplete="off"
              @input="onSearchInput"
              @focus="candOpen = !!keyword.trim()"
            />
            <div class="cand-box" :class="{ on: candOpen }">
              <template v-if="candidates.length">
                <div v-for="i in candidates" :key="i.id" class="cand" @click="pickIng(i)">
                  <span class="grow">
                    <strong>{{ i.name }}</strong>
                    <span class="small muted"> {{ i.cat }} · {{ i.kcal }} kcal/100g</span>
                  </span>
                  <span class="badge gray">蛋白 {{ i.p }}g</span>
                </div>
              </template>
              <div v-else class="cand-empty">
                没有匹配的食材，可以试试「鸡胸肉」「燕麦」「西兰花」。
              </div>
            </div>
          </div>
        </div>

        <div class="row mt-12" style="gap: 14px; align-items: flex-end; flex-wrap: wrap">
          <div class="field" style="max-width: 180px; flex: 1; min-width: 130px">
            <label for="gramsInput">食用量</label>
            <div class="input-affix">
              <input
                id="gramsInput"
                v-model="grams"
                class="input num"
                type="number"
                min="1"
                max="1000"
                step="10"
                @input="onGramsInput"
              />
              <span>g</span>
            </div>
          </div>
          <button type="button" class="btn btn-outline" @click="addItem">
            <SvgIcon name="plus" />加入本餐
          </button>
        </div>

        <!-- 实时营养预览 -->
        <div class="nut-preview mt-12">
          <p v-if="previewLoading" class="small muted">正在计算营养…</p>
          <p v-else-if="preview && preview.error" class="small" style="color: var(--danger)">
            {{ preview.error }}
          </p>
          <template v-else-if="preview">
            <div class="row-between">
              <span class="small"><b>{{ preview.name }}</b> · {{ preview.grams }}g</span>
              <span class="small num" style="color: var(--green-800)">{{ preview.kcal }} kcal</span>
            </div>
            <div class="row small muted mt-8" style="gap: 16px; flex-wrap: wrap">
              <span>蛋白 <b class="num">{{ preview.p }}</b>g</span>
              <span>碳水 <b class="num">{{ preview.c }}</b>g</span>
              <span>脂肪 <b class="num">{{ preview.f }}</b>g</span>
            </div>
          </template>
          <p v-else class="small muted">选择食材并填写克数后，这里会显示实时营养估算。</p>
        </div>

        <div class="field mt-16">
          <div class="row-between">
            <label>已添加条目</label>
            <span class="small muted">合计 {{ stagedKcal }} kcal</span>
          </div>
          <div>
            <div v-if="!staged.length" class="small muted" style="padding: 6px 0">
              尚未添加食材，选择候选后点击「加入本餐」。
            </div>
            <div v-for="(it, i) in staged" :key="i" class="log-row">
              <span class="small muted num">{{ i + 1 }}</span>
              <div class="grow">
                <strong style="font-size: 12.5px">{{ it.name }}</strong>
                <p class="small muted">{{ it.amount }}g · 蛋白 {{ it.p }}g · 碳水 {{ it.c }}g</p>
              </div>
              <span class="num small" style="color: var(--green-800)">{{ Math.round(it.kcal) }} kcal</span>
              <button class="icon-btn plain" title="移除" @click="removeItem(i)">
                <SvgIcon name="trash" />
              </button>
            </div>
          </div>
        </div>

        <div class="field mt-16">
          <label for="noteInput">备注</label>
          <textarea
            id="noteInput"
            v-model="note"
            class="textarea"
            placeholder="如：公司食堂、晨跑后、少油少盐"
          />
        </div>
      </div>
      <div class="modal-ft">
        <button type="button" class="btn btn-outline" @click="closeRecord">取消</button>
        <button type="button" class="btn btn-primary" :disabled="saving" @click="saveRecord">
          <SvgIcon name="check" />{{ saving ? '保存中' : '保存记录' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.log-ring {
  position: relative;
  width: 120px;
  height: 120px;
  flex: none;
}
.log-ring svg {
  transform: rotate(-90deg);
}
.log-ring .ring-track {
  stroke: var(--border);
}
.log-ring .ring-val {
  stroke: var(--green-800);
}
.log-ring-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  line-height: 1.2;
}
.log-ring-center b {
  font-family: var(--font-num);
  font-size: 23px;
  color: var(--green-950);
}
.log-ring-center span {
  font-size: 10.5px;
  color: var(--text-3);
}
.cand-box {
  position: absolute;
  left: 0;
  right: 0;
  top: calc(100% + 6px);
  z-index: 6;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: var(--shadow);
  max-height: 224px;
  overflow-y: auto;
  display: none;
}
.cand-box.on {
  display: block;
}
.cand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 13px;
  cursor: pointer;
  font-size: 12.5px;
  border-bottom: 1px dashed var(--border);
}
.cand:last-child {
  border-bottom: 0;
}
.cand:hover {
  background: var(--green-050);
}
.cand-empty {
  padding: 14px 13px;
  font-size: 12px;
  color: var(--text-3);
}
.log-row {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr) auto auto;
  gap: 10px;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px dashed var(--border);
}
.log-row:last-child {
  border-bottom: 0;
}
.meal-empty {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 0;
}
.nut-preview {
  padding: 12px 14px;
  border: 1px dashed var(--border-strong);
  border-radius: 12px;
  background: var(--surface-2);
  font-size: 12px;
}
.trend-svg {
  display: block;
  width: 100%;
  height: auto;
}
.trend-svg text {
  font-family: var(--font-num);
  font-size: 9.5px;
  fill: var(--text-3);
}
.trend-svg .t-grid {
  stroke: var(--border);
  stroke-width: 1;
  stroke-dasharray: 3 5;
}
.trend-svg .t-bar {
  fill: var(--green-100);
}
.trend-svg .t-bar.today {
  fill: var(--green-700);
}
.trend-svg .t-line {
  fill: none;
  stroke: var(--amber-600);
  stroke-width: 2.2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.trend-svg .t-dot {
  fill: var(--surface);
  stroke: var(--amber-600);
  stroke-width: 2;
}
.trend-svg .t-ptext {
  fill: var(--amber-600);
}
.trend-svg .t-today {
  fill: var(--green-800);
  font-weight: 600;
}
@media (max-width: 720px) {
  .log-row {
    grid-template-columns: 40px minmax(0, 1fr) auto auto;
    gap: 8px;
  }
}
</style>
