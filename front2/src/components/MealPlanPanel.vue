<script setup>
/* ============================================================
   MealPlanPanel.vue · 智能配餐（食谱库内切换视图）
   ------------------------------------------------------------
   和第一版 RecipeRecommend.vue 对齐的能力：
     · 1 / 7 / 30 天周期
     · 每天固定早 / 中 / 晚三餐
     · 导出 Word / Excel / PDF（打印另存）
   区别：视觉用 front2 的设计系统重做，数据走 /recommend/recipes，
   后端返回不足天数时按索引循环补齐（和第一版一致）。
   ============================================================ */
import { ref, computed } from 'vue'
import { useAppStore } from '@/stores/app'
import { recommendApi } from '@/services/api'
import { toast } from '@/composables/useToast'
import { exportPlanToWord, exportPlanToExcel, exportPlanToPdf } from '@/utils/mealPlanExport'
import { toRecipeLink } from '@/services/adapters/recommend'
import SvgIcon from '@/components/SvgIcon.vue'

const store = useAppStore()

const PLAN_OPTIONS = [
  { days: 1, label: '1 天' },
  { days: 7, label: '7 天' },
  { days: 30, label: '30 天' }
]

const planDays = ref(7)
const days = ref([])
const loading = ref(false)
const generatedDays = ref(0)

const goalLabel = computed(() => store.goalInfo?.goalType || '均衡饮食')
const targetKcal = computed(() => Number(store.goalInfo?.kcal) || 0)
/** 导出/标题都按「已生成的周期」算，避免改了周期但没重新生成时标签错位 */
const generatedLabel = computed(() => `${days.value.length ? generatedDays.value : planDays.value} 天`)

/* ------------------------------------------------------------
   结果持久化：点食谱进详情页会卸载本组件，返回时必须还原清单。
   按用户分开存，避免同一浏览器换账号后看到别人的配餐。
   ------------------------------------------------------------ */
const PLAN_KEY_PREFIX = 'sh_meal_plan_'
const storageKey = computed(() => PLAN_KEY_PREFIX + (store.session?.userId || 'guest'))

function readSavedPlan() {
  try {
    const raw = localStorage.getItem(storageKey.value)
    if (!raw) return null
    const data = JSON.parse(raw)
    if (!data || !Array.isArray(data.days) || !data.days.length) return null
    return data
  } catch (e) {
    return null
  }
}

function savePlan() {
  try {
    localStorage.setItem(
      storageKey.value,
      JSON.stringify({
        planDays: planDays.value,
        generatedDays: generatedDays.value,
        days: days.value,
        savedAt: Date.now()
      })
    )
  } catch (e) {
    /* 存储空间不足时只影响刷新后的还原，不阻断生成 */
  }
}

const savedPlan = readSavedPlan()
if (savedPlan) {
  planDays.value = [1, 7, 30].includes(savedPlan.planDays) ? savedPlan.planDays : 7
  generatedDays.value = savedPlan.generatedDays || savedPlan.days.length
  days.value = savedPlan.days
}

const dayKcal = (day) =>
  [day.breakfast, day.lunch, day.dinner].reduce(
    (sum, meal) => sum + (Number(meal?.kcal) || 0),
    0
  )

async function generate() {
  if (loading.value) return
  loading.value = true
  days.value = []

  const count = planDays.value
  const res = await recommendApi.plan({
    breakfastCount: count,
    lunchCount: count,
    dinnerCount: count
  })
  loading.value = false

  if (res.code !== 200) {
    toast(res.message, 'error')
    return
  }

  const groups = (res.data && res.data.groups) || []
  const pick = (key) => {
    const group = groups.find((g) => g.key === key)
    return (group && group.list) || []
  }
  const breakfasts = pick('breakfast')
  const lunches = pick('lunch')
  const dinners = pick('dinner')

  const result = []
  for (let i = 0; i < count; i += 1) {
    const day = {
      index: i + 1,
      label: `第 ${i + 1} 天`,
      breakfast: breakfasts.length ? breakfasts[i % breakfasts.length] : null,
      lunch: lunches.length ? lunches[i % lunches.length] : null,
      dinner: dinners.length ? dinners[i % dinners.length] : null
    }
    const kcal = dayKcal(day)
    day.kcal = kcal
    day.kcalText = kcal > 0 ? `${Math.round(kcal)} kcal` : '--'
    result.push(day)
  }

  days.value = result
  generatedDays.value = count
  savePlan()
  if (res.data && res.data.offline) {
    toast(res.message)
    return
  }
  toast(`已生成 ${count} 天配餐计划`)
}

function exportAs(type) {
  if (!days.value.length) return
  const title = `${goalLabel.value} · ${generatedLabel.value}配餐计划`
  const filename = `膳衡_${goalLabel.value}_${generatedLabel.value}配餐.${type === 'word' ? 'doc' : 'xls'}`

  if (type === 'word') {
    exportPlanToWord(filename, title, days.value)
    toast('Word 文件已开始下载')
    return
  }
  if (type === 'excel') {
    exportPlanToExcel(filename, title, days.value)
    toast('Excel 文件已开始下载')
    return
  }
  const opened = exportPlanToPdf(title, days.value)
  toast(opened ? '已打开打印窗口，可选择另存为 PDF' : '浏览器拦截了弹窗，请允许后重试', opened ? 'default' : 'error')
}

function mealKcal(meal) {
  return Number(meal?.kcal) || 0
}
</script>

<template>
  <div class="meal-plan">
    <!-- 生成栏 -->
    <section class="card plan-toolbar reveal">
      <div class="plan-toolbar-main">
        <div>
          <p class="eyebrow">Smart Meal Plan</p>
          <h2>智能配餐</h2>
          <p class="small muted">
            按当前饮食目标生成早 / 中 / 晚三餐清单，支持 1 天、7 天与 30 天。
          </p>
        </div>

        <div class="plan-controls">
          <div class="seg plan-seg">
            <button
              v-for="opt in PLAN_OPTIONS"
              :key="opt.days"
              type="button"
              :class="{ on: planDays === opt.days }"
              @click="planDays = opt.days"
            >
              {{ opt.label }}
            </button>
          </div>
          <button class="btn btn-primary" :disabled="loading" @click="generate">
            <SvgIcon name="sparkles" />{{ loading ? '生成中…' : days.length ? '重新生成' : '生成配餐' }}
          </button>
        </div>
      </div>

      <div class="plan-summary">
        <div>
          <span class="small muted">当前目标</span>
          <strong>{{ goalLabel }}</strong>
        </div>
        <div>
          <span class="small muted">每日热量目标</span>
          <strong>{{ targetKcal ? targetKcal + ' kcal' : '未设置' }}</strong>
        </div>
        <div>
          <span class="small muted">本次覆盖</span>
          <strong>{{ days.length ? generatedDays + ' 天' : '待生成' }}</strong>
        </div>
        <div v-if="days.length" class="plan-export">
          <span class="small muted">导出</span>
          <div class="row wrap" style="gap: 8px">
            <button class="btn btn-outline btn-sm" @click="exportAs('word')">Word</button>
            <button class="btn btn-outline btn-sm" @click="exportAs('excel')">Excel</button>
            <button class="btn btn-outline btn-sm" @click="exportAs('pdf')">PDF</button>
          </div>
        </div>
      </div>
    </section>

    <!-- 生成中 -->
    <div v-if="loading" class="plan-grid mt-24">
      <article v-for="i in 3" :key="i" class="card plan-card">
        <div class="sk" style="height: 18px; width: 46%; margin-bottom: 16px" />
        <div v-for="j in 3" :key="j" class="sk" style="height: 34px; margin-bottom: 10px" />
      </article>
    </div>

    <!-- 结果 -->
    <section v-else-if="days.length" class="mt-24">
      <div class="section-title">
        <h2>{{ generatedLabel }}配餐清单</h2>
        <span class="small muted">每天三餐 · 共 {{ days.length }} 天</span>
      </div>

      <div class="plan-grid">
        <article v-for="(day, i) in days" :key="day.index" class="card plan-card reveal" :class="'d' + ((i % 3) + 1)">
          <div class="plan-card-head">
            <h3>{{ day.label }}</h3>
            <span class="plan-kcal">
              <SvgIcon name="flame" />{{ day.kcalText }}
            </span>
          </div>

          <div class="plan-meals">
            <div
              v-for="meal in [
                { key: 'breakfast', label: '早餐', data: day.breakfast },
                { key: 'lunch', label: '午餐', data: day.lunch },
                { key: 'dinner', label: '晚餐', data: day.dinner }
              ]"
              :key="meal.key"
              class="plan-meal"
            >
              <span class="plan-meal-label">{{ meal.label }}</span>
              <RouterLink
                v-if="meal.data && meal.data.id"
                class="plan-meal-name"
                :to="toRecipeLink(meal.data)"
              >
                {{ meal.data.name }}
              </RouterLink>
              <span v-else class="plan-meal-name muted">{{ meal.data ? meal.data.name : '暂无可用食谱' }}</span>
              <span class="plan-meal-kcal">
                {{ mealKcal(meal.data) ? mealKcal(meal.data) + ' kcal' : '--' }}
              </span>
            </div>
          </div>
        </article>
      </div>
    </section>

    <!-- 空状态 -->
    <div v-else class="empty mt-24">
      <div class="empty-ico"><SvgIcon name="utensils" /></div>
      <h4>还没有配餐计划</h4>
      <p>选择 1 天、7 天或 30 天，点「生成配餐」后会按早 / 中 / 晚排好清单，可再导出 Word、Excel 或 PDF。</p>
    </div>
  </div>
</template>

<style scoped>
.meal-plan {
  display: flex;
  flex-direction: column;
}

.plan-toolbar {
  padding: 22px;
}

.plan-toolbar-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  flex-wrap: wrap;
}

.plan-toolbar h2 {
  margin: 6px 0 8px;
}

.plan-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.plan-seg {
  min-width: 210px;
}

.plan-summary {
  display: flex;
  gap: 28px;
  flex-wrap: wrap;
  margin-top: 20px;
  padding-top: 18px;
  border-top: 1px solid var(--border);
}

.plan-summary > div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.plan-summary strong {
  color: var(--text);
  font-size: 18px;
}

.plan-export {
  margin-left: auto;
}

.plan-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
  gap: 16px;
}

.plan-card {
  padding: 18px;
}

.plan-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.plan-card-head h3 {
  margin: 0;
  font-size: 16px;
}

.plan-kcal {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--green-700);
  font-size: 13px;
  white-space: nowrap;
}

.plan-kcal :deep(.ic) {
  width: 13px;
  height: 13px;
}

.plan-meals {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.plan-meal {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  background: var(--green-050);
}

.plan-meal-label {
  font-size: 12px;
  color: var(--text-3);
}

.plan-meal-name {
  color: var(--text);
  font-weight: 600;
  text-decoration: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plan-meal-name:hover {
  color: var(--green-700);
}

.plan-meal-kcal {
  color: var(--text-3);
  font-size: 12px;
  white-space: nowrap;
}

@media (max-width: 720px) {
  .plan-toolbar-main,
  .plan-export {
    width: 100%;
    margin-left: 0;
  }

  .plan-toolbar h2 {
    font-size: 20px;
  }

  .plan-seg {
    width: 100%;
  }
}
</style>
