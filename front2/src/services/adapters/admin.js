/* ============================================================
   services/adapters/admin.js · 运营后台字段适配层
   ------------------------------------------------------------
   后台页面的数据形状是照着 mock 写的，后端总览/用户/内容接口
   用的是另一套字段，这里统一翻译一次，页面就不用改。
   ============================================================ */

import { toRecipe } from './recipe'
import { toArticle } from './article'
import { toIngredient } from './ingredient'

/** 后端时间 → YYYY-MM-DD（用户注册日期只显示到天） */
function dateOnly(value) {
  if (!value) return ''
  const text = String(value)
  if (/^\d{4}-\d{2}-\d{2}/.test(text)) return text.slice(0, 10)
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return text
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

/** 后端用户 → 后台用户表格 */
export function toAdminUser(user) {
  const u = user || {}
  return {
    id: u.userId ?? u.id,
    name: u.username || '未命名用户',
    email: u.email || '',
    goal: u.goalType || '',
    records: Number(u.recordCount) || 0,
    joined: dateOnly(u.createTime),
    status: u.status == null ? 1 : Number(u.status),
    role: u.role || '',
    _raw: u
  }
}

/** 后端总览 → 页面 overview */
export function toAdminOverview(data) {
  const d = data || {}
  const s = d.summary || {}
  const t = d.trends || {}
  const dates = Array.isArray(t.dates) ? t.dates : []

  const trend = dates.map((date, index) => ({
    date,
    users: Number((t.activeUsers || [])[index]) || 0,
    records: Number((t.dietRecords || [])[index]) || 0
  }))

  return {
    stats: {
      users: Number(s.userCount) || 0,
      dau: Number(s.todayActiveUserCount) || 0,
      records: Number(s.todayDietRecordCount) || 0,
      recipes: Number(s.recipeCount) || 0,
      articles: Number(s.articleCount) || 0,
      ingredients: Number(s.ingredientCount) || 0
    },
    trend,
    activities: buildActivities(d.recentActivities || {}),
    topRecipes: (d.topRecipes || []).map((r) => ({
      id: r.id,
      name: r.name || '未命名食谱',
      views: Number(r.viewCount ?? r.views) || 0
    })),
    topArticles: (d.topArticles || []).map((a) => ({
      id: a.id == null ? null : String(a.id),
      title: a.title || '未命名文章',
      views: Number(a.readCount ?? a.views) || 0
    }))
  }
}

function buildActivities(raw) {
  const activities = []
  const unread = Number(raw.unreadNotificationCount) || 0
  const disabled = Number(raw.disabledUserCount) || 0
  const readUsers = Number(raw.todayReadUserCount) || 0

  if (unread > 0) {
    activities.push({ type: 'amber', text: `有 ${unread} 条通知未读`, time: '实时' })
  }
  if (disabled > 0) {
    activities.push({ type: 'gray', text: `${disabled} 个账号已被禁用`, time: '实时' })
  }
  if (readUsers > 0) {
    activities.push({ type: '', text: `今日 ${readUsers} 位用户阅读了健康文章`, time: '今日' })
  }
  ;(raw.recentArticles || []).slice(0, 1).forEach((article) => {
    activities.push({
      type: '',
      text: `新文章《${article.title || '未命名'}》已发布`,
      time: dateOnly(article.createTime || article.publishDate)
    })
  })
  ;(raw.recentCustomRecipes || []).slice(0, 1).forEach((recipe) => {
    activities.push({
      type: '',
      text: `用户新增自定义食谱「${recipe.name || '未命名'}」`,
      time: dateOnly(recipe.createTime)
    })
  })

  return activities
}

/** 后台内容列表 → 页面表格行（保留 status 供上/下架用） */
export function toAdminContentRows(type, rows) {
  if (!Array.isArray(rows)) return []
  if (type === 'recipe') return rows.map((row) => toRecipe(row))
  if (type === 'article') return rows.map((row) => toArticle(row))
  return rows.map((row) => toIngredient(row))
}
