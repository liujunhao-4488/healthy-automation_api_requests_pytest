<script setup>
/* ============================================================
   RecipeDetailView.vue · 食谱详情
   ------------------------------------------------------------
   对应静态版 pages/recipe-detail.html?id=x，现在地址是 /recipes/:id。

   原版是「拿 id → 拼一大段 innerHTML」，这里改成模板 + computed：
   营养占比、「目标匹配」三条进度条、相似食谱都由数据算出来。
   ============================================================ */
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useAppStore, TODAY } from '@/stores/app'
import { recipesApi, recordsApi } from '@/services/api'
import { toast } from '@/composables/useToast'
import SvgIcon from '@/components/SvgIcon.vue'

const route = useRoute()
const store = useAppStore()

const recipe = ref(null)
const loading = ref(true)
const errorMsg = ref('')
const added = ref(false)
const saving = ref(false)
/** 相似食谱的候选池：原来直接读本地 DB.recipes，接真接口后要换成接口数据 */
const pool = ref([])

const goal = computed(() => store.goalInfo)

async function loadPool() {
  const res = await recipesApi.list({ page: 1, pageSize: 999 })
  if (res.code === 200) pool.value = res.data.list
}

async function load(id) {
  loading.value = true
  errorMsg.value = ''
  added.value = false
  const res = await recipesApi.get(id)
  loading.value = false
  if (res.code !== 200) {
    errorMsg.value = res.message
    recipe.value = null
    return
  }
  recipe.value = res.data
  document.title = res.data.name + ' · 膳衡'
}

onMounted(() => {
  loadPool()
  load(route.params.id)
})
// 从相似食谱跳转时组件被复用，靠 watch 重新加载
watch(
  () => route.params.id,
  (id) => {
    if (id) load(id)
  }
)

/* ---------------- 营养占比 ---------------- */
const nutrition = computed(() => {
  const r = recipe.value
  if (!r) return null
  const g = goal.value
  const pTarget = Math.round((g.kcal * g.proteinPct) / 100 / 4)
  const fTarget = Math.round((g.kcal * g.fatPct) / 100 / 9)
  return {
    kcalPct: Math.round((r.kcal / g.kcal) * 100),
    pTarget,
    fTarget,
    pPct: Math.round((r.p / pTarget) * 100),
    fPct: Math.round((r.f / fTarget) * 100),
    pShare: Math.round(((r.p * 4) / r.kcal) * 100),
    fShare: Math.round(((r.f * 9) / r.kcal) * 100)
  }
})

/** 「目标匹配」的三条进度条 */
const matchBars = computed(() => {
  const r = recipe.value
  const n = nutrition.value
  if (!r || !n) return []
  return [
    { name: '热量', val: r.kcal, target: goal.value.kcal, unit: 'kcal', cls: ' amber', pct: n.kcalPct },
    { name: '蛋白质', val: r.p, target: n.pTarget, unit: 'g', cls: '', pct: n.pPct },
    { name: '脂肪', val: r.f, target: n.fTarget, unit: 'g', cls: ' clay', pct: n.fPct }
  ]
})

/* ---------------- 相似食谱 ---------------- */
const similar = computed(() => {
  const r = recipe.value
  if (!r || !pool.value.length) return []
  const rest = pool.value.filter((x) => x.id !== r.id)
  const sameMeal = rest.filter((x) => x.mealType === r.mealType)
  const others = rest
    .filter((x) => x.mealType !== r.mealType)
    .sort((a, b) => {
      const sa =
        a.fit.filter((f) => r.fit.includes(f)).length + (a.cuisine === r.cuisine ? 1 : 0)
      const sb =
        b.fit.filter((f) => r.fit.includes(f)).length + (b.cuisine === r.cuisine ? 1 : 0)
      return sb - sa
    })
  return sameMeal.concat(others).slice(0, 3)
})

/* ---------------- 记入今日 ---------------- */
const addHint = computed(() => {
  const r = recipe.value
  if (!r) return ''
  const t = store.totals(TODAY)
  const after = t.kcal + r.kcal
  const pct = Math.round((after / goal.value.kcal) * 100)
  return (
    '今日已摄入 ' + t.kcal.toLocaleString('zh-CN') + ' kcal，加入本餐后约 ' +
    after.toLocaleString('zh-CN') + ' kcal，占每日目标 ' + pct + '%。'
  )
})

async function addToRecord() {
  const r = recipe.value
  if (!r) return
  saving.value = true
  const res = await recordsApi.submit({
    mealType: r.mealType,
    time: store.nowTime(),
    note: '来自食谱「' + r.name + '」',
    items: [{ name: r.name, amount: 1, unit: '份', kcal: r.kcal, p: r.p, c: r.c, f: r.f }]
  })
  saving.value = false
  if (res.code !== 200) {
    toast(res.message, 'error')
    return
  }
  added.value = true
  toast('已记入今日' + r.mealType + '：' + r.name)
}

async function toggleFav() {
  const r = recipe.value
  const res = await recipesApi.collect(r.id)
  if (res.code !== 200) {
    toast(res.message, 'error')
    return
  }
  toast(res.data.collected ? '已收藏「' + r.name + '」' : '已取消收藏「' + r.name + '」')
}
</script>

<template>
  <div class="row-between mb-16">
    <RouterLink class="detail-link" to="/recipes">
      <SvgIcon name="arrow-left" />返回食谱库
    </RouterLink>
    <span class="small muted">营养口径：每份 · 数据更新于 2026-10-18</span>
  </div>

  <!-- 加载骨架 -->
  <div v-if="loading">
    <div class="sk" style="aspect-ratio: 16/8; border-radius: var(--r-xl)" />
    <section class="grid split mt-24">
      <div class="col" style="gap: 20px">
        <div class="card card-pad">
          <div class="sk" style="height: 16px; width: 32%" />
          <div class="grid g4 mt-16" style="gap: 12px">
            <div v-for="i in 4" :key="i" class="sk" style="height: 58px" />
          </div>
        </div>
        <div class="card card-pad">
          <div class="sk" style="height: 16px; width: 28%" />
          <div class="sk mt-16" style="height: 12px; width: 92%" />
          <div class="sk mt-8" style="height: 12px; width: 86%" />
          <div class="sk mt-8" style="height: 12px; width: 90%" />
        </div>
      </div>
      <aside class="col" style="gap: 20px">
        <div class="card card-pad">
          <div class="sk" style="height: 16px; width: 40%" />
          <div class="sk mt-16" style="height: 40px; width: 52%" />
        </div>
        <div class="card card-pad">
          <div class="sk" style="height: 16px; width: 40%" />
          <div class="sk mt-16" style="height: 12px" />
          <div class="sk mt-12" style="height: 12px" />
        </div>
      </aside>
    </section>
  </div>

  <!-- 找不到 -->
  <div v-else-if="errorMsg" class="card card-pad mt-24">
    <div class="empty">
      <div class="empty-ico"><SvgIcon name="bowl" /></div>
      <h4>食谱不存在或已下架</h4>
      <p>{{ errorMsg || '该食谱可能已被移除，返回食谱库看看其他选择。' }}</p>
    </div>
    <div style="text-align: center; padding-bottom: 26px">
      <RouterLink class="btn btn-primary btn-sm" to="/recipes">
        <SvgIcon name="arrow-left" />返回食谱库
      </RouterLink>
    </div>
  </div>

  <!-- 正文 -->
  <template v-else-if="recipe">
    <div class="recipe-hero hero-detail reveal">
      <img :src="recipe.img" :alt="recipe.name" />
      <div class="overlay-text">
        <div class="row wrap" style="gap: 8px; margin-bottom: 10px">
          <span class="badge" style="background: var(--green-100); color: var(--green-900)">
            {{ recipe.mealType }}
          </span>
          <span class="badge" style="background: var(--surface); color: var(--green-900)">
            {{ recipe.cuisine }}
          </span>
          <span class="badge" style="background: var(--surface); color: var(--green-900)">
            {{ recipe.level }}
          </span>
          <span v-if="recipe.custom" class="badge amber">我的自定义</span>
        </div>
        <h1>{{ recipe.name }}</h1>
        <div class="meta">
          <span><SvgIcon name="clock" /> {{ recipe.time }} 分钟</span>
          <span><SvgIcon name="utensils" /> {{ recipe.servings }} 人份</span>
          <span v-if="!recipe.custom"><SvgIcon name="star" /> {{ recipe.rating.toFixed(1) }} 分</span>
          <span v-if="recipe.custom"><SvgIcon name="star" /> 我创建的食谱</span>
          <span v-if="!recipe.custom"><SvgIcon name="eye" /> {{ recipe.views.toLocaleString('zh-CN') }} 次浏览</span>
          <span v-if="!recipe.custom"><SvgIcon name="bookmark" /> {{ recipe.collects.toLocaleString('zh-CN') }} 收藏</span>
        </div>
      </div>
      <button
        class="hero-fav"
        :class="{ on: store.isRecipeCollected(recipe.id) }"
        aria-label="收藏本食谱"
        @click="toggleFav"
      >
        <SvgIcon name="bookmark" />
      </button>
    </div>

    <p class="page-sub mt-16" style="max-width: 760px">{{ recipe.desc }}</p>

    <section class="grid split mt-24 reveal d1">
      <div class="col" style="gap: 20px">
        <!-- 营养概览 -->
        <article class="card card-pad">
          <div class="row-between">
            <p class="eyebrow" style="margin: 0">Nutrition · 营养概览</p>
            <span class="tag">整份 / {{ recipe.servings }} 人份</span>
          </div>
          <div class="grid g4 mt-16" style="gap: 12px">
            <div class="kpi">
              <span class="kpi-label">热量</span><span class="kpi-value">{{ recipe.kcal }}</span><span class="kpi-foot">kcal</span>
            </div>
            <div class="kpi">
              <span class="kpi-label">蛋白质</span><span class="kpi-value">{{ recipe.p }}</span><span class="kpi-foot">g</span>
            </div>
            <div class="kpi">
              <span class="kpi-label">碳水</span><span class="kpi-value">{{ recipe.c }}</span><span class="kpi-foot">g</span>
            </div>
            <div class="kpi">
              <span class="kpi-label">脂肪</span><span class="kpi-value">{{ recipe.f }}</span><span class="kpi-foot">g</span>
            </div>
          </div>
          <div class="row wrap mt-16" style="gap: 8px">
            <span class="tag">膳食纤维 {{ recipe.fiber }} g</span>
            <span class="tag">蛋白质供能 {{ nutrition.pShare }}%</span>
            <span class="tag">脂肪供能 {{ nutrition.fShare }}%</span>
          </div>
        </article>

        <!-- 食材清单 -->
        <article class="card">
          <div class="card-hd">
            <h3>食材清单</h3>
            <span class="badge">{{ recipe.ingredients.length }} 种食材</span>
          </div>
          <div class="card-bd">
            <div class="ing-list">
              <div v-for="(it, i) in recipe.ingredients" :key="i" class="ing-row">
                <span>{{ it.name }}</span>
                <span class="amt">{{ it.amount }}{{ it.unit ? ' ' + it.unit : '' }}</span>
              </div>
              <p v-if="!recipe.ingredients.length" class="small muted" style="padding: 6px 0">
                还没有填写食材清单，可返回食谱库编辑补充。
              </p>
            </div>
          </div>
        </article>

        <!-- 制作步骤 -->
        <article class="card">
          <div class="card-hd">
            <h3>制作步骤</h3>
            <span class="small muted">约 {{ recipe.time }} 分钟</span>
          </div>
          <div class="card-bd">
            <ol class="step-list">
              <li v-for="(s, i) in recipe.steps" :key="i">{{ s }}</li>
            </ol>
          </div>
        </article>

        <div v-if="recipe.tips" class="alert-inline green">
          <SvgIcon name="sparkles" />
          <span><b>小贴士</b>：{{ recipe.tips }}</span>
        </div>
      </div>

      <aside class="col" style="gap: 20px">
        <!-- 份量说明 -->
        <article class="card card-pad">
          <p class="eyebrow" style="margin: 0">Serving · 份量说明</p>
          <div class="row mt-12" style="align-items: baseline; gap: 8px">
            <span class="num" style="font-size: 34px; color: var(--green-950)">{{ recipe.servings }}</span>
            <span class="small muted">人份 / 整份</span>
          </div>
          <p class="small muted mt-8" style="line-height: 1.8">
            营养数据按整份统计。若分成 2 次食用，请将热量与三大营养素各自减半；食材用量与步骤仍以整份为准。
          </p>
          <div class="row-between mt-12">
            <span class="small muted">备餐时间</span><span class="small num">{{ recipe.time }} 分钟</span>
          </div>
          <div class="row-between mt-8">
            <span class="small muted">难度</span><span class="small">{{ recipe.level }}</span>
          </div>
        </article>

        <!-- 目标匹配 -->
        <article class="card card-pad">
          <div class="row-between">
            <p class="eyebrow" style="margin: 0">Goal Match · 目标匹配</p>
            <RouterLink class="link-btn" to="/goal">
              调整目标<SvgIcon name="chevron-right" />
            </RouterLink>
          </div>
          <p class="small muted mt-8">
            当前目标：{{ goal.goalType }} · 每日 {{ goal.kcal.toLocaleString('zh-CN') }} kcal
          </p>
          <div class="col mt-16" style="gap: 14px">
            <div v-for="b in matchBars" :key="b.name">
              <div class="row-between small" style="margin-bottom: 6px">
                <span style="color: var(--text-2)">{{ b.name }}</span>
                <span class="num" style="color: var(--text-3)">
                  {{ b.val }} / {{ b.target }} {{ b.unit }} · {{ b.pct }}%
                </span>
              </div>
              <div class="bar" :class="b.cls"><i :style="{ width: Math.min(100, b.pct) + '%' }" /></div>
            </div>
          </div>
          <p class="small muted mt-12" style="line-height: 1.7">
            占比为本餐相对每日目标；三餐可按 30% / 40% / 30% 微调，剩余额度留给加餐。
          </p>
        </article>

        <!-- 记录 -->
        <article class="card card-pad">
          <p class="eyebrow" style="margin: 0">Action · 记录</p>
          <h3 class="display" style="font-size: 19px; color: var(--green-950); margin-top: 8px">
            把这一份记进今天
          </h3>
          <p class="small muted mt-8" style="line-height: 1.7">{{ addHint }}</p>
          <button
            class="btn btn-primary btn-block mt-16"
            :disabled="saving || added"
            @click="addToRecord"
          >
            <SvgIcon :name="added ? 'check-circle' : 'plus'" />
            {{ added ? '已记入今日' + recipe.mealType : saving ? '保存中' : '记入今日饮食记录' }}
          </button>
          <RouterLink class="btn btn-soft btn-block mt-8" to="/assistant">
            <SvgIcon name="sparkles" />继续问 AI
          </RouterLink>
          <RouterLink
            class="link-btn mt-12"
            to="/record"
            style="display: flex; justify-content: center"
          >
            查看今日饮食记录<SvgIcon name="chevron-right" />
          </RouterLink>
        </article>
      </aside>
    </section>

    <!-- 相似食谱 -->
    <section class="mt-40 reveal d2">
      <div class="section-title">
        <h2>相似食谱</h2>
        <RouterLink class="link" to="/recipes">
          浏览全部<SvgIcon name="chevron-right" />
        </RouterLink>
      </div>
      <div class="grid g3">
        <article v-for="s in similar" :key="s.id" class="card recipe-card">
          <div class="cover">
            <RouterLink :to="'/recipes/' + s.id">
              <img :src="s.img" :alt="s.name" />
            </RouterLink>
            <span class="fit">{{ s.fit.join(' / ') }}</span>
          </div>
          <div class="body">
            <h3>
              <RouterLink :to="'/recipes/' + s.id" style="text-decoration: none; color: inherit">
                {{ s.name }}
              </RouterLink>
            </h3>
            <div class="meal-meta">
              <span><SvgIcon name="flame" /> {{ s.kcal }} kcal</span>
              <span>蛋白 {{ s.p }}g</span>
              <span>{{ s.mealType }}</span>
            </div>
          </div>
        </article>
      </div>
    </section>
  </template>

  <p class="small muted mt-32" style="text-align: center">
    营养数据来自平台食材库的标准口径，实际烹饪会因用油与火候产生差异。本文不构成医疗诊断，慢病管理请遵医嘱。
  </p>
</template>

<style scoped>
.detail-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--green-700);
  text-decoration: none;
  font-size: 12.5px;
}
.detail-link .ic {
  width: 15px;
  height: 15px;
}
.hero-detail {
  aspect-ratio: 16 / 8;
}
.hero-fav {
  position: absolute;
  right: 32px;
  bottom: 30px;
  z-index: 2;
  width: 46px;
  height: 46px;
  border-radius: 50%;
  border: 0;
  background: var(--surface);
  color: var(--green-900);
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: 0.16s var(--ease);
  box-shadow: var(--shadow-sm);
}
.hero-fav:hover {
  color: var(--clay-600);
}
.hero-fav.on {
  color: var(--clay-600);
}
.hero-fav .ic {
  width: 20px;
  height: 20px;
}
@media (max-width: 720px) {
  .hero-detail {
    aspect-ratio: 5 / 4;
  }
  .hero-detail .overlay-text {
    padding: 20px 66px 20px 20px;
  }
  .hero-detail .overlay-text h1 {
    font-size: 23px;
    line-height: 1.32;
  }
  .hero-fav {
    right: 14px;
    bottom: 14px;
    width: 40px;
    height: 40px;
  }
}
</style>
