/* ============================================================
   services/adapters/article.js · 文章字段适配层
   ------------------------------------------------------------
   后端 /article/* 的契约和前端页面差得比食谱还多：

     1. 字段名不同
        readCount → views、likeCount → likes、collectCount → collects、
        publishDate → date、category → cat、tags 是「顿号/逗号分隔的字符串」

     2. content 是**纯文本**，不是结构化节点
        真实数据是「段落之间空一行」的字符串，还有「一、二、」小标题和
        「1. 2.」列表项、制表符表格。前端正文按 {t:'h2'|'h3'|'p'|'ul'|'quote'}
        渲染，所以这里要切段并识别标题/列表，否则整篇会挤成一大块。

     3. 后端 health_article 表**没有封面字段**
        前端卡片和精选区都要图，统一用按分类生成的渐变 SVG 封面，
        不新增图片文件、不会 404。

     4. 评论是树形（replies 数组），前端模板只支持一层 reply
        取第一条回复挂到 reply 上，其余忽略。
   ============================================================ */

import { http } from '@/services/http'

/* ---------------- 标签 ---------------- */

function parseTags(source) {
  if (!source) return []
  const normalized = String(source).replace(/[\[\]"']/g, '')
  return normalized
    .split(/[,，、;；/|\s]+/)
    .map((s) => s.trim())
    .filter(Boolean)
}

/* ---------------- 日期 ---------------- */

/** 'YYYY-MM-DD HH:mm:ss' → 'YYYY-MM-DD'；解析失败返回原值 */
function dateOnly(value) {
  if (!value) return ''
  const s = String(value)
  const m = s.match(/^(\d{4}-\d{2}-\d{2})/)
  return m ? m[1] : s.slice(0, 10)
}

/** 'YYYY-MM-DD HH:mm:ss' → '刚刚 / N 分钟前 / N 小时前 / 昨天 / N 天前 / 日期' */
function relativeTime(value) {
  if (!value) return ''
  const t = new Date(String(value).replace(' ', 'T')).getTime()
  if (Number.isNaN(t)) return dateOnly(value)
  const diff = Date.now() - t
  if (diff < 60 * 1000) return '刚刚'
  if (diff < 60 * 60 * 1000) return Math.floor(diff / 60000) + ' 分钟前'
  if (diff < 24 * 60 * 60 * 1000) return Math.floor(diff / 3600000) + ' 小时前'
  if (diff < 48 * 60 * 60 * 1000) return '昨天'
  if (diff < 30 * 24 * 60 * 60 * 1000) return Math.floor(diff / 86400000) + ' 天前'
  return dateOnly(value)
}

/* ---------------- 正文解析 ---------------- */

const HEADING = /^[一二三四五六七八九十百]+[、.]\s*/
const MD_HEADING = /^#{1,6}\s+/
const LIST_ITEM = /^(?:\d+[.、)]|[-*•·]|✅|❌|✔|✘)\s*/

/**
 * 纯文本 → 结构化节点数组
 * · 「一、xxx」「## xxx」  → h2
 * · 「1. xxx」「- xxx」「❌ xxx」 → ul 列表项（连续行合并成一个 ul）
 * · 其余非空行 → p
 */
export function parseContent(content) {
  const raw = String(content || '').replace(/\r\n?/g, '\n')
  if (!raw.trim()) return []

  const nodes = []
  let listBuffer = null

  const flushList = () => {
    if (listBuffer && listBuffer.length) nodes.push({ t: 'ul', items: listBuffer })
    listBuffer = null
  }

  raw.split('\n').forEach((line) => {
    const text = line.replace(/\t+/g, ' · ').trim()
    if (!text) {
      flushList()
      return
    }

    if (MD_HEADING.test(text)) {
      flushList()
      nodes.push({ t: 'h2', text: text.replace(MD_HEADING, '').trim() })
      return
    }
    if (HEADING.test(text)) {
      flushList()
      nodes.push({ t: 'h2', text: text.replace(HEADING, '').trim() })
      return
    }
    if (LIST_ITEM.test(text)) {
      if (!listBuffer) listBuffer = []
      listBuffer.push(text.replace(LIST_ITEM, '').trim())
      return
    }

    flushList()
    nodes.push({ t: 'p', text })
  })

  flushList()
  return nodes
}

/* ---------------- 封面 ---------------- */

const COVER_COLORS = {
  饮食指南: ['#2f6b4f', '#6fa287'],
  营养知识: ['#376f8f', '#7aa9bd'],
  减肥指南: ['#8a6a3f', '#bfa37a'],
  减脂指南: ['#6b7a3f', '#a7b578'],
  增肌指南: ['#5b4f8a', '#9a8fbd'],
  饮食误区: ['#8a4f4f', '#bd8b8b'],
  健康知识: ['#4f7a6b', '#8fb3a4']
}
const coverCache = {}

/** 按分类生成渐变 SVG 封面（data URI），同一分类只生成一次 */
function coverFor(category) {
  const cat = COVER_COLORS[category] ? category : '健康知识'
  if (coverCache[cat]) return coverCache[cat]
  const [from, to] = COVER_COLORS[cat]
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="400" height="300">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${from}"/><stop offset="1" stop-color="${to}"/></linearGradient></defs>
<rect width="400" height="300" fill="url(#g)"/>
<circle cx="330" cy="70" r="90" fill="#ffffff" opacity="0.07"/>
<circle cx="60" cy="250" r="70" fill="#ffffff" opacity="0.05"/>
<text x="200" y="146" text-anchor="middle" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="26" font-weight="600" fill="#ffffff">${cat}</text>
<text x="200" y="178" text-anchor="middle" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="12" letter-spacing="3" fill="#ffffff" opacity="0.72">SHANHENG · 健康知识</text>
</svg>`
  coverCache[cat] = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg)
  return coverCache[cat]
}

/* ---------------- 主映射 ---------------- */

/** 后端文章 → 前端文章对象 */
export function toArticle(be) {
  const a = be || {}
  const cat = a.category || '健康知识'
  return {
    // 文章 id 是雪花号（如 2038627116093902855），超过 Number.MAX_SAFE_INTEGER，
    // 转 Number 会丢精度导致详情页 404，所以原样保留字符串
    id: a.id == null ? null : String(a.id),
    title: a.title || '未命名文章',
    summary: a.summary || '',
    cat,
    tags: parseTags(a.tags),
    author: a.author || '平台编辑部',
    date: dateOnly(a.publishDate),
    views: Number(a.readCount) || 0,
    likes: Number(a.likeCount) || 0,
    collects: Number(a.collectCount) || 0,
    comments: Number(a.commentCount) || 0,
    cover: coverFor(cat),
    body: parseContent(a.content),
    liked: !!a.liked,
    collected: !!a.collected,
    status: a.status,
    content: a.content || '',
    publishDate: a.publishDate,
    readTime: a.readTime || null,
    readDuration: Number(a.readDuration) || 0,
    _raw: a
  }
}

/** 后端评论 → 前端评论对象（树形只取第一层回复） */
export function toComment(be, currentUserId) {
  const c = be || {}
  const name = c.username || '匿名用户'
  const firstReply = Array.isArray(c.replies) && c.replies.length ? c.replies[0] : null
  return {
    id: c.id == null ? null : String(c.id),
    userId: String(c.userId || ''),
    name,
    avatar: name.charAt(0),
    time: relativeTime(c.createTime),
    text: c.content || '',
    likes: 0,
    liked: false,
    self: currentUserId != null && String(currentUserId) === String(c.userId),
    reply: firstReply
      ? { name: firstReply.username || '匿名用户', text: firstReply.content || '' }
      : null
  }
}

/* ---------------- 取数 ---------------- */

/** GET /article/list */
export async function fetchArticleList({ category, tag, keyword, page = 1, pageSize = 10, sort = 'recommend' } = {}) {
  const res = await http.get('/article/list', { category, tag, keyword, page, pageSize, sort })
  if (res.code !== 200) return res
  const d = res.data || {}
  const raw = Array.isArray(d.list) ? d.list : []
  return {
    code: 200,
    message: res.message,
    data: {
      list: raw.map(toArticle),
      total: Number(d.total) || 0,
      page: Number(d.page) || page,
      pageSize: Number(d.pageSize) || pageSize,
      tags: Array.isArray(d.tags) ? d.tags : []
    }
  }
}

/**
 * POST /article/publish  用户发帖
 *
 * 后端接收 HealthArticle 实体，关键约束（看 HealthArticleController.publishArticle）：
 *   · title   @NotBlank，不能为空
 *   · content 不能为空
 *   · category 为空时后端兜底成「健康知识」
 *   · author 为空时后端用当前登录用户的 username
 *   · 前端传的 id 会被后端强制置 null（防止覆盖已有文章）
 *   · status 强制为 1（直接上架），前端传什么都不作数
 *
 * 标签在库里是「顿号或逗号分隔的字符串」，不是数组：
 *   "控糖，糖尿病，健康"
 * 前端表单用数组更好操作（增删标签），提交前在这里 join 成字符串。
 */
export async function publishArticle(payload) {
  const p = payload || {}

  const title = String(p.title || '').trim()
  const content = String(p.content || '').trim()
  if (!title) return { code: 400, message: '请填写文章标题', data: null }
  if (!content) return { code: 400, message: '请填写文章内容', data: null }

  // tags 支持数组或字符串两种输入
  const tags = Array.isArray(p.tags)
    ? p.tags.map((t) => String(t).trim()).filter(Boolean)
    : String(p.tags || '')
        .split(/[，,、;；\s]+/)
        .map((t) => t.trim())
        .filter(Boolean)

  const body = {
    title,
    summary: String(p.summary || '').trim(),
    content,
    category: String(p.category || '').trim() || '健康知识',
    tags: tags.join('，'),
    // author 留空则由后端填当前用户名；这里显式传便于用户自定义署名
    author: String(p.author || '').trim(),
    suitableFor: String(p.suitableFor || '').trim(),
    goalType: String(p.goalType || '').trim()
  }

  const res = await http.post('/article/publish', body)
  if (res.code !== 200) return res
  return {
    code: 200,
    message: res.message || '发布成功',
    data: res.data ? toArticle(res.data) : null
  }
}

/** GET /article/detail/{id} */
export async function fetchArticleDetail(id) {
  const res = await http.get('/article/detail/' + id)
  if (res.code !== 200) return res
  if (!res.data || res.data.id === undefined) {
    return { code: 404, message: '文章不存在或已下架', data: null }
  }
  return { code: 200, message: res.message, data: toArticle(res.data) }
}

/** GET /article/recommend（用于精选、相关阅读） */
export async function fetchArticleRecommend({ excludeId, page = 1, pageSize = 3 } = {}) {
  const res = await http.get('/article/recommend', { excludeId, page, pageSize })
  if (res.code !== 200) return res
  const d = res.data || {}
  return {
    code: 200,
    message: res.message,
    data: {
      list: (Array.isArray(d.list) ? d.list : []).map(toArticle),
      total: Number(d.total) || 0
    }
  }
}

/**
 * GET /article/tags
 * 返回全部标签。实测 data 是纯字符串数组（54 个），例如
 *   ["蛋白质","恢复","饮食管理","碳水","误区", ...]
 * 这里统一转成去重、去空的字符串数组，页面直接渲染。
 */
export async function fetchArticleTags() {
  const res = await http.get('/article/tags')
  if (res.code !== 200) return res
  const arr = Array.isArray(res.data) ? res.data : []
  const tags = arr
    .map((t) => (t == null ? '' : String(t).trim()))
    .filter(Boolean)
  return { code: 200, message: res.message, data: Array.from(new Set(tags)) }
}

/** GET /article/collect/list */
export async function fetchCollectedArticles() {
  const res = await http.get('/article/collect/list')
  if (res.code !== 200) return res
  return {
    code: 200,
    message: res.message,
    data: (Array.isArray(res.data) ? res.data : []).map(toArticle)
  }
}

/** GET /article/read/history */
export async function fetchArticleReadHistory(limit = 20) {
  const res = await http.get('/article/read/history', { limit })
  if (res.code !== 200) return res
  return {
    code: 200,
    message: res.message,
    data: (Array.isArray(res.data) ? res.data : []).map((be) => {
      const article = toArticle(be)
      return {
        id: article.id,
        date: dateOnly(be.readTime),
        duration: Number(be.readDuration) || 0,
        article
      }
    })
  }
}

/** POST /article/read/{id} */
export async function recordArticleRead(articleId, { readDuration, scrollPercent } = {}) {
  return http.post('/article/read/' + articleId, { readDuration, scrollPercent })
}

/** GET /article/comment/list/{id} */
export async function fetchArticleComments(articleId, currentUserId) {
  const res = await http.get('/article/comment/list/' + articleId)
  if (res.code !== 200) return res
  return {
    code: 200,
    message: res.message,
    data: (Array.isArray(res.data) ? res.data : []).map((c) => toComment(c, currentUserId))
  }
}

/** POST /article/comment/{id} */
export async function postArticleComment(articleId, content, parentId) {
  const res = await http.post('/article/comment/' + articleId, { content, parentId })
  if (res.code !== 200) return res
  return { code: 200, message: res.message, data: toComment(res.data) }
}

/** POST / DELETE /article/like/{id}；next 是切换后的目标状态 */
export function setArticleLike(articleId, next) {
  const path = '/article/like/' + articleId
  return next ? http.post(path) : http.del(path)
}

/** POST / DELETE /article/collect/{id}；next 是切换后的目标状态 */
export function setArticleCollect(articleId, next) {
  const path = '/article/collect/' + articleId
  return next ? http.post(path) : http.del(path)
}
