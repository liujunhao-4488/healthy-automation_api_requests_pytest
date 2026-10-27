<script setup>
/* ============================================================
   RecipesView.vue · 食谱库
   ------------------------------------------------------------
   对应静态版 pages/recipes.html。

   筛选分两层（和原版一致）：
     · 餐次 / 目标 / 关键词 → 交给接口过滤
     · 菜系 / 排序 / 「换一批」→ 拿到结果后在本地处理

   所以 load() 会循环把分页拉完，再在 computed 里做菜系过滤、
   排序和轮转，换页只是切数组，不用再请求接口。
   ============================================================ */
import { ref, reactive, computed, onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { recipesApi } from '@/services/api'
import { toast } from '@/composables/useToast'
import { confirmDialog } from '@/composables/useConfirm'
import SvgIcon from '@/components/SvgIcon.vue'
import imgChicken from '@/assets/recipe-chicken.jpg'
import imgSalmon from '@/assets/recipe-salmon.jpg'
import imgOatmeal from '@/assets/recipe-oatmeal.jpg'
import imgSoup from '@/assets/recipe-soup.jpg'

const store = useAppStore()

const PAGE_SIZE = 6
const SORT_LABEL = { recommend: '推荐度', kcal: '热量从低到高', protein: '蛋白从高到低' }

const MEAL_OPTIONS = ['全部', '早餐', '午餐', '晚餐', '加餐']
const FIT_OPTIONS = ['全部', '减脂', '增肌', '控糖', '维持']
const CUISINE_OPTIONS = ['全部', '中式', '西式', '轻食']

const state = reactive({
  mealType: '全部',
  fit: '全部',
  cuisine: '全部',
  sort: 'recommend',
  keyword: '',
  page: 1,
  seed: 0
})

/** 接口一次拉回来的完整候选（已按餐次/目标/关键词过滤） */
const rawList = ref([])
const totalRaw = ref(0)
const loading = ref(true)
/** 请求序号：连续改筛选时只认最后一次，避免旧结果覆盖新结果 */
let seq = 0

/* ---------------- 匹配分 ---------------- */
function scoreOf(r) {
  const goal = store.goalInfo
  let s = 30
  if (r.fit.includes(goal.goalType)) s += 22
  const gap = Math.abs(r.kcal - goal.kcal / goal.meals)
  s += Math.max(0, 20 - gap / 18)
  s += Math.min(12, r.p / 4)
  s += Math.min(8, r.fiber / 1.4)
  s += r.rating * 2
  return Math.min(96, Math.round(s))
}

/* ---------------- 本地处理：菜系 → 排序 → 换一批 ---------------- */
const viewList = computed(() => {
  let list = rawList.value
  if (state.cuisine !== '全部') list = list.filter((r) => r.cuisine === state.cuisine)

  list = list.slice()
  if (state.sort === 'kcal') list.sort((a, b) => a.kcal - b.kcal)
  else if (state.sort === 'protein') list.sort((a, b) => b.p - a.p)
  else list.sort((a, b) => scoreOf(b) - scoreOf(a) || b.rating - a.rating)

  if (state.sort === 'recommend' && state.seed && list.length) {
    const k = (state.seed * 3) % list.length
    list = list.slice(k).concat(list.slice(0, k))
  }
  return list
})

const total = computed(() => viewList.value.length)
const pages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))
const paged = computed(() =>
  viewList.value.slice((state.page - 1) * PAGE_SIZE, state.page * PAGE_SIZE)
)

const resultMeta = computed(() =>
  loading.value ? '正在检索…' : '共 ' + total.value + ' 道 · ' + SORT_LABEL[state.sort] + '排序'
)

/* ---------------- 拉数据 ---------------- */
async function load() {
  const my = ++seq
  loading.value = true

  let all = []
  let page = 1
  let totalCount = Infinity
  // 上限 40 页：真接口实测 193 条，按 PAGE_SIZE(6) 需要 33 页。
  // 原来写死 12（=72 条）是为 mock 的 8 条准备的，接真数据会把列表截断成 72 条。
  // mock 分支不会受影响：totalCount 只有 8，第二圈就退出循环。
  while (all.length < totalCount && page <= 40) {
    const res = await recipesApi.list({
      mealType: state.mealType,
      fit: state.fit,
      keyword: state.keyword,
      page,
      pageSize: PAGE_SIZE
    })
    if (my !== seq) return // 有更新的请求了，放弃这次
    if (res.code !== 200) {
      loading.value = false
      toast(res.message, 'error')
      rawList.value = []
      return
    }
    totalCount = res.data.total
    all = all.concat(res.data.list)
    if (!res.data.list.length) break
    page++
  }
  if (my !== seq) return

  loading.value = false
  totalRaw.value = totalCount
  rawList.value = all
  if (state.page > pages.value) state.page = pages.value
}

/* ---------------- 交互 ---------------- */
function pickChip(group, value) {
  state[group] = value
  state.page = 1
  state.seed = 0
  load()
}

function onSortChange() {
  state.seed = 0
  state.page = 1
}

function onRefresh() {
  state.sort = 'recommend'
  state.seed += 1
  state.page = 1
  toast('已换一批推荐')
}

function clearFilters() {
  state.mealType = '全部'
  state.fit = '全部'
  state.cuisine = '全部'
  state.keyword = ''
  state.sort = 'recommend'
  state.page = 1
  state.seed = 0
  load()
}

/* 搜索防抖 300ms */
let timer = null
const keywordInput = ref('')
function onSearchInput() {
  clearTimeout(timer)
  timer = setTimeout(() => {
    state.keyword = keywordInput.value.trim()
    state.page = 1
    state.seed = 0
    load()
  }, 300)
}
function onSearchEnter() {
  clearTimeout(timer)
  state.keyword = keywordInput.value.trim()
  state.page = 1
  load()
}

async function toggleCollect(r) {
  const res = await recipesApi.collect(r.id)
  if (res.code !== 200) {
    toast(res.message, 'error')
    return
  }
  toast(res.data.collected ? '已收藏「' + r.name + '」' : '已取消收藏「' + r.name + '」')
  // 收藏会改变「我的食谱」数量，无论在哪个视图都刷新一下
  loadCollected()
}

/* ---------------- 自定义食谱 ---------------- */
const IMG_OPTIONS = [
  { label: '鸡胸轻食', value: imgChicken },
  { label: '三文鱼', value: imgSalmon },
  { label: '燕麦早餐', value: imgOatmeal },
  { label: '暖汤', value: imgSoup }
]
const customList = ref([])
const collectedList = ref([])
/* 自建食谱单独展示，收藏区只放平台食谱，避免同一道菜出现两次 */
const collectedDisplay = computed(() => collectedList.value.filter((r) => !r.custom))
const modalOpen = ref(false)
const editingId = ref(0)
const savingCustom = ref(false)
/* 两个视图：library = 平台食谱库，mine = 自建 + 收藏 */
const TAB_KEY = 'sh_recipes_tab'
const tab = ref('library')

function switchTab(next) {
  if (tab.value === next) return
  tab.value = next
  localStorage.setItem(TAB_KEY, next)
  if (next === 'mine') {
    loadCustom()
    loadCollected()
  }
}

function blankForm() {
  return {
    name: '', mealType: '午餐', cuisine: '轻食', time: 20, level: '简单', servings: 1,
    img: imgChicken, kcal: '', p: '', c: '', f: '', fiber: '',
    desc: '', ingredients: '', steps: '', tips: '', fit: ['减脂']
  }
}
const form = reactive(blankForm())

async function loadCustom() {
  const res = await recipesApi.custom()
  if (res.code === 200) customList.value = res.data
}

async function loadCollected() {
  const res = await recipesApi.collected()
  if (res.code !== 200) return
  // 后端返回已收藏食谱；自建食谱的收藏由本地状态补上，按 id 去重
  const map = new Map()
  const customCollected = customList.value.filter((r) => store.recipeCollectIds.includes(r.id))
  ;(res.data || []).concat(customCollected).forEach((r) => map.set(r.id, r))
  collectedList.value = Array.from(map.values())
}

function openCreate() {
  editingId.value = 0
  Object.assign(form, blankForm())
  modalOpen.value = true
}

function openEdit(r) {
  editingId.value = r.id
  Object.assign(form, {
    name: r.name,
    mealType: r.mealType,
    cuisine: r.cuisine,
    time: r.time,
    level: r.level,
    servings: r.servings,
    img: r.img,
    kcal: r.kcal,
    p: r.p,
    c: r.c,
    f: r.f,
    fiber: r.fiber,
    desc: r.desc,
    tips: r.tips || '',
    ingredients: (r.ingredients || []).map((i) => [i.name, i.amount, i.unit].filter(Boolean).join(' ')).join('\n'),
    steps: (r.steps || []).join('\n'),
    fit: (r.fit || []).slice()
  })
  modalOpen.value = true
}

function toggleFit(value) {
  const i = form.fit.indexOf(value)
  if (i > -1) form.fit.splice(i, 1)
  else form.fit.push(value)
}

function parseIngredient(line) {
  const parts = line.trim().split(/\s+/).filter(Boolean)
  if (!parts.length) return null
  if (parts.length === 1) return { name: parts[0], amount: '', unit: '' }
  if (parts.length === 2) return { name: parts[0], amount: parts[1], unit: '' }
  return {
    name: parts.slice(0, parts.length - 2).join(' '),
    amount: parts[parts.length - 2],
    unit: parts[parts.length - 1]
  }
}

async function saveCustom() {
  if (savingCustom.value) return
  const name = form.name.trim()
  const kcal = Number(form.kcal) || 0
  const steps = form.steps.split('\n').map((s) => s.trim()).filter(Boolean)
  if (!name) { toast('请填写食谱名称', 'error'); return }
  if (kcal <= 0) { toast('请填写大于 0 的热量', 'error'); return }
  if (!steps.length) { toast('请至少填写一个制作步骤', 'error'); return }
  if (!form.fit.length) { toast('请至少选择一个适宜目标', 'error'); return }

  const payload = {
    id: editingId.value || undefined,
    name,
    mealType: form.mealType,
    cuisine: form.cuisine,
    time: Number(form.time) || 20,
    level: form.level,
    servings: Number(form.servings) || 1,
    img: form.img,
    kcal,
    p: Number(form.p) || 0,
    c: Number(form.c) || 0,
    f: Number(form.f) || 0,
    fiber: Number(form.fiber) || 0,
    desc: form.desc.trim() || '自定义食谱。',
    fit: form.fit.slice(),
    ingredients: form.ingredients.split('\n').map(parseIngredient).filter(Boolean),
    steps,
    tips: form.tips.trim()
  }

  savingCustom.value = true
  const res = await recipesApi.save(payload)
  savingCustom.value = false
  if (res.code !== 200) { toast(res.message, 'error'); return }
  modalOpen.value = false
  toast(res.message)
  loadCustom()
}

async function removeCustom(r) {
  const ok = await confirmDialog('删除「' + r.name + '」后不可恢复，确定继续吗？', {
    title: '删除自定义食谱',
    okText: '删除',
    danger: true
  })
  if (!ok) return
  const res = await recipesApi.remove(r.id)
  toast(res.message)
  loadCustom().then(loadCollected)
}

function goPage(delta) {
  const next = state.page + delta
  if (next < 1 || next > pages.value) return
  state.page = next
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(() => {
  const queryTab = new URLSearchParams(window.location.search).get('tab')
  const savedTab = localStorage.getItem(TAB_KEY)
  tab.value = queryTab === 'mine' || (!queryTab && savedTab === 'mine') ? 'mine' : 'library'
  load()
  loadCustom().then(loadCollected)
})
</script>

<template>
  <header class="page-head reveal">
    <div>
      <p class="eyebrow">{{ tab === 'library' ? 'Recipe Library' : 'My Recipes' }}</p>
      <h1 class="page-title">{{ tab === 'library' ? '食谱库' : '我的食谱' }}</h1>
      <p class="page-sub">
        {{ tab === 'library'
          ? '按餐次、目标与营养密度筛选，找到更贴合你的搭配。'
          : '自己创建的食谱与收藏的食谱，集中在这里管理。' }}
      </p>
    </div>
    <div v-if="tab === 'library'" class="page-actions">
      <div class="search-box" style="min-width: 240px">
        <SvgIcon name="search" />
        <input
          v-model="keywordInput"
          class="input"
          type="search"
          placeholder="搜索食谱名称或食材"
          aria-label="搜索食谱"
          @input="onSearchInput"
          @keydown.enter="onSearchEnter"
        />
      </div>
      <button class="btn btn-outline" @click="onRefresh">
        <SvgIcon name="refresh" />换一批
      </button>
    </div>
    <div v-else class="page-actions">
      <button class="btn btn-primary" @click="openCreate">
        <SvgIcon name="plus" />新建食谱
      </button>
    </div>
  </header>

  <!-- 视图切换：平台食谱库 / 我的食谱 -->
  <div class="seg recipe-tabs reveal d1">
    <button type="button" :class="{ on: tab === 'library' }" @click="switchTab('library')">
      <SvgIcon name="book-open" />食谱库
    </button>
    <button type="button" :class="{ on: tab === 'mine' }" @click="switchTab('mine')">
      <SvgIcon name="user" />我的食谱
      <span v-if="customList.length + collectedDisplay.length" class="nav-badge">
        {{ customList.length + collectedDisplay.length }}
      </span>
    </button>
  </div>

  <!-- ========== 食谱库 ========== -->
  <div v-show="tab === 'library'">

  <div class="alert-inline green reveal d1" style="margin-bottom: 20px">
    <SvgIcon name="sparkles" />
    <span>
      <b>今日推荐逻辑 · V2 混合引擎</b>：先用 SVD 协同过滤召回候选，再由 GBDT 结合健康档案、饮食目标与历史记录排序，规则护栏拦截过敏原与慢病禁忌。卡片上的「匹配分」综合单餐热量差、蛋白密度、纤维密度与目标契合度，满分 100，仅代表适配程度。
    </span>
  </div>

  <!-- 筛选栏 -->
  <section class="card filter-bar reveal d2">
    <div class="filter-row">
      <span class="filter-label">餐次</span>
      <div class="row wrap" style="gap: 8px">
        <button
          v-for="opt in MEAL_OPTIONS"
          :key="opt"
          class="chip"
          :class="{ on: state.mealType === opt }"
          @click="pickChip('mealType', opt)"
        >
          {{ opt }}
        </button>
      </div>
    </div>
    <div class="filter-row">
      <span class="filter-label">目标</span>
      <div class="row wrap" style="gap: 8px">
        <button
          v-for="opt in FIT_OPTIONS"
          :key="opt"
          class="chip"
          :class="{ on: state.fit === opt }"
          @click="pickChip('fit', opt)"
        >
          {{ opt }}
        </button>
      </div>
    </div>
    <div class="filter-row">
      <span class="filter-label">菜系</span>
      <div class="row wrap" style="gap: 8px">
        <button
          v-for="opt in CUISINE_OPTIONS"
          :key="opt"
          class="chip"
          :class="{ on: state.cuisine === opt }"
          @click="pickChip('cuisine', opt)"
        >
          {{ opt }}
        </button>
      </div>
    </div>
    <div class="filter-row">
      <span class="filter-label">排序</span>
      <select v-model="state.sort" class="select" style="max-width: 210px" aria-label="排序方式" @change="onSortChange">
        <option value="recommend">推荐度</option>
        <option value="kcal">热量从低到高</option>
        <option value="protein">蛋白从高到低</option>
      </select>
    </div>
  </section>

  <section class="mt-32">
    <div class="section-title">
      <h2>筛选结果</h2>
      <span class="small muted">{{ resultMeta }}</span>
    </div>

    <div class="grid g3">
      <!-- 加载骨架 -->
      <template v-if="loading">
        <article v-for="i in PAGE_SIZE" :key="i" class="card recipe-card">
          <div class="sk" style="aspect-ratio: 4/3; border-radius: 0" />
          <div class="body">
            <div class="sk" style="height: 16px; width: 68%" />
            <div class="sk" style="height: 11px; width: 92%" />
            <div class="sk" style="height: 11px; width: 80%" />
            <div class="row" style="gap: 6px; margin-top: 4px">
              <div class="sk" style="height: 20px; width: 62px" />
              <div class="sk" style="height: 20px; width: 62px" />
              <div class="sk" style="height: 20px; width: 62px" />
            </div>
          </div>
        </article>
      </template>

      <!-- 空结果 -->
      <div v-else-if="!paged.length" style="grid-column: 1 / -1">
        <div class="empty">
          <div class="empty-ico"><SvgIcon name="search" /></div>
          <h4>没有符合条件的食谱</h4>
          <p>试试放宽餐次或菜系，或清空关键词重新检索。</p>
        </div>
        <div style="text-align: center; padding-bottom: 26px">
          <button class="btn btn-outline btn-sm" @click="clearFilters">
            <SvgIcon name="refresh" />清空筛选
          </button>
        </div>
      </div>

      <!-- 食谱卡片 -->
      <article
        v-for="(r, i) in paged"
        :key="r.id"
        class="card recipe-card reveal"
        :class="'d' + ((i % 3) + 1)"
      >
        <div class="cover">
          <RouterLink :to="'/recipes/' + r.id">
            <img :src="r.img" :alt="r.name" />
          </RouterLink>
          <span class="fit">{{ r.fit.join(' / ') }}</span>
          <button
            class="fav"
            :class="{ on: store.isRecipeCollected(r.id) }"
            :aria-label="'收藏' + r.name"
            @click="toggleCollect(r)"
          >
            <SvgIcon name="bookmark" />
          </button>
        </div>
        <div class="body">
          <h3>
            <RouterLink :to="'/recipes/' + r.id" style="text-decoration: none; color: inherit">
              {{ r.name }}
            </RouterLink>
          </h3>
          <p class="desc">{{ r.desc }}</p>
          <div class="recipe-nut">
            <span class="nut-pill">
              <SvgIcon name="flame" style="width: 11px; height: 11px" /><b>{{ r.kcal }}</b> kcal
            </span>
            <span class="nut-pill">蛋白 <b>{{ r.p }}</b>g</span>
            <span class="nut-pill">纤维 <b>{{ r.fiber }}</b>g</span>
            <span class="nut-pill">匹配 <b>{{ scoreOf(r) }}</b></span>
          </div>
          <div class="meal-meta" style="margin-top: auto; padding-top: 6px">
            <span><SvgIcon name="clock" /> {{ r.time }} 分钟</span>
            <span>{{ r.cuisine }}</span>
            <span><SvgIcon name="star" /> {{ r.rating.toFixed(1) }}</span>
          </div>
        </div>
      </article>
    </div>

    <!-- 分页 -->
    <div v-if="!loading && paged.length" class="pager">
      <button class="btn btn-outline btn-sm" :disabled="state.page <= 1" @click="goPage(-1)">
        <SvgIcon name="chevron-left" />上一页
      </button>
      <span class="small num">第 {{ state.page }} / {{ pages }} 页</span>
      <button class="btn btn-outline btn-sm" :disabled="state.page >= pages" @click="goPage(1)">
        下一页<SvgIcon name="chevron-right" />
      </button>
    </div>
  </section>
  </div><!-- /食谱库 -->

  <!-- ========== 我的食谱 ========== -->
  <div v-show="tab === 'mine'">
    <section class="mt-16">
      <div class="section-title">
        <h2>我的自定义食谱</h2>
        <span class="small muted">共 {{ customList.length }} 道 · 仅自己可见</span>
      </div>

      <div v-if="!customList.length" class="empty">
        <div class="empty-ico"><SvgIcon name="book-open" /></div>
        <h4>还没有自定义食谱</h4>
        <p>把常做的菜记录下来，营养数据自己填，之后可一键记入饮食记录。</p>
        <button class="btn btn-primary btn-sm" style="margin-top: 14px" @click="openCreate">
          <SvgIcon name="plus" />新建食谱
        </button>
      </div>

      <div v-else class="grid g3">
        <article
          v-for="(r, i) in customList"
          :key="r.id"
          class="card recipe-card reveal"
          :class="'d' + ((i % 3) + 1)"
        >
          <div class="cover">
            <RouterLink :to="'/recipes/' + r.id">
              <img :src="r.img" :alt="r.name" />
            </RouterLink>
            <span class="fit">我的</span>
          </div>
          <div class="body">
            <h3>
              <RouterLink :to="'/recipes/' + r.id" style="text-decoration: none; color: inherit">
                {{ r.name }}
              </RouterLink>
            </h3>
            <p class="desc">{{ r.desc }}</p>
            <div class="recipe-nut">
              <span class="nut-pill">
                <SvgIcon name="flame" style="width: 11px; height: 11px" /><b>{{ r.kcal }}</b> kcal
              </span>
              <span class="nut-pill">蛋白 <b>{{ r.p }}</b>g</span>
              <span class="nut-pill">纤维 <b>{{ r.fiber }}</b>g</span>
            </div>
            <div class="meal-meta" style="margin-top: auto; padding-top: 6px">
              <span><SvgIcon name="clock" /> {{ r.time }} 分钟</span>
              <span>{{ r.mealType }}</span>
            </div>
            <div class="row" style="gap: 8px; margin-top: 10px">
              <button class="btn btn-outline btn-sm grow" @click="openEdit(r)">编辑</button>
              <button class="btn btn-danger btn-sm" @click="removeCustom(r)">删除</button>
            </div>
          </div>
        </article>
      </div>
    </section>

    <section class="mt-32">
      <div class="section-title">
        <h2>已收藏食谱</h2>
        <span class="small muted">{{ collectedDisplay.length }} 道</span>
      </div>

      <div v-if="!collectedDisplay.length" class="empty">
        <div class="empty-ico"><SvgIcon name="bookmark" /></div>
        <h4>还没有收藏食谱</h4>
        <p>在食谱库点卡片右上角的书签，就能把喜欢的食谱收进来。</p>
        <button class="btn btn-outline btn-sm" style="margin-top: 14px" @click="switchTab('library')">
          <SvgIcon name="book-open" />去食谱库看看
        </button>
      </div>

      <div v-else class="grid g3">
        <article
          v-for="(r, i) in collectedDisplay"
          :key="r.id"
          class="card recipe-card reveal"
          :class="'d' + ((i % 3) + 1)"
        >
          <div class="cover">
            <RouterLink :to="'/recipes/' + r.id">
              <img :src="r.img" :alt="r.name" />
            </RouterLink>
            <span class="fit">{{ (r.fit || []).join(' / ') }}</span>
            <button class="fav on" :aria-label="'取消收藏' + r.name" @click="toggleCollect(r)">
              <SvgIcon name="bookmark" />
            </button>
          </div>
          <div class="body">
            <h3>
              <RouterLink :to="'/recipes/' + r.id" style="text-decoration: none; color: inherit">
                {{ r.name }}
              </RouterLink>
            </h3>
            <p class="desc">{{ r.desc }}</p>
            <div class="recipe-nut">
              <span class="nut-pill">
                <SvgIcon name="flame" style="width: 11px; height: 11px" /><b>{{ r.kcal }}</b> kcal
              </span>
              <span class="nut-pill">蛋白 <b>{{ r.p }}</b>g</span>
              <span class="nut-pill">纤维 <b>{{ r.fiber }}</b>g</span>
            </div>
            <div class="meal-meta" style="margin-top: auto; padding-top: 6px">
              <span><SvgIcon name="clock" /> {{ r.time }} 分钟</span>
              <span>{{ r.cuisine }}</span>
            </div>
          </div>
        </article>
      </div>
    </section>
  </div><!-- /我的食谱 -->

  <p class="small muted mt-32" style="text-align: center">
    食谱营养为整份估算值，实际会因食材品种、烹调方式与用油量浮动。健康建议不构成医疗诊断，慢病管理请遵医嘱。
  </p>

  <!-- 自定义食谱编辑弹窗 -->
  <div class="overlay" :class="{ open: modalOpen }" @click.self="modalOpen = false">
    <div class="modal" style="width: min(720px, 100%)">
      <div class="modal-hd">
        <div>
          <h3>{{ editingId ? '编辑自定义食谱' : '新建自定义食谱' }}</h3>
          <p>保存后仅自己可见，可随时编辑或删除。</p>
        </div>
        <button class="modal-close" aria-label="关闭" @click="modalOpen = false"><SvgIcon name="x" /></button>
      </div>
      <div class="modal-bd">
        <label class="field mb-16">
          <span class="field-label">食谱名称</span>
          <input v-model="form.name" class="input" placeholder="例如：番茄鸡胸意面" />
        </label>

        <div class="grid g2 mb-16" style="gap: 14px">
          <label class="field">
            <span class="field-label">餐次</span>
            <select v-model="form.mealType" class="select">
              <option>早餐</option><option>午餐</option><option>晚餐</option><option>加餐</option>
            </select>
          </label>
          <label class="field">
            <span class="field-label">菜系</span>
            <select v-model="form.cuisine" class="select">
              <option>中式</option><option>轻食</option><option>西式</option>
            </select>
          </label>
          <label class="field">
            <span class="field-label">烹饪时长（分钟）</span>
            <input v-model="form.time" class="input" type="number" min="1" />
          </label>
          <label class="field">
            <span class="field-label">难度</span>
            <select v-model="form.level" class="select">
              <option>简单</option><option>中等</option><option>进阶</option>
            </select>
          </label>
          <label class="field">
            <span class="field-label">份数</span>
            <input v-model="form.servings" class="input" type="number" min="1" />
          </label>
          <label class="field">
            <span class="field-label">封面图</span>
            <select v-model="form.img" class="select">
              <option v-for="opt in IMG_OPTIONS" :key="opt.label" :value="opt.value">{{ opt.label }}</option>
            </select>
          </label>
        </div>

        <div class="grid g3 mb-16" style="gap: 14px">
          <label class="field">
            <span class="field-label">热量（kcal）</span>
            <input v-model="form.kcal" class="input" type="number" min="1" placeholder="486" />
          </label>
          <label class="field">
            <span class="field-label">蛋白质（g）</span>
            <input v-model="form.p" class="input" type="number" min="0" step="0.1" placeholder="39" />
          </label>
          <label class="field">
            <span class="field-label">碳水（g）</span>
            <input v-model="form.c" class="input" type="number" min="0" step="0.1" placeholder="52" />
          </label>
          <label class="field">
            <span class="field-label">脂肪（g）</span>
            <input v-model="form.f" class="input" type="number" min="0" step="0.1" placeholder="11" />
          </label>
          <label class="field">
            <span class="field-label">膳食纤维（g）</span>
            <input v-model="form.fiber" class="input" type="number" min="0" step="0.1" placeholder="6.2" />
          </label>
        </div>

        <div class="field mb-16">
          <span class="field-label">适宜目标</span>
          <div class="row wrap" style="gap: 8px">
            <button
              v-for="opt in FIT_OPTIONS.slice(1)"
              :key="opt"
              type="button"
              class="chip"
              :class="{ on: form.fit.includes(opt) }"
              @click="toggleFit(opt)"
            >
              {{ opt }}
            </button>
          </div>
        </div>

        <label class="field mb-16">
          <span class="field-label">一句话简介</span>
          <textarea v-model="form.desc" class="textarea" rows="2" placeholder="自己常做的低脂高蛋白快手午餐。"></textarea>
        </label>
        <label class="field mb-16">
          <span class="field-label">食材清单（每行一项，格式：名称 用量 单位）</span>
          <textarea
            v-model="form.ingredients"
            class="textarea"
            rows="4"
            placeholder="全麦意面 70 g&#10;鸡胸肉 120 g&#10;番茄 2 个"
          ></textarea>
        </label>
        <label class="field mb-16">
          <span class="field-label">制作步骤（每行一步）</span>
          <textarea
            v-model="form.steps"
            class="textarea"
            rows="4"
            placeholder="意面下沸水煮 8 分钟，捞出备用。&#10;鸡胸切条用黑胡椒腌 5 分钟，少油煎熟。&#10;番茄炒出汁，倒入意面与鸡胸翻匀即可。"
          ></textarea>
        </label>
        <label class="field">
          <span class="field-label">小贴士（选填）</span>
          <input v-model="form.tips" class="input" placeholder="用不粘锅可把用油控制在 5g 以内。" />
        </label>
      </div>
      <div class="modal-ft">
        <button class="btn btn-outline" @click="modalOpen = false">取消</button>
        <button class="btn btn-primary" :disabled="savingCustom" @click="saveCustom">
          {{ savingCustom ? '保存中…' : '保存食谱' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.recipe-tabs {
  margin-bottom: 24px;
  width: 100%;
  max-width: 340px;
}
.recipe-tabs button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  flex: 1;
}
.recipe-tabs button :deep(.ic) {
  width: 15px;
  height: 15px;
}
.recipe-tabs .nav-badge {
  margin-left: 2px;
  height: 16px;
  min-width: 16px;
  line-height: 1;
}
.filter-bar {
  padding: 18px 22px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.filter-row {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}
.filter-label {
  font-size: 11.5px;
  letter-spacing: 0.08em;
  color: var(--text-3);
  min-width: 34px;
}
.pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  margin-top: 28px;
}
</style>
