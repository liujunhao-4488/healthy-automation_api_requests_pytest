<script setup>
/* ============================================================
   ArticlePublishView.vue · 用户发帖
   ------------------------------------------------------------
   对应后端 POST /article/publish。

   后端契约（HealthArticleController.publishArticle）：
     · title   必填，@NotBlank
     · content 必填
     · category 为空时兜底「健康知识」
     · author   为空时用当前登录用户名
     · id 会被强制置 null（防覆盖已有文章）
     · status 强制 1 —— 发布即上架，无审核流程
   标签在库里是「顿号/逗号分隔的字符串」，前端用数组操作，
   提交时由 adapters/article.js 的 publishArticle 拼成字符串。

   页面能力：
     · 标题 / 摘要 / 正文 / 分类 / 标签 / 作者署名 / 适宜人群 / 目标类型
     · 正文实时字数统计与阅读时长估算
     · 标签增删（回车或逗号添加）
     · 草稿自动存 localStorage，防止误关丢失
     · 发布前校验，发布后跳转到文章详情
   ============================================================ */
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { articlesApi } from '@/services/api'
import { toast } from '@/composables/useToast'
import { confirmDialog } from '@/composables/useConfirm'
import SvgIcon from '@/components/SvgIcon.vue'

const router = useRouter()
const store = useAppStore()

/** 库里实际用到的分类，与 KnowledgeView 的 CATS 保持一致 */
const CATS = ['健康知识', '营养知识', '饮食指南', '减脂指南', '增肌指南', '饮食误区']
/** 目标类型，与后端 goal_type 字段对应 */
const GOAL_TYPES = ['', '减脂', '增肌', '控糖', '维持']

const DRAFT_KEY = 'sh_article_draft'

const form = reactive({
  title: '',
  summary: '',
  content: '',
  category: '健康知识',
  author: '',
  suitableFor: '',
  goalType: ''
})

/** 标签用数组维护，提交时由 adapter 拼成字符串 */
const tagInput = ref('')
const tags = ref([])

const saving = ref(false)
const errs = reactive({ title: false, content: false })

/* ---------------- 派生信息 ---------------- */
/** 正文去掉空白后的字符数 */
const charCount = computed(() => (form.content || '').replace(/\s/g, '').length)
/** 按中文每分钟约 350 字估算阅读时长，至少 1 分钟 */
const readMinutes = computed(() => Math.max(1, Math.round(charCount.value / 350)))
/** 摘要超长提示 */
const summaryOverflow = computed(() => (form.summary || '').length > 200)

/** 可提交性：标题与正文非空 */
const canSubmit = computed(
  () => form.title.trim().length > 0 && form.content.trim().length > 0 && !saving.value
)

/* ---------------- 标签 ---------------- */
function addTag(raw) {
  const parts = String(raw || '')
    .split(/[，,、;；\s]+/)
    .map((t) => t.trim())
    .filter(Boolean)
  let added = 0
  for (const t of parts) {
    if (tags.value.includes(t)) continue
    if (tags.value.length >= 8) {
      toast('最多添加 8 个标签', 'error')
      break
    }
    if (t.length > 12) {
      toast('单个标签不要超过 12 个字', 'error')
      continue
    }
    tags.value.push(t)
    added++
  }
  tagInput.value = ''
  return added
}

function onTagKeydown(e) {
  if (e.key === 'Enter' || e.key === ',') {
    e.preventDefault()
    addTag(tagInput.value)
  } else if (e.key === 'Backspace' && !tagInput.value && tags.value.length) {
    // 输入框为空时按退格删最后一个标签
    tags.value.pop()
  }
}

function removeTag(t) {
  tags.value = tags.value.filter((x) => x !== t)
}

/* ---------------- 草稿 ---------------- */
let draftTimer = null
function saveDraft() {
  try {
    localStorage.setItem(
      DRAFT_KEY,
      JSON.stringify({
        ...form,
        tags: tags.value,
        savedAt: Date.now()
      })
    )
  } catch (e) {
    /* 配额或隐私模式下写不进去，忽略即可 */
  }
}

/** 表单任意变化后 800ms 存一次草稿，避免频繁写盘 */
watch(
  [form, tags],
  () => {
    clearTimeout(draftTimer)
    draftTimer = setTimeout(saveDraft, 800)
  },
  { deep: true }
)

function restoreDraft() {
  try {
    const raw = localStorage.getItem(DRAFT_KEY)
    if (!raw) return false
    const d = JSON.parse(raw)
    if (!d || (!d.title && !d.content)) return false
    Object.assign(form, {
      title: d.title || '',
      summary: d.summary || '',
      content: d.content || '',
      category: CATS.includes(d.category) ? d.category : '健康知识',
      author: d.author || '',
      suitableFor: d.suitableFor || '',
      goalType: GOAL_TYPES.includes(d.goalType) ? d.goalType : ''
    })
    tags.value = Array.isArray(d.tags) ? d.tags.slice(0, 8) : []
    return true
  } catch (e) {
    return false
  }
}

function clearDraft() {
  try {
    localStorage.removeItem(DRAFT_KEY)
  } catch (e) {
    /* 忽略 */
  }
}

/* ---------------- 发布 ---------------- */
async function submit() {
  errs.title = !form.title.trim()
  errs.content = !form.content.trim()
  if (errs.title || errs.content) {
    toast(errs.title ? '请填写文章标题' : '请填写文章内容', 'error')
    return
  }
  if (form.title.trim().length > 100) {
    toast('标题不要超过 100 字', 'error')
    return
  }

  saving.value = true
  const res = await articlesApi.publish({
    title: form.title.trim(),
    summary: form.summary.trim(),
    content: form.content.trim(),
    category: form.category,
    tags: tags.value,
    author: form.author.trim(),
    suitableFor: form.suitableFor.trim(),
    goalType: form.goalType
  })
  saving.value = false

  if (res.code !== 200) {
    toast(res.message || '发布失败，请稍后重试', 'error')
    return
  }

  clearDraft()
  toast('文章已发布并上架')
  // 跳到详情页，让用户立刻看到成品；没有 id 时退回列表
  if (res.data && res.data.id) {
    router.push('/knowledge/' + res.data.id)
  } else {
    router.push('/knowledge')
  }
}

async function discard() {
  const ok = await confirmDialog('放弃这篇草稿？已填写的内容会被清空。', {
    title: '放弃草稿',
    okText: '放弃',
    danger: true
  })
  if (!ok) return
  form.title = ''
  form.summary = ''
  form.content = ''
  form.author = ''
  form.suitableFor = ''
  form.goalType = ''
  form.category = '健康知识'
  tags.value = []
  tagInput.value = ''
  clearDraft()
  toast('草稿已清空')
}

function goBack() {
  router.push('/knowledge')
}

onMounted(() => {
  // 默认署名当前登录用户名，用户可改
  form.author = store.displayName || ''
  if (restoreDraft()) {
    toast('已恢复上次未发布的草稿')
  }
})

onUnmounted(() => {
  clearTimeout(draftTimer)
})
</script>

<template>
  <header class="page-head reveal">
    <div>
      <p class="eyebrow">Publish</p>
      <h1 class="page-title">发布文章</h1>
      <p class="page-sub">分享你的饮食经验与营养知识，发布后立即在「健康知识」中上架</p>
    </div>
    <div class="page-actions">
      <button class="btn btn-outline" @click="goBack">
        <SvgIcon name="chevron-left" />返回列表
      </button>
      <button class="btn btn-outline" @click="discard">清空</button>
      <button class="btn btn-primary" :disabled="!canSubmit" @click="submit">
        <SvgIcon name="check" />{{ saving ? '发布中' : '发布' }}
      </button>
    </div>
  </header>

  <!-- 标题 + 摘要 -->
  <article class="card card-pad reveal d1">
    <div class="card-hd">
      <h3>基本信息</h3>
      <span class="small muted">标题与正文为必填</span>
    </div>
    <div class="card-bd">
      <div class="field" :class="{ 'has-error': errs.title }">
        <label>文章标题 <span class="small muted">（必填）</span></label>
        <input
          v-model="form.title"
          class="input"
          type="text"
          maxlength="100"
          placeholder="例如：减脂期怎么吃主食才不容易饿"
          @input="errs.title = false"
        />
        <span class="small muted">{{ form.title.length }} / 100</span>
      </div>

      <div class="field">
        <label>摘要 <span class="small muted">（选填，列表页展示用）</span></label>
        <textarea
          v-model="form.summary"
          class="input"
          rows="3"
          maxlength="500"
          placeholder="用一两句话概括文章要点，不填会自动截取正文开头"
        ></textarea>
        <span class="small" :class="summaryOverflow ? 'muted' : 'muted'" style="color: var(--clay-600)" v-if="summaryOverflow">
          摘要偏长，列表页可能被截断
        </span>
        <span v-else class="small muted">{{ form.summary.length }} / 500</span>
      </div>
    </div>
  </article>

  <!-- 正文 -->
  <article class="card reveal d2" style="margin-top: 18px">
    <div class="card-hd">
      <h3>正文 <span class="small muted">（必填）</span></h3>
      <span class="small muted">
        {{ charCount }} 字 · 约 {{ readMinutes }} 分钟读完
      </span>
    </div>
    <div class="card-bd">
      <div class="field" :class="{ 'has-error': errs.content }">
        <textarea
          v-model="form.content"
          class="input"
          rows="16"
          placeholder="支持换行分段。建议先用一句话说结论，再展开原因和具体做法。"
          style="line-height: 1.85; font-family: inherit"
          @input="errs.content = false"
        ></textarea>
      </div>
      <p class="small muted" style="line-height: 1.7">
        提示：内容请基于权威食养指南或自身经验，不要给出诊断、用药等医疗建议。
      </p>
    </div>
  </article>

  <!-- 分类与标签 -->
  <article class="card reveal d3" style="margin-top: 18px">
    <div class="card-hd">
      <h3>分类与标签</h3>
    </div>
    <div class="card-bd">
      <div class="field">
        <label>分类</label>
        <div class="row wrap" style="gap: 8px">
          <button
            v-for="c in CATS"
            :key="c"
            type="button"
            class="chip"
            :class="{ active: form.category === c }"
            @click="form.category = c"
          >
            {{ c }}
          </button>
        </div>
      </div>

      <div class="field">
        <label>标签 <span class="small muted">（回车或逗号添加，最多 8 个）</span></label>
        <div class="tag-editor">
          <span v-for="t in tags" :key="t" class="tag-pill">
            {{ t }}
            <button type="button" class="tag-x" aria-label="移除标签" @click="removeTag(t)">×</button>
          </span>
          <input
            v-model="tagInput"
            class="tag-input"
            type="text"
            :placeholder="tags.length ? '继续添加' : '例如：控糖、低GI'"
            @keydown="onTagKeydown"
            @blur="tagInput && addTag(tagInput)"
          />
        </div>
      </div>
    </div>
  </article>

  <!-- 推荐设置 -->
  <article class="card reveal d4" style="margin-top: 18px">
    <div class="card-hd">
      <h3>推荐设置 <span class="small muted">（选填）</span></h3>
      <span class="small muted">用于个性化推荐</span>
    </div>
    <div class="card-bd">
      <div class="grid-2" style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px">
        <div class="field">
          <label>作者署名</label>
          <input
            v-model="form.author"
            class="input"
            type="text"
            maxlength="50"
            placeholder="留空则使用当前用户名"
          />
        </div>
        <div class="field">
          <label>适宜人群</label>
          <input
            v-model="form.suitableFor"
            class="input"
            type="text"
            maxlength="100"
            placeholder="例如：减脂人群、办公室人群"
          />
        </div>
      </div>

      <div class="field">
        <label>目标类型</label>
        <div class="row wrap" style="gap: 8px">
          <button
            v-for="g in GOAL_TYPES"
            :key="g || 'none'"
            type="button"
            class="chip"
            :class="{ active: form.goalType === g }"
            @click="form.goalType = g"
          >
            {{ g || '不指定' }}
          </button>
        </div>
      </div>
    </div>
  </article>

  <!-- 底部操作 -->
  <div class="row-between reveal d4" style="margin-top: 22px; align-items: center">
    <span class="small muted">
      发布后立即上架，可在「健康知识」列表看到
    </span>
    <div class="row" style="gap: 10px">
      <button class="btn btn-outline" @click="goBack">取消</button>
      <button class="btn btn-primary" :disabled="!canSubmit" @click="submit">
        <SvgIcon name="check" />{{ saving ? '发布中' : '发布文章' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
/* 分类/目标类型 chip 的选中态；
   项目全局有 .chip 样式，这里只补 active 的视觉反馈 */
.chip.active {
  background: var(--green-800);
  color: #fff;
  border-color: var(--green-800);
}

/* 标签编辑器：把已选标签和输入框排成一行可换行的容器 */
.tag-editor {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: 1px solid var(--line, #dbe5de);
  border-radius: 10px;
  background: #fff;
  min-height: 44px;
}

.tag-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px 3px 10px;
  border-radius: 999px;
  background: var(--green-50, #e8f2ec);
  color: var(--green-800, #1f5b3e);
  font-size: 13px;
  line-height: 1.6;
}

.tag-x {
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font-size: 15px;
  line-height: 1;
  padding: 0 2px;
  opacity: 0.65;
}

.tag-x:hover {
  opacity: 1;
}

.tag-input {
  flex: 1 1 140px;
  min-width: 120px;
  border: 0;
  outline: none;
  font-size: 14px;
  background: transparent;
  padding: 4px 0;
}
</style>
