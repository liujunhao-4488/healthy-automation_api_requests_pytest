<script setup>
/* ============================================================
   IngredientsView.vue · 食材库 + 替代工具
   ------------------------------------------------------------
   对应静态版 pages/ingredients.html。两块内容：
     1) 替代工具：选原食材 + 填目标 → 生成等价替代方案
     2) 食材库：分类 / 关键词筛选 + 点卡片看营养详情
   ============================================================ */
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import DB from '@/mock/db'
import { ingredientsApi } from '@/services/api'
import { toast } from '@/composables/useToast'
import SvgIcon from '@/components/SvgIcon.vue'

/* ---------------- 食材列表 ---------------- */
const CATS = ['全部', '主食', '蔬菜', '肉类', '蛋类', '乳制品', '水果', '坚果', '豆制品']

const cat = ref('全部')
const keyword = ref('')
const keywordInput = ref('')
const list = ref([])
const total = ref(0)
const loading = ref(true)
let seq = 0

async function loadIngredients() {
  const my = ++seq
  loading.value = true
  const res = await ingredientsApi.list({ cat: cat.value, keyword: keyword.value })
  if (my !== seq) return
  loading.value = false
  if (res.code !== 200) {
    toast(res.message, 'error')
    list.value = []
    total.value = 0
    return
  }
  list.value = res.data.list
  total.value = res.data.total
}

function pickCat(c) {
  cat.value = c
  loadIngredients()
}

/* 搜索防抖 300ms */
let timer = null
function onSearchInput() {
  clearTimeout(timer)
  timer = setTimeout(() => {
    keyword.value = keywordInput.value.trim()
    loadIngredients()
  }, 300)
}

function clearFilters() {
  cat.value = '全部'
  keyword.value = ''
  keywordInput.value = ''
  loadIngredients()
}

/* ---------------- 食材详情弹窗 ---------------- */
const modalOpen = ref(false)
const currentIng = ref(null)

const detailRows = computed(() => {
  const ing = currentIng.value
  if (!ing) return []
  return [
    ['热量', ing.kcal + ' kcal'],
    ['蛋白质', ing.p + ' g'],
    ['碳水化合物', ing.c + ' g'],
    ['脂肪', ing.f + ' g'],
    ['膳食纤维', ing.fiber + ' g'],
    ['糖', ing.sugar + ' g'],
    ['钠', ing.sodium + ' mg'],
    ['升糖指数 GI', ing.gi ? String(ing.gi) : '—'],
    ['胆固醇', ing.chol ? ing.chol + ' mg' : '—']
  ]
})

function openIng(ing) {
  currentIng.value = ing
  modalOpen.value = true
}

function closeIng() {
  modalOpen.value = false
}

/* ---------------- 替代工具 ---------------- */
const BASE_OPTIONS = ['鸡胸肉', '白米饭', '牛奶']
/** 通过「作为替代方案」动态加进来的食材，追加到下拉框 */
const extraOptions = ref([])
const subOptions = computed(() => {
  const all = BASE_OPTIONS.concat(extraOptions.value)
  // 去重，保留第一次出现的顺序
  return all.filter((v, i) => all.indexOf(v) === i)
})

const subName = ref('鸡胸肉')
const subPrompt = ref('低脂、低 GI')
const subList = ref([])
const subLoading = ref(false)
const subHint = ref('正在准备替代工具…')

async function runSubstitute() {
  subLoading.value = true
  subHint.value = '正在按「' + (subPrompt.value.trim() || '营养等价') + '」检索替代方案…'
  const res = await ingredientsApi.substitute({
    name: subName.value,
    prompt: subPrompt.value.trim()
  })
  subLoading.value = false
  if (res.code !== 200) {
    subHint.value = ''
    subList.value = []
    toast(res.message, 'error')
    return
  }
  const data = res.data
  subList.value = data.list
  subHint.value =
    '已为「' + data.source + '」生成 ' + data.list.length + ' 个方案' +
    (data.prompt ? ' · 目标：' + data.prompt : '') + '。替换后请同步调整用量。'
}

/** 从详情弹窗把食材填回替代工具 */
function useAsSubstitute() {
  const ing = currentIng.value
  if (!ing) return
  if (!extraOptions.value.includes(ing.name) && !BASE_OPTIONS.includes(ing.name)) {
    extraOptions.value = extraOptions.value.concat([ing.name])
  }
  subName.value = ing.name
  modalOpen.value = false
  window.scrollTo({ top: 0, behavior: 'smooth' })
  toast('已填入替代工具：' + ing.name)
}

/** 每个替代方案对应的食材 id（有的话才能跳详情） */
function ingOf(name) {
  return DB.ingredients.find((x) => x.name === name)
}

/* 弹窗打开时锁滚动 */
watch(modalOpen, (open) => {
  document.body.style.overflow = open ? 'hidden' : ''
})
function onKeydown(e) {
  if (e.key === 'Escape' && modalOpen.value) closeIng()
}
onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})

onMounted(() => {
  loadIngredients()
  runSubstitute()
})
</script>

<template>
  <header class="page-head reveal">
    <div>
      <p class="eyebrow">Ingredient Lab</p>
      <h1 class="page-title">食材库</h1>
      <p class="page-sub">22 种常见食材，每 100g 营养口径</p>
    </div>
    <div class="page-actions">
      <div class="search-box" style="min-width: 260px">
        <SvgIcon name="search" />
        <input
          v-model="keywordInput"
          class="input"
          type="search"
          placeholder="搜索食材名称，如 鸡胸肉"
          aria-label="搜索食材"
          @input="onSearchInput"
        />
      </div>
    </div>
  </header>

  <!-- 替代工具 -->
  <article class="card card-pad sub-tool reveal d1">
    <div class="row-between" style="align-items: flex-start">
      <div>
        <p class="eyebrow" style="margin: 0">Substitution Lab</p>
        <h2 class="display" style="font-size: 21px; color: var(--green-950); margin-top: 6px">
          替代工具
        </h2>
      </div>
      <span class="badge"><SvgIcon name="refresh" />按营养等价</span>
    </div>

    <div class="grid g2 mt-16" style="gap: 14px">
      <label class="field">
        <span class="field-label">原食材</span>
        <select v-model="subName" class="select">
          <option v-for="opt in subOptions" :key="opt" :value="opt">{{ opt }}</option>
        </select>
      </label>
      <label class="field">
        <span class="field-label">目标说明</span>
        <input
          v-model="subPrompt"
          class="input"
          type="text"
          placeholder="例如：低脂、低 GI、乳糖不耐"
          @keydown.enter="runSubstitute"
        />
      </label>
    </div>

    <div class="row-between mt-16" style="flex-wrap: wrap; gap: 12px">
      <p class="small muted" style="line-height: 1.7">
        按每 100g 营养口径做等价替换，生成后请同步调整用量，保持这一餐的蛋白质总量不变。
      </p>
      <button class="btn btn-primary" :disabled="subLoading" @click="runSubstitute">
        <SvgIcon name="refresh" />{{ subLoading ? '生成中' : '生成替代方案' }}
      </button>
    </div>

    <p class="small mt-16" style="color: var(--green-800)">{{ subHint }}</p>

    <div class="grid g3 mt-12">
      <template v-if="subLoading">
        <div v-for="i in 3" :key="i" class="card card-pad-sm">
          <div class="sk" style="height: 14px; width: 50%" />
          <div class="sk mt-12" style="height: 26px; width: 40%" />
          <div class="sk mt-12" style="height: 11px" />
          <div class="sk mt-8" style="height: 11px; width: 80%" />
        </div>
      </template>

      <article v-for="s in subList" :key="s.name" class="card card-pad-sm">
        <div class="row-between">
          <strong style="font-size: 14.5px; color: var(--green-950)">{{ s.name }}</strong>
          <span class="badge">{{ s.tag }}</span>
        </div>
        <div class="row mt-8" style="align-items: baseline; gap: 6px">
          <span class="num" style="font-size: 26px; color: var(--green-900)">{{ s.kcal }}</span>
          <span class="small muted">kcal / 100g</span>
        </div>
        <div class="ing-macros">
          <span>蛋白 <b>{{ s.p }}</b>g</span><span>脂肪 <b>{{ s.f }}</b>g</span>
        </div>
        <p class="small muted mt-8" style="line-height: 1.7">{{ s.reason }}</p>
        <div class="row-between mt-12">
          <span class="small muted">等价替换</span>
          <button v-if="ingOf(s.name)" class="link-btn" @click="openIng(ingOf(s.name))">
            营养详情<SvgIcon name="chevron-right" />
          </button>
          <span v-else class="small muted">—</span>
        </div>
      </article>
    </div>
  </article>

  <!-- 食材库 -->
  <section class="mt-32 reveal d2">
    <div class="section-title">
      <h2>食材库</h2>
      <span class="small muted">{{ loading ? '正在检索…' : '共 ' + total + ' 种食材' }}</span>
    </div>
    <div class="row wrap" style="gap: 8px; margin-bottom: 18px">
      <button
        v-for="c in CATS"
        :key="c"
        class="chip"
        :class="{ on: cat === c }"
        @click="pickCat(c)"
      >
        {{ c }}
      </button>
    </div>

    <div class="grid g3">
      <template v-if="loading">
        <article v-for="i in 6" :key="i" class="card ing-card">
          <div class="row-between">
            <div class="sk" style="height: 15px; width: 45%" />
            <div class="sk" style="height: 20px; width: 42px" />
          </div>
          <div class="sk mt-12" style="height: 26px; width: 38%" />
          <div class="sk mt-12" style="height: 11px; width: 92%" />
          <div class="sk mt-12" style="height: 11px; width: 70%" />
        </article>
      </template>

      <div v-else-if="!list.length" style="grid-column: 1 / -1">
        <div class="empty">
          <div class="empty-ico"><SvgIcon name="apple" /></div>
          <h4>没有匹配的食材</h4>
          <p>换个关键词，或清空分类后再试。</p>
        </div>
        <div style="text-align: center; padding-bottom: 26px">
          <button class="btn btn-outline btn-sm" @click="clearFilters">
            <SvgIcon name="refresh" />清空筛选
          </button>
        </div>
      </div>

      <template v-else>
        <article
          v-for="(ing, i) in list"
          :key="ing.id"
          class="card ing-card reveal"
          :class="'d' + ((i % 3) + 1)"
          role="button"
          tabindex="0"
          :aria-label="'查看' + ing.name + '营养详情'"
          @click="openIng(ing)"
          @keydown.enter.prevent="openIng(ing)"
          @keydown.space.prevent="openIng(ing)"
        >
          <div class="row-between" style="align-items: flex-start">
            <h3>{{ ing.name }}</h3>
            <span class="tag">{{ ing.cat }}</span>
          </div>
          <div class="ing-kcal mt-8">{{ ing.kcal }}<small> kcal / 100g</small></div>
          <div class="ing-macros" style="flex-wrap: wrap">
            <span>蛋白 <b>{{ ing.p }}</b></span>
            <span>碳水 <b>{{ ing.c }}</b></span>
            <span>脂肪 <b>{{ ing.f }}</b></span>
            <span>纤维 <b>{{ ing.fiber }}</b></span>
          </div>
          <div class="row wrap mt-12" style="gap: 6px">
            <span v-for="t in ing.tags" :key="t" class="tag">{{ t }}</span>
          </div>
        </article>
      </template>
    </div>
  </section>

  <div class="alert-inline mt-32 reveal d3">
    <SvgIcon name="info" />
    <span>
      <b>GI 小知识</b>：GI ≤ 55 为低 GI，56–69 为中 GI，≥ 70 为高 GI。GI 只描述升糖速度，不反映实际摄入量；控糖时还要结合 GL（血糖负荷）与总碳水摄入一起看，并优先保证蛋白质与膳食纤维。
    </span>
  </div>

  <p class="small muted mt-24" style="text-align: center">
    营养数据为每 100g 可食部均值，来源为平台食材库标准口径，实际会因品种与烹调方式浮动。健康建议不构成医疗诊断，慢病管理请遵医嘱。
  </p>

  <!-- 食材详情弹窗 -->
  <div class="overlay" :class="{ open: modalOpen }" @click.self="closeIng">
    <div class="modal">
      <div class="modal-hd">
        <div>
          <h3>{{ currentIng?.name || '食材详情' }}</h3>
          <p>{{ currentIng ? currentIng.cat + ' · 每 100g 可食部' : '每 100g 营养' }}</p>
        </div>
        <button class="modal-close" aria-label="关闭" @click="closeIng">
          <SvgIcon name="x" />
        </button>
      </div>
      <div class="modal-bd">
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr><th>营养指标</th><th>每 100g</th></tr>
            </thead>
            <tbody>
              <tr v-for="row in detailRows" :key="row[0]">
                <td class="strong">{{ row[0] }}</td>
                <td class="num">{{ row[1] }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="small" style="color: var(--text-2); line-height: 1.8; margin-top: 16px">
          {{ currentIng ? currentIng.desc + '。' : '' }}
        </p>
      </div>
      <div class="modal-ft">
        <RouterLink class="btn btn-outline btn-sm" to="/recipes">
          <SvgIcon name="book-open" />用这个食材找食谱
        </RouterLink>
        <button class="btn btn-primary btn-sm" @click="useAsSubstitute">
          <SvgIcon name="refresh" />作为替代方案
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sub-tool {
  background: linear-gradient(155deg, var(--surface) 0%, var(--green-050) 100%);
}
.ing-card h3 {
  line-height: 1.35;
}
.ing-card .tag {
  white-space: nowrap;
}
</style>
