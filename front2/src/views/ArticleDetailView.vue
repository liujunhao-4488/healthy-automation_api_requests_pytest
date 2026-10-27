<script setup>
/* ============================================================
   ArticleDetailView.vue · 文章详情
   ------------------------------------------------------------
   对应静态版 pages/article-detail.html?id=x，现在地址是 /knowledge/:id。

   要点：
   · 正文是结构化节点数组（h2/h3/ul/quote/p），用 v-for 渲染，
     顺便给每个 h2 生成锚点 id，右侧目录就能点、能跟着滚动高亮
   · 收藏 / 点赞 / 评论都走本地状态，刷新后仍在（store 持久化）
   ============================================================ */
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useAppStore } from '@/stores/app'
import DB from '@/mock/db'
import { articlesApi } from '@/services/api'
import { toast } from '@/composables/useToast'
import SvgIcon from '@/components/SvgIcon.vue'

const route = useRoute()
const store = useAppStore()

const article = ref(null)
const loading = ref(true)
const errorMsg = ref('')

/* ---------------- 加载 ---------------- */
async function load(id) {
  loading.value = true
  errorMsg.value = ''
  const res = await articlesApi.get(id)
  loading.value = false
  if (res.code !== 200) {
    errorMsg.value = res.message
    article.value = null
    return
  }
  article.value = res.data
  document.title = res.data.title + ' · 膳衡'
  store.markArticleRead(res.data.id)
  comments.value = SEEDS.map((c) => ({ ...c, liked: false }))
  await nextTick()
  spyToc()
}

onMounted(() => load(route.params.id))
watch(
  () => route.params.id,
  (id) => {
    if (id) load(id)
  }
)

/* ---------------- 正文与目录 ---------------- */
const bodyNodes = computed(() => {
  let n = 0
  return (article.value?.body || []).map((node) => {
    if (node.t === 'h2') {
      n++
      return { ...node, id: 'sec-' + n }
    }
    return node
  })
})

const toc = computed(() =>
  bodyNodes.value.filter((n) => n.t === 'h2').map((n) => ({ id: n.id, text: n.text }))
)

/** 正文字数（去掉空白后的字符数） */
const wordCount = computed(() => {
  let n = 0
  ;(article.value?.body || []).forEach((node) => {
    if (node.text) n += node.text.replace(/\s/g, '').length
    if (node.items) node.items.forEach((x) => (n += x.replace(/\s/g, '').length))
  })
  return n
})

/* ---------------- 作者信息 ---------------- */
const author = computed(() => {
  const full = String(article.value?.author || '')
  const name = full.split('·').pop().trim()
  if (full.indexOf('周昀') > -1) {
    return {
      name,
      avatar: '周',
      role: '注册营养师 · 慢病营养',
      bio: '专注血脂管理与体重管理 8 年，负责平台食养指南的通俗化解读与内容审校。'
    }
  }
  if (full.indexOf('陈牧') > -1) {
    return {
      name,
      avatar: '陈',
      role: '体能教练 · 增肌方向',
      bio: 'NSCA-CPT，负责训练日营养与增肌期膳食方案，长期跟踪力量训练人群的饮食执行。'
    }
  }
  return {
    name,
    avatar: '编',
    role: '平台内容编辑部',
    bio: '由平台营养师团队审校，内容参考《中国居民膳食指南》与成人慢病食养指南。'
  }
})

/* ---------------- 相关阅读 ---------------- */
const related = computed(() => {
  const a = article.value
  if (!a) return []
  return DB.articles
    .filter((x) => x.id !== a.id)
    .map((x) => ({
      x,
      score: (x.cat === a.cat ? 2 : 0) + x.tags.filter((t) => a.tags.indexOf(t) > -1).length
    }))
    .sort((p, q) => q.score - p.score || q.x.views - p.x.views)
    .slice(0, 3)
    .map((p) => p.x)
})

/* ---------------- 收藏 / 点赞 ---------------- */
const collected = computed(() => store.isArticleCollected(article.value?.id))
const liked = computed(() => store.isArticleLiked(article.value?.id))
const likeCount = computed(() => (article.value?.likes || 0) + (liked.value ? 1 : 0))

function toggleCollect() {
  const on = store.toggleArticleCollect(article.value.id)
  toast(on ? '已收藏这篇文章' : '已取消收藏')
}
function toggleLike() {
  const on = store.toggleArticleLike(article.value.id)
  toast(on ? '感谢点赞' : '已取消点赞')
}

/* ---------------- 目录滚动高亮 ---------------- */
const activeToc = ref('')
let ticking = false

function spyToc() {
  const heads = Array.from(document.querySelectorAll('.article-body h2[id]'))
  if (!heads.length) return
  let cur = heads[0]
  heads.forEach((h) => {
    if (h.getBoundingClientRect().top <= 130) cur = h
  })
  activeToc.value = cur ? cur.id : ''
}

function onScroll() {
  if (ticking) return
  ticking = true
  requestAnimationFrame(() => {
    spyToc()
    ticking = false
  })
}

function scrollToSection(id) {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

/* ---------------- 评论 ---------------- */
const SEEDS = [
  {
    name: '陈嘉宁',
    avatar: '陈',
    time: '2 小时前',
    likes: 24,
    text: '把晚餐的一半白米换成杂粮饭，坚持三周后餐后犯困明显少了。文里「份量比种类更关键」这句很受用，容易执行。'
  },
  {
    name: '许知遥',
    avatar: '许',
    time: '昨天',
    likes: 11,
    text: '想问下燕麦奶能不能替代牛奶？乳糖不耐，但不太喜欢豆奶的味道。',
    reply: {
      name: '周昀',
      text: '可以，但要留意燕麦奶的碳水与添加糖，选择配料表干净的无糖款，并相应计入全天主食量。'
    }
  },
  {
    name: '赵思齐',
    avatar: '赵',
    time: '2 天前',
    likes: 8,
    text: '希望后续能出一篇外食场景的实操，尤其是火锅和烧烤怎么点，光看原则还是不太会落地。'
  }
]

const comments = ref([])
const commentInput = ref('')
const posting = ref(false)

function toggleCommentLike(c) {
  c.liked = !c.liked
  c.likes = c.likes + (c.liked ? 1 : -1)
}

function replyTo(c) {
  commentInput.value = '@' + c.name + ' '
}

async function postComment() {
  const content = commentInput.value.trim()
  if (content.length < 2) {
    toast('评论内容至少 2 个字', 'error')
    return
  }
  posting.value = true
  const r = await articlesApi.comment({ articleId: article.value.id, content })
  posting.value = false
  if (r.code !== 200) {
    toast(r.message, 'error')
    return
  }
  comments.value = [
    {
      name: store.displayName,
      avatar: (store.displayName || '用').charAt(0),
      text: content,
      time: '刚刚',
      likes: 0,
      liked: false,
      self: true
    }
  ].concat(comments.value)
  commentInput.value = ''
  toast('评论已发布')
}

/* 滚动监听 */
onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
onUnmounted(() => window.removeEventListener('scroll', onScroll))
</script>

<template>
  <!-- 骨架 -->
  <div v-if="loading">
    <div class="sk" style="height: 22px; width: 140px" />
    <div class="sk" style="height: 38px; width: 72%; margin-top: 18px" />
    <div class="sk" style="height: 14px; width: 56%; margin-top: 14px" />
    <div class="sk" style="height: 14px; width: 300px; margin-top: 14px" />
    <div class="grid split mt-24">
      <div class="sk" style="height: 520px; border-radius: 18px" />
      <div class="sk" style="height: 300px; border-radius: 18px" />
    </div>
  </div>

  <!-- 加载失败 -->
  <div v-else-if="errorMsg">
    <div class="card">
      <div class="empty">
        <div class="empty-ico"><SvgIcon name="file-text" /></div>
        <h4>文章不存在或已下线</h4>
        <p>{{ errorMsg || '换一篇继续浏览吧。' }}</p>
      </div>
    </div>
    <div class="row mt-16" style="justify-content: center">
      <RouterLink class="btn btn-primary" to="/knowledge">
        <SvgIcon name="chevron-left" />返回知识库
      </RouterLink>
    </div>
  </div>

  <!-- 正文 -->
  <template v-else-if="article">
    <header class="page-head reveal" style="align-items: flex-start">
      <div class="ad-head">
        <p class="eyebrow">Knowledge · Article</p>
        <div class="row wrap" style="gap: 10px; margin-bottom: 10px">
          <span class="badge gray">{{ article.cat }}</span>
          <RouterLink
            class="small"
            to="/knowledge"
            style="color: var(--green-700); text-decoration: none; display: inline-flex; align-items: center; gap: 4px"
          >
            <SvgIcon name="chevron-left" />返回知识库
          </RouterLink>
        </div>
        <h1 class="page-title" style="font-size: 32px; line-height: 1.3">{{ article.title }}</h1>
        <p class="page-sub" style="max-width: 700px; line-height: 1.8">{{ article.summary }}</p>
        <div class="ad-meta">
          <span><SvgIcon name="user" />{{ article.author }}</span>
          <span><SvgIcon name="calendar" />{{ store.dateLabel(article.date) }}</span>
          <span><SvgIcon name="eye" />{{ article.views.toLocaleString('zh-CN') }} 阅读</span>
          <span><SvgIcon name="file-text" />约 {{ wordCount.toLocaleString('zh-CN') }} 字</span>
        </div>
      </div>
      <div class="page-actions">
        <button class="btn" :class="collected ? 'btn-soft' : 'btn-outline'" @click="toggleCollect">
          <SvgIcon name="bookmark" />{{ collected ? '已收藏' : '收藏' }}
        </button>
        <button class="btn" :class="liked ? 'btn-soft' : 'btn-outline'" @click="toggleLike">
          <SvgIcon name="thumbs-up" />{{ liked ? '已点赞 ' : '点赞 ' }}{{ likeCount.toLocaleString('zh-CN') }}
        </button>
      </div>
    </header>

    <section class="grid split mt-24 reveal d1">
      <div class="col" style="gap: 20px">
        <!-- 正文 -->
        <article class="card">
          <div class="card-bd">
            <div class="article-body">
              <template v-for="(node, i) in bodyNodes" :key="i">
                <h2 v-if="node.t === 'h2'" :id="node.id">{{ node.text }}</h2>
                <h3 v-else-if="node.t === 'h3'">{{ node.text }}</h3>
                <ul v-else-if="node.t === 'ul'">
                  <li v-for="(x, j) in node.items" :key="j">{{ x }}</li>
                </ul>
                <blockquote v-else-if="node.t === 'quote'">{{ node.text }}</blockquote>
                <p v-else>{{ node.text }}</p>
              </template>
            </div>
            <div class="ad-tags">
              <span v-for="t in article.tags" :key="t" class="tag">{{ t }}</span>
            </div>
            <div class="alert-inline mt-24">
              <SvgIcon name="alert" />
              <span>本文为通用营养科普，不构成医疗诊断。若正在用药或患有慢性疾病，请先咨询医生或临床营养师。</span>
            </div>
          </div>
        </article>

        <!-- 评论 -->
        <article class="card">
          <div class="card-hd">
            <h3>评论 <span class="small muted num">{{ comments.length }}</span></h3>
            <span class="small muted">友善交流，不构成医疗建议</span>
          </div>
          <div class="card-bd">
            <div class="ad-comment-form">
              <textarea v-model="commentInput" class="textarea" placeholder="说说你的看法或想了解的问题…" />
              <div class="row-between">
                <span class="small muted">以「{{ store.displayName }}」的身份发布</span>
                <button class="btn btn-primary btn-sm" :disabled="posting" @click="postComment">
                  <SvgIcon name="send" />{{ posting ? '发布中' : '发布评论' }}
                </button>
              </div>
            </div>

            <div class="mt-24">
              <div v-for="(c, i) in comments" :key="i" class="comment">
                <span class="avatar sm">{{ c.avatar }}</span>
                <div class="comment-bd">
                  <div class="who">
                    <strong>{{ c.name }}</strong>
                    <span v-if="c.self" class="badge gray">我</span>
                    <time>{{ c.time }}</time>
                  </div>
                  <p>{{ c.text }}</p>
                  <div class="actions">
                    <button class="link-btn" type="button" @click="toggleCommentLike(c)">
                      <SvgIcon name="thumbs-up" />{{ c.liked ? '已赞 ' : '点赞 ' }}
                      <span class="num">{{ c.likes }}</span>
                    </button>
                    <button class="link-btn" type="button" @click="replyTo(c)">
                      <SvgIcon name="reply" />回复
                    </button>
                  </div>
                  <div v-if="c.reply" class="reply">
                    <strong>{{ c.reply.name }} 回复：</strong>{{ c.reply.text }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </article>
      </div>

      <aside class="col" style="gap: 20px">
        <!-- 作者 -->
        <article class="card card-pad">
          <p class="eyebrow" style="margin: 0">Author · 作者</p>
          <div class="row mt-12" style="gap: 12px">
            <span class="avatar lg">{{ author.avatar }}</span>
            <div class="grow">
              <strong style="font-size: 14px">{{ author.name }}</strong>
              <div class="small muted">{{ author.role }}</div>
            </div>
          </div>
          <p class="small muted mt-12" style="line-height: 1.8">{{ author.bio }}</p>
          <RouterLink class="btn btn-outline btn-sm btn-block mt-16" to="/knowledge">
            <SvgIcon name="news" />浏览全部文章
          </RouterLink>
        </article>

        <!-- 相关阅读 -->
        <article class="card card-pad">
          <p class="eyebrow" style="margin: 0">Related · 相关阅读</p>
          <div class="mt-8">
            <RouterLink
              v-for="x in related"
              :key="x.id"
              class="ad-rel"
              :to="'/knowledge/' + x.id"
            >
              <img :src="x.cover" :alt="x.title" />
              <div class="grow">
                <strong>{{ x.title }}</strong>
                <span>{{ x.cat }} · {{ x.views.toLocaleString('zh-CN') }} 阅读</span>
              </div>
            </RouterLink>
          </div>
        </article>

        <!-- 目录 -->
        <article v-if="toc.length" class="card card-pad">
          <p class="eyebrow" style="margin: 0">Contents · 目录</p>
          <div class="ad-toc">
            <a
              v-for="(t, i) in toc"
              :key="t.id"
              href="javascript:void(0)"
              :class="{ on: activeToc === t.id }"
              @click="scrollToSection(t.id)"
            >
              {{ i + 1 }}. {{ t.text }}
            </a>
          </div>
        </article>
      </aside>
    </section>
  </template>
</template>

<style scoped>
.ad-head {
  max-width: 780px;
}
.ad-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  font-size: 12px;
  color: var(--text-3);
  margin-top: 16px;
}
.ad-meta span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.ad-meta .ic {
  width: 14px;
  height: 14px;
}
.ad-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 20px;
}
.ad-comment-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.ad-toc {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: 12px;
}
.ad-toc a {
  display: block;
  padding: 7px 10px;
  border-left: 2px solid var(--border);
  font-size: 12px;
  color: var(--text-2);
  text-decoration: none;
  line-height: 1.55;
  transition: 0.15s;
}
.ad-toc a:hover {
  color: var(--green-800);
  background: var(--green-050);
}
.ad-toc a.on {
  border-left-color: var(--green-700);
  color: var(--green-800);
  background: var(--green-050);
  font-weight: 600;
}
.ad-rel {
  display: flex;
  gap: 10px;
  align-items: center;
  text-decoration: none;
  padding: 10px 0;
  border-bottom: 1px dashed var(--border);
}
.ad-rel:last-child {
  border-bottom: 0;
}
.ad-rel img {
  width: 56px;
  height: 56px;
  border-radius: 9px;
  object-fit: cover;
  flex: none;
}
.ad-rel strong {
  display: block;
  font-size: 12.5px;
  line-height: 1.5;
  color: var(--text);
}
.ad-rel span {
  font-size: 10.5px;
  color: var(--text-3);
}
.ad-rel:hover strong {
  color: var(--green-800);
}
.article-body :deep([id]) {
  scroll-margin-top: 24px;
}
@media (max-width: 720px) {
  .ad-meta {
    gap: 10px;
  }
}
</style>
