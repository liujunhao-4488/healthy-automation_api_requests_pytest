<script setup>
/* ============================================================
   HomeView.vue · 首页
   ------------------------------------------------------------
   对应静态版 pages/home.html。

   静态版靠一堆 getElementById 改写文本，现在全部换成本地状态：
   数据一变，模板自动更新，不再需要 location.reload()。
   ============================================================ */
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useAppStore, TODAY } from '@/stores/app'
import { recommendApi, recordsApi } from '@/services/api'
import { toast } from '@/composables/useToast'
import SvgIcon from '@/components/SvgIcon.vue'

const store = useAppStore()

/* ---------------- 问候语 ---------------- */
function greeting() {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 11) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
}

const title = computed(() => greeting() + '，' + store.displayName)
const subtitle = computed(
  () =>
    store.dateLabel(TODAY) +
    ' · 已记录 ' +
    store.recordsByDate(TODAY).length +
    ' 餐，按目标稳步推进'
)

/* ---------------- 能量环 ---------------- */
const goal = computed(() => store.goalInfo)
const total = computed(() => store.totals(TODAY))
const kcalPct = computed(() =>
  Math.min(100, Math.round((total.value.kcal / goal.value.kcal) * 100))
)
const kcalLeft = computed(() => Math.max(0, goal.value.kcal - total.value.kcal))
const RADIUS = 70
const CIRC = 2 * Math.PI * RADIUS
/** 环的偏移量：一开始满格（100% 未填充），挂载后再动画到目标值 */
const ringOffset = ref(CIRC)

onMounted(() => {
  setTimeout(() => {
    ringOffset.value = CIRC * (1 - kcalPct.value / 100)
  }, 120)
})

/* ---------------- 三大营养素 ---------------- */
const macros = computed(() => {
  const t = total.value
  const g = goal.value
  return [
    {
      name: '蛋白质',
      val: t.p,
      target: Math.round((g.kcal * g.proteinPct) / 100 / 4),
      cls: ''
    },
    {
      name: '碳水',
      val: t.c,
      target: Math.round((g.kcal * g.carbPct) / 100 / 4),
      cls: ' amber'
    },
    {
      name: '脂肪',
      val: t.f,
      target: Math.round((g.kcal * g.fatPct) / 100 / 9),
      cls: ' clay'
    }
  ].map((m) => ({
    ...m,
    pct: Math.min(100, Math.round((m.val / (m.target || 1)) * 100))
  }))
})

/* ---------------- 目标进度 ---------------- */
const lostWeight = computed(() =>
  +(goal.value.startWeight - goal.value.currentWeight).toFixed(1)
)
const needWeight = computed(() => +(goal.value.startWeight - goal.value.targetWeight).toFixed(1))
const goalPct = computed(() =>
  Math.min(100, Math.round((lostWeight.value / (needWeight.value || 1)) * 100))
)
/** 进度条宽度也做一次性动画 */
const weightBarWidth = ref('0%')
onMounted(() => {
  setTimeout(() => (weightBarWidth.value = goalPct.value + '%'), 200)
})

const streakDays = ['一', '二', '三', '四', '五', '六', '日']

/* ---------------- 饮水 ---------------- */
const waterText = computed(() => store.waterCups * 250 + ' / ' + goal.value.water + ' ml')

function onCup(index) {
  // 点第几格就是第几杯；点当前最后一杯则减一杯
  store.addWater(index + 1 === store.waterCups ? index : index + 1)
  toast('已记录饮水')
}

/* ---------------- 今日记录时间线 ---------------- */
const todayRecords = computed(() => store.recordsByDate(TODAY))

function recordKcal(r) {
  return (r.items || []).reduce((s, i) => s + (+i.kcal || 0), 0)
}
function recordNames(r) {
  return (r.items || []).map((i) => i.name).join(' · ')
}

/* ---------------- 今日推荐 ---------------- */
const mealRecos = ref([])
const recoLoading = ref(true)
const addedIds = ref([])

async function loadReco() {
  recoLoading.value = true
  const res = await recommendApi.today()
  recoLoading.value = false
  if (res.code !== 200) {
    toast(res.message, 'error')
    return
  }
  mealRecos.value = res.data.list
}
loadReco()

async function addToRecord(recipe) {
  const res = await recordsApi.submit({
    mealType: recipe.mealType,
    time: store.nowTime(),
    note: '来自推荐',
    items: [
      {
        name: recipe.name,
        amount: 1,
        unit: '份',
        kcal: recipe.kcal,
        p: recipe.p,
        c: recipe.c,
        f: recipe.f
      }
    ]
  })
  if (res.code !== 200) {
    toast(res.message, 'error')
    return
  }
  addedIds.value = addedIds.value.concat([recipe.id])
  toast('已记入今日' + recipe.mealType)
}

/* ---------------- 今日建议 ---------------- */
const advice = ref([])
recordsApi.suggestions().then((res) => {
  if (res.code === 200) advice.value = res.data
})

/* ---------------- 快捷入口 ---------------- */
const quickLinks = [
  { to: '/record', icon: 'notebook', title: '记录一餐', sub: '早餐 / 午餐 / 晚餐' },
  { to: '/ingredients', icon: 'refresh', title: '食材替代', sub: '按营养等价替换' },
  { to: '/goal', icon: 'target', title: '更新目标', sub: '热量与配比' },
  { to: '/knowledge/1', icon: 'news', title: '今日科普', sub: '低 GI 主食怎么选' }
]
</script>

<template>
  <header class="page-head reveal">
    <div>
      <p class="eyebrow">My Health · Today</p>
      <h1 class="page-title">{{ title }}</h1>
      <p class="page-sub">{{ subtitle }}</p>
    </div>
    <div class="page-actions">
      <button class="btn btn-outline" :disabled="recoLoading" @click="loadReco">
        <SvgIcon name="refresh" />{{ recoLoading ? '生成中' : '换一批推荐' }}
      </button>
      <RouterLink class="btn btn-primary" to="/record">
        <SvgIcon name="plus" />记录一餐
      </RouterLink>
    </div>
  </header>

  <!-- 今日能量 + 目标 -->
  <section class="grid split">
    <article class="card energy-card reveal d1">
      <div class="row-between" style="align-items: flex-start">
        <div>
          <p class="eyebrow">Energy · 今日能量</p>
          <h2 class="display" style="font-size: 22px; color: var(--green-950)">摄入与目标</h2>
        </div>
        <span class="badge"><SvgIcon name="sparkles" />V2 混合引擎</span>
      </div>

      <div class="row mt-24" style="gap: 28px; align-items: center; flex-wrap: wrap">
        <div class="ring-wrap">
          <svg width="168" height="168" viewBox="0 0 168 168">
            <circle cx="84" cy="84" r="70" fill="none" stroke="#ece8de" stroke-width="12" />
            <circle
              cx="84"
              cy="84"
              r="70"
              fill="none"
              stroke="#1e6b52"
              stroke-width="12"
              stroke-linecap="round"
              :stroke-dasharray="CIRC"
              :stroke-dashoffset="ringOffset"
              style="transition: stroke-dashoffset 1s var(--ease)"
            />
          </svg>
          <div class="ring-center">
            <span class="big num">{{ total.kcal }}</span>
            <span class="small">已摄入 kcal</span>
          </div>
        </div>

        <div class="grow" style="min-width: 240px">
          <div class="macro-row">
            <div v-for="m in macros" :key="m.name" class="macro-item">
              <span class="name">{{ m.name }}</span>
              <span class="bar" :class="m.cls"><i :style="{ width: m.pct + '%' }" /></span>
              <span class="val">{{ m.val }} / {{ m.target }}g</span>
            </div>
          </div>
          <div
            class="row-between mt-24"
            style="padding-top: 16px; border-top: 1px dashed var(--border)"
          >
            <div class="kpi">
              <span class="kpi-label">还可摄入</span>
              <span class="kpi-value num">{{ kcalLeft }} kcal</span>
            </div>
            <div class="kpi" style="text-align: right">
              <span class="kpi-label">今日目标</span>
              <span class="kpi-value num">{{ goal.kcal }} kcal</span>
            </div>
          </div>
        </div>
      </div>
    </article>

    <aside class="col" style="gap: 20px">
      <article class="card card-pad reveal d2">
        <div class="row-between">
          <p class="eyebrow" style="margin: 0">Goal · 目标进度</p>
          <RouterLink class="link small" to="/goal" style="color: var(--green-700); text-decoration: none">
            调整目标
          </RouterLink>
        </div>
        <div class="row mt-12" style="align-items: baseline; gap: 8px">
          <span class="num" style="font-size: 34px; color: var(--green-950)">
            {{ goal.currentWeight.toFixed(1) }}
          </span>
          <span class="small muted">
            kg / 目标 <b>{{ goal.targetWeight.toFixed(1) }}</b> kg
          </span>
        </div>
        <div class="bar mt-12"><i :style="{ width: weightBarWidth }" /></div>
        <div class="row-between small muted mt-8">
          <span>已减 <b class="num">{{ lostWeight }}</b> kg</span>
          <span>{{ goalPct }}%</span>
        </div>
        <div class="mt-16">
          <span class="small muted">连续记录</span>
          <div class="streak">
            <i v-for="(d, i) in streakDays" :key="d" :class="{ on: i < 5 }">{{ d }}</i>
          </div>
        </div>
      </article>

      <article class="card card-pad reveal d3">
        <div class="row-between">
          <p class="eyebrow" style="margin: 0">Water · 今日饮水</p>
          <span class="small num">{{ waterText }}</span>
        </div>
        <div class="water-track">
          <i
            v-for="i in 8"
            :key="i"
            :class="{ on: i <= store.waterCups }"
            :title="'记录第 ' + i + ' 杯（250ml）'"
            style="cursor: pointer"
            @click="onCup(i - 1)"
          >
            {{ i * 250 }}
          </i>
        </div>
        <p class="small muted mt-8">每格 250ml，点击记录一杯。</p>
      </article>
    </aside>
  </section>

  <!-- 今日推荐 -->
  <section class="mt-40 reveal d3">
    <div class="section-title">
      <h2>今天吃什么</h2>
      <RouterLink class="link" to="/recipes">
        全部食谱 <SvgIcon name="chevron-right" />
      </RouterLink>
    </div>
    <div class="grid g3">
      <!-- 加载骨架 -->
      <template v-if="recoLoading">
        <div v-for="i in 3" :key="i" class="card meal-card">
          <div class="sk" style="aspect-ratio: 4/3" />
          <div class="body">
            <div class="sk" style="height: 14px; width: 70%" />
            <div class="sk" style="height: 11px; width: 90%" />
          </div>
        </div>
      </template>

      <article
        v-for="(r, i) in mealRecos"
        :key="r.id"
        class="card meal-card reveal"
        :class="'d' + (i + 1)"
      >
        <div class="thumb">
          <img :src="r.img" :alt="r.name" />
          <span class="meal-tag">{{ r.mealType }}</span>
        </div>
        <div class="body">
          <h3>
            <RouterLink :to="'/recipes/' + r.id" style="text-decoration: none; color: inherit">
              {{ r.name }}
            </RouterLink>
          </h3>
          <div class="meal-meta">
            <span><SvgIcon name="flame" /> {{ r.kcal }} kcal</span>
            <span>蛋白 {{ r.p }}g</span>
            <span>匹配分 {{ r.score }}</span>
          </div>
          <div class="meal-foot">
            <span class="badge">{{ r.fit.join(' / ') }}</span>
            <button
              class="btn btn-sm btn-soft"
              :disabled="addedIds.includes(r.id)"
              @click="addToRecord(r)"
            >
              <SvgIcon :name="addedIds.includes(r.id) ? 'check' : 'plus'" />
              {{ addedIds.includes(r.id) ? '已记入' : '记入' + r.mealType }}
            </button>
          </div>
        </div>
      </article>
    </div>
  </section>

  <!-- 记录 + 建议 -->
  <section class="grid split mt-40 reveal d4">
    <article class="card">
      <div class="card-hd">
        <h3>今日饮食记录</h3>
        <RouterLink class="link-btn" to="/record">
          查看全部 <SvgIcon name="chevron-right" />
        </RouterLink>
      </div>
      <div class="card-bd">
        <div v-if="todayRecords.length" class="timeline">
          <div v-for="r in todayRecords" :key="r.id" class="tl-item">
            <span class="tl-time">{{ r.time }}</span>
            <div class="tl-body">
              <strong>{{ r.mealType }}</strong>
              <p>{{ recordNames(r) }}</p>
            </div>
            <span class="tl-kcal num">{{ recordKcal(r) }} kcal</span>
          </div>
        </div>
        <div v-else class="empty">
          <div class="empty-ico"><SvgIcon name="notebook" /></div>
          <h4>今天还没有记录</h4>
          <p>记录第一餐后，这里会显示热量与营养汇总。</p>
        </div>
      </div>
    </article>

    <aside class="col" style="gap: 20px">
      <article class="card card-pad">
        <p class="eyebrow" style="margin: 0">Advice · 今日建议</p>
        <ul style="display: flex; flex-direction: column; gap: 12px; margin-top: 14px">
          <li
            v-for="(t, i) in advice"
            :key="i"
            class="row"
            style="align-items: flex-start; gap: 10px; font-size: 12.5px; color: var(--text-2); line-height: 1.75"
          >
            <SvgIcon name="check-circle" style="color: var(--green-700); margin-top: 3px" />
            <span>{{ t }}</span>
          </li>
        </ul>
        <RouterLink class="btn btn-soft btn-sm btn-block mt-16" to="/assistant">
          <SvgIcon name="sparkles" />继续问 AI 助手
        </RouterLink>
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
    推荐结果基于健康档案与饮食目标生成（V2：SVD + GBDT + 规则护栏）。健康建议不构成医疗诊断，慢病管理请遵医嘱。
  </p>
</template>
