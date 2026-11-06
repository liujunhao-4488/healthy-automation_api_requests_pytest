<script setup>
/* ============================================================
   KnowledgeView.vue · 健康知识
   ------------------------------------------------------------
   对应静态版 pages/knowledge.html。三块：
     · 精选文章（后端 /article/recommend 的首条，可用 ?excludeId 排除）
     · 文章列表：分类 chip / 搜索 / 标签云，带分页
     · 右侧：热门榜 + 标签云 + 免责声明

   【2026-11-04 修复】
   精选 / 热门榜 / 标签云 三块原先直接读本地 mock 库 DB.articles，
   而下方列表走的是真接口。结果是页面上「精选文章」「热门榜」
   显示的是 8 篇假文章，点进列表却是 133 篇真文章，数据完全对不上。
   现在三块都改用后端接口：
     · 精选      GET /article/recommend?pageSize=1
     · 热门榜    GET /article/list?sort=hot&pageSize=5（按阅读量）
     · 标签云    GET /article/tags
   ============================================================ */
import { ref, reactive, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { articlesApi } from '@/services/api'
import { toast } from '@/composables/useToast'
import SvgIcon from '@/components/SvgIcon.vue'

const store = useAppStore()

const CATS = ['全部', '饮食指南', '营养知识', '减肥指南', '增肌指南', '饮食误区']

const state = reactive({ cat: '全部', keyword: '', tag: '', page: 1 })

/* ---------------- 精选文章 ---------------- */
/** 后端 /article/recommend 的第一条；取不到时退回列表首条 */
const feature = ref(null)

/* ---------------- 热门榜 ---------------- */
/** 按阅读量排序的前 5 篇，来自 GET /article/list?sort=hot */
const hot = ref([])

/* ---------------- 标签云 ---------------- */
/**
 * 标签来自 GET /article/tags（实测返回 54 个纯字符串）。
 * 后端不给每个标签的出现次数，所以「count」这里只用于排序占位——
 * 原有模板里展示的是标签名，数量不影响视觉，但从大到小排序更自然，
 * 因此保留 count 字段并统一置 0，模板无需改动。
 */
const tagCloud = ref([])

/** 加载右侧三块（精选 / 热门榜 / 标签云） */
async function loadSidebar() {
  // 三块互不依赖，并行请求
  const [recRes, hotRes, tagRes] = await Promise.all([
    articlesApi.recommend({ pageSize: 1 }),
    articlesApi.list({ page: 1, pageSize: 5, sort: 'hot' }),
    articlesApi.tags()
  ])

  if (recRes.code === 200 && recRes.data && recRes.data.list && recRes.data.list.length) {
    feature.value = recRes.data.list[0]
  }

  if (hotRes.code === 200 && hotRes.data && Array.isArray(hotRes.data.list)) {
    hot.value = hotRes.data.list.slice(0, 5)
  }

  if (tagRes.code === 200 && Array.isArray(tagRes.data)) {
    tagCloud.value = tagRes.data.slice(0, 12).map((t) => ({ tag: t, count: 0 }))
  }
}

/* ---------------- 列表 ---------------- */
const list = ref([])
const total = ref(0)
const loading = ref(true)
const keywordInput = ref('')
let seq = 0
let timer = null

const pages = computed(() => Math.max(1, Math.ceil(total.value / 5)))

async function load() {
  const mine = ++seq
  loading.value = true
  const res = await articlesApi.list({
    cat: state.cat,
    keyword: state.keyword,
    tag: state.tag,
    page: state.page,
    pageSize: 5
  })
  if (mine !== seq) return
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
  state.cat = c
  state.page = 1
  load()
}

function pickTag(t) {
  state.tag = t
  state.keyword = ''
  state.cat = '全部'
  state.page = 1
  keywordInput.value = t
  load()
}

function onSearchInput() {
  clearTimeout(timer)
  timer = setTimeout(() => {
    state.keyword = keywordInput.value.trim()
    state.tag = ''
    state.page = 1
    load()
  }, 300)
}

function goPage(delta) {
  const next = state.page + delta
  if (next < 1 || next > pages.value) return
  state.page = next
  load()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(() => {
  load()
  loadSidebar()
})
</script>

<template>
  <header class="page-head reveal">
    <div>
      <p class="eyebrow">Knowledge Base</p>
      <h1 class="page-title">健康知识</h1>
      <p class="page-sub">基于权威食养指南与平台营养师内容</p>
    </div>
    <div class="page-actions">
      <div class="search-box" style="width: 280px">
        <SvgIcon name="search" />
        <input
          v-model="keywordInput"
          class="input"
          type="search"
          placeholder="搜索标题或摘要"
          aria-label="搜索文章"
          @input="onSearchInput"
        />
      </div>
      <!-- 用户发帖入口：后端 /article/publish 仅需登录，发布即上架 -->
      <RouterLink class="btn btn-primary" to="/knowledge/new">
        <SvgIcon name="plus" />发布文章
      </RouterLink>
    </div>
  </header>

  <!-- 精选 -->
  <section class="reveal d1">
    <div class="section-title">
      <h2>精选文章</h2>
      <span class="small muted">编辑推荐 · 每周更新</span>
    </div>
    <!-- feature 来自异步接口，未返回前为 null，用 v-if 包住避免访问空对象 -->
    <div v-if="feature" class="feature-article">
      <img :src="feature.cover" :alt="feature.title" />
      <div class="inner">
        <span class="badge">{{ feature.cat }}</span>
        <h2 class="mt-12">
          <RouterLink :to="'/knowledge/' + feature.id" style="color: inherit; text-decoration: none">
            {{ feature.title }}
          </RouterLink>
        </h2>
        <p class="small" style="color: var(--green-100); margin-top: 10px; max-width: 560px; line-height: 1.8">
          {{ feature.summary }}
        </p>
        <div class="k-feature-meta">
          <span><SvgIcon name="user" />{{ feature.author }}</span>
          <span><SvgIcon name="calendar" />{{ store.dateLabel(feature.date) }}</span>
          <span><SvgIcon name="eye" />{{ feature.views.toLocaleString('zh-CN') }} 阅读</span>
        </div>
        <RouterLink class="btn btn-outline btn-sm mt-16" :to="'/knowledge/' + feature.id">
          阅读全文 <SvgIcon name="arrow-right" />
        </RouterLink>
      </div>
    </div>
  </section>

  <!-- 分类 -->
  <section class="reveal d2">
    <div class="k-filters">
      <button
        v-for="c in CATS"
        :key="c"
        class="chip"
        type="button"
        :class="{ on: state.cat === c }"
        @click="pickCat(c)"
      >
        {{ c }}
      </button>
    </div>
  </section>

  <section class="grid split reveal d3">
    <div>
      <div class="k-list">
        <!-- 骨架 -->
        <template v-if="loading">
          <div v-for="i in 3" :key="i" class="card k-skeleton">
            <div class="sk sk-thumb" />
            <div class="sk-body">
              <div class="sk" style="height: 18px; width: 62%" />
              <div class="sk" style="height: 12px; width: 96%" />
              <div class="sk" style="height: 12px; width: 86%" />
              <div class="sk" style="height: 12px; width: 44%; margin-top: 6px" />
            </div>
          </div>
        </template>

        <!-- 空 -->
        <div v-else-if="!list.length" class="card">
          <div class="empty">
            <div class="empty-ico"><SvgIcon name="news" /></div>
            <h4>没有找到相关文章</h4>
            <p>试试更换分类、清空搜索词，或点击标签云里的其他标签。</p>
          </div>
        </div>

        <!-- 列表 -->
        <template v-else>
          <article
            v-for="a in list"
            :key="a.id"
            class="card article-card"
            style="cursor: pointer"
            @click="$router.push('/knowledge/' + a.id)"
          >
            <RouterLink class="thumb" :to="'/knowledge/' + a.id" style="display: block">
              <img :src="a.cover" :alt="a.title" />
            </RouterLink>
            <div class="body">
              <div class="row wrap" style="gap: 8px">
                <span class="badge gray">{{ a.cat }}</span>
                <span v-for="t in a.tags.slice(0, 2)" :key="t" class="tag">{{ t }}</span>
              </div>
              <h3>
                <RouterLink :to="'/knowledge/' + a.id" style="text-decoration: none; color: inherit">
                  {{ a.title }}
                </RouterLink>
              </h3>
              <p class="excerpt">{{ a.summary }}</p>
              <div class="article-meta">
                <span class="a-meta-item"><SvgIcon name="user" />{{ a.author }}</span>
                <span class="a-meta-item"><SvgIcon name="calendar" />{{ store.dateLabel(a.date) }}</span>
                <span class="a-meta-item"><SvgIcon name="eye" />{{ a.views.toLocaleString('zh-CN') }}</span>
                <span class="a-meta-item"><SvgIcon name="thumbs-up" />{{ a.likes.toLocaleString('zh-CN') }}</span>
              </div>
            </div>
          </article>
        </template>
      </div>

      <!-- 分页 -->
      <div v-if="!loading && list.length" class="k-pager">
        <button class="btn btn-outline btn-sm" :disabled="state.page <= 1" @click="goPage(-1)">
          上一页
        </button>
        <span class="small muted">第 {{ state.page }} / {{ pages }} 页 · 共 {{ total }} 篇</span>
        <button class="btn btn-outline btn-sm" :disabled="state.page >= pages" @click="goPage(1)">
          下一页
        </button>
      </div>
    </div>

    <aside class="col" style="gap: 20px">
      <article class="card card-pad">
        <div class="row-between">
          <p class="eyebrow" style="margin: 0">Trending · 热门</p>
          <span class="small muted">按阅读量</span>
        </div>
        <div class="mt-12">
          <RouterLink
            v-for="(a, i) in hot"
            :key="a.id"
            class="rank-row"
            :to="'/knowledge/' + a.id"
            style="text-decoration: none"
          >
            <span class="rank">{{ i + 1 }}</span>
            <span class="rank-name">{{ a.title }}</span>
            <span class="rank-val">{{ a.views.toLocaleString('zh-CN') }}</span>
          </RouterLink>
        </div>
      </article>

      <article class="card card-pad">
        <p class="eyebrow" style="margin: 0">Tags · 标签云</p>
        <div class="k-tagcloud">
          <button
            v-for="t in tagCloud"
            :key="t.tag"
            class="chip"
            type="button"
            style="height: 28px; padding: 0 11px; font-size: 11.5px"
            @click="pickTag(t.tag)"
          >
            {{ t.tag }}
            <span class="num" style="color: var(--text-3); font-size: 10px">{{ t.count }}</span>
          </button>
        </div>
        <p class="k-note">点击标签会填入搜索框并筛选相关文章。</p>
      </article>

      <article class="card card-pad">
        <div class="alert-inline">
          <SvgIcon name="info" />
          <div>
            <strong style="display: block; margin-bottom: 3px">内容不替代医疗诊断</strong>
            文章为通用营养科普，慢病管理与用药请遵医嘱，必要时咨询临床营养师。
          </div>
        </div>
      </article>
    </aside>
  </section>
</template>

<style scoped>
.k-feature-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  margin-top: 14px;
  font-size: 12px;
  color: var(--green-100);
}
.k-feature-meta span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.k-feature-meta .ic {
  width: 13px;
  height: 13px;
}
.k-filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin: 22px 0 20px;
}
.k-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.a-meta-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.k-pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  margin-top: 20px;
}
.k-tagcloud {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-top: 14px;
}
.k-note {
  font-size: 11.5px;
  line-height: 1.75;
  color: var(--text-3);
  margin-top: 10px;
}
.k-skeleton {
  display: flex;
  gap: 20px;
  padding: 16px;
}
.k-skeleton .sk-thumb {
  width: 190px;
  flex: none;
  aspect-ratio: 4 / 3;
  border-radius: 12px;
}
.k-skeleton .sk-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 9px;
  padding-top: 4px;
}
@media (max-width: 720px) {
  .k-skeleton .sk-thumb {
    width: 96px;
  }
}
</style>
