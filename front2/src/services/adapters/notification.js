/* ============================================================
   services/adapters/notification.js · 通知字段适配层
   ------------------------------------------------------------
   后端通知类型是英文枚举（diet_reminder / goal_achievement 等），
   页面按中文标签分组和选图标，这里统一翻译；
   时间字段是 ISO 字符串，页面直接按 "YYYY-MM-DD HH:mm" 切片显示。
   ============================================================ */

const TYPE_MAP = {
  diet_reminder: '饮食提醒',
  goal_achievement: '目标达成',
  article_recommend: '文章推荐',
  warning: '警告',
  system: '系统'
}

const pad = (n) => String(n).padStart(2, '0')

function formatTime(value) {
  if (!value) return ''
  const text = String(value)
  const match = text.match(/^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/)
  if (match) {
    return `${match[1]}-${match[2]}-${match[3]} ${match[4]}:${match[5]}`
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return text
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function toLink(notification) {
  const relatedId = notification.relatedId
  if (relatedId == null) return ''
  if (notification.relatedType === 'article') return 'article-detail.html?id=' + relatedId
  if (notification.relatedType === 'recipe') return 'recipe-detail.html?id=' + relatedId
  if (notification.relatedType === 'diet_goal') return 'goal.html'
  if (notification.relatedType === 'diet_record') return 'record.html'
  return ''
}

export function toNotification(be) {
  const n = be || {}
  return {
    id: n.id,
    type: TYPE_MAP[n.type] || n.type || '系统',
    title: n.title || '系统通知',
    content: n.content || '',
    read: n.isRead === 1 || n.isRead === true,
    time: formatTime(n.createTime || n.sendTime),
    link: toLink(n),
    _raw: n
  }
}
