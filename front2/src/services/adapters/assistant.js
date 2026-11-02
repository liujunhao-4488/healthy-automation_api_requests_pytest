/* ============================================================
   services/adapters/assistant.js · AI 助手字段适配层
   ------------------------------------------------------------
   后端 /assistant/* 的契约：
     · 会话  { id, title, summary, messageCount, lastMessageAt, createTime, updateTime }
     · 消息  { id, role, text, messageType, cards, createTime, intent?, source?, blocked? }
     · 流式  event: start / delta / done / error

   和前端的差异：
     1. role 是 user / assistant / context，前端只认 user / ai；
        其中 context 是「拼了档案上下文的完整提示词」，属于内部记录，不展示。
     2. 会话 id 是 Long，统一转字符串，避免和本地 'c-' 会话混用后类型不一致。
     3. 历史消息接口不返回 intent / source / blocked（后端已知缺口），
        这两个标签会退回「闲聊 / 模型生成」，不影响阅读。
     4. cards 后端是按 JSON 存的，字段不完全固定，这里做一层兼容：
        title / name、sub / desc、img / cover、to / href。
   ============================================================ */

import { http } from '@/services/http'

/* ---------------- 时间 ---------------- */

/** 'YYYY-MM-DD HH:mm:ss' → 'MM-DD HH:mm'，会话列表用 */
function convTime(value) {
  const s = String(value || '')
  const m = s.match(/^\d{4}-(\d{2}-\d{2})[ T](\d{2}:\d{2})/)
  return m ? m[1] + ' ' + m[2] : ''
}

/** 'YYYY-MM-DD HH:mm:ss' → 'HH:mm'，消息气泡用；没有时间就返回空串 */
function clockTime(value) {
  const s = String(value || '')
  const m = s.match(/[ T](\d{2}:\d{2})/)
  return m ? m[1] : ''
}

/* ---------------- 卡片 ---------------- */

function toCard(raw) {
  const c = raw || {}
  const title = c.title || c.name || ''
  const sub = c.sub || c.desc || c.nutrition || c.summary || ''
  const img = c.img || c.cover || c.image || ''
  let to = c.to || c.href || ''
  if (!to && c.type === 'recipe' && c.id) to = '/recipes/' + c.id
  if (!to) to = '/ingredients'
  return { title, sub, img, to, href: to }
}

function toCards(list) {
  return Array.isArray(list) ? list.map(toCard).filter((c) => c.title) : []
}

/* ---------------- 会话 ---------------- */

export function toConversation(be) {
  const c = be || {}
  return {
    id: c.id == null ? null : String(c.id),
    title: c.title || '新的对话',
    summary: c.summary || '',
    messageCount: Number(c.messageCount) || 0,
    time: convTime(c.lastMessageAt || c.updateTime || c.createTime),
    messages: []
  }
}

/** 会话详情（含消息）由页面自己拼；这里只取列表需要的字段 */
export async function fetchConversations() {
  const res = await http.get('/assistant/conversations')
  if (res.code !== 200) return res
  const list = Array.isArray(res.data) ? res.data : []
  return { code: 200, message: res.message, data: list.map(toConversation) }
}

/* ---------------- 消息 ---------------- */

export function toMessage(be) {
  const m = be || {}
  const role = m.role === 'user' ? 'user' : 'ai'
  const msg = {
    id: m.id == null ? null : String(m.id),
    role,
    text: m.text || '',
    cards: toCards(m.cards),
    time: clockTime(m.createTime),
    intent: m.intent || '',
    source: m.source || ''
  }
  if (m.blocked) {
    msg.blocked = true
    msg.blockReason = m.blocked
  }
  return msg
}

export async function fetchConversationMessages(conversationId) {
  const res = await http.get('/assistant/conversations/' + conversationId + '/messages')
  if (res.code !== 200) return res
  const list = Array.isArray(res.data) ? res.data : []
  // context 是内部提示词记录，不展示
  const messages = list.filter((x) => x && x.role !== 'context').map(toMessage)
  return { code: 200, message: res.message, data: messages }
}

export function deleteConversation(conversationId) {
  return http.del('/assistant/conversations/' + conversationId)
}

/* ---------------- 流式聊天 ---------------- */

/**
 * POST /assistant/chat/stream
 *
 * onStart 在收到 start 事件时回调，只带会话信息（新建会话时页面要靠它拿到 id）；
 * onChunk 每次收到增量文本时回调，参数是「已拼接好的完整文本」，方便直接绑到气泡；
 * 返回统一信封，data 是与一次性聊天同构的结果：
 *   { text, intent, source, blocked, cards, message, conversationId, conversation }
 */
export async function chatStream(prompt, { conversationId, onStart, onChunk } = {}) {
  const result = {
    text: '',
    intent: '',
    source: '',
    blocked: false,
    cards: [],
    message: null,
    conversationId: conversationId == null ? null : String(conversationId),
    conversation: null
  }
  let full = ''
  let errorMessage = ''

  const body = { prompt, rawPrompt: prompt }
  if (conversationId) body.conversationId = conversationId

  const res = await http.stream('/assistant/chat/stream', body, (name, data) => {
    const d = data || {}
    if (name === 'start') {
      if (d.conversationId != null) result.conversationId = String(d.conversationId)
      if (d.conversation) result.conversation = toConversation(d.conversation)
      if (onStart) onStart(result)
    } else if (name === 'delta') {
      full += String(d.text || '')
      if (onChunk) onChunk(full, result)
    } else if (name === 'done') {
      if (d.conversationId != null) result.conversationId = String(d.conversationId)
      if (d.conversation) result.conversation = toConversation(d.conversation)
      if (d.assistantMessage) {
        const msg = toMessage(d.assistantMessage)
        result.message = msg
        result.text = msg.text
        result.intent = msg.intent
        result.source = msg.source
        result.blocked = !!msg.blocked
        result.cards = msg.cards
      }
    } else if (name === 'error') {
      errorMessage = d.message || '回答生成失败'
    }
  })

  if (res.code !== 200) return res
  if (errorMessage) return { code: 400, message: errorMessage, data: result }
  return { code: 200, message: 'ok', data: result }
}
