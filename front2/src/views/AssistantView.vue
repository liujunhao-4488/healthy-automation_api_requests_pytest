<script setup>
/* ============================================================
   AssistantView.vue · AI 饮食助手
   ------------------------------------------------------------
   对应静态版 pages/assistant.html。核心是流式对话：

     用户提问 → 列表先落一条 user 消息 → 气泡区插一个「正在输入」
     → chatStream 的 onChunk 逐段刷新 streamText（打字机效果）
     → onDone 把最终回答写进 store，占位气泡被真实消息替换

   每条 AI 回答都带「意图 + 来源」两个小标签，这是这个页面的产品点。
   ============================================================ */
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { assistantApi } from '@/services/api'
import { toast } from '@/composables/useToast'
import { confirmDialog } from '@/composables/useConfirm'
import SvgIcon from '@/components/SvgIcon.vue'

const store = useAppStore()
const router = useRouter()

const SUGGESTS = [
  '高血脂人群饮食要注意什么',
  '鸡胸肉可以用什么替代',
  '减脂期一周早餐怎么搭',
  '米饭多少卡'
]
const GUARD_Q = '帮我开个降脂药处方'

const INTENTS = {
  knowledge: '知识问答',
  recipe: '食谱推荐',
  advice: '饮食建议',
  chat: '闲聊',
  medical: '医疗越界',
  abuse: '不当内容',
  blocked: '护栏拦截'
}
const SOURCES = {
  authority: '权威指南',
  ingredient: '食材库',
  recipe: '食谱库',
  model: '模型生成',
  guardrail: '安全护栏',
  article: '知识库'
}

/* ---------------- 会话 ---------------- */
const currentId = ref(store.convos.length ? store.convos[0].id : null)
const search = ref('')

const currentConv = computed(() =>
  currentId.value ? store.conversation(currentId.value) : null
)

const filteredConvs = computed(() => {
  const q = search.value.trim()
  if (!q) return store.convos
  return store.convos.filter(
    (c) => (c.title || '').indexOf(q) > -1 || (c.summary || '').indexOf(q) > -1
  )
})

const convSummary = (c) =>
  c.summary ||
  (c.messages && c.messages.length
    ? String(c.messages[c.messages.length - 1].text || '').slice(0, 26)
    : '尚未开始对话')

const messages = computed(() => currentConv.value?.messages || [])

const chatTitle = computed(() => currentConv.value?.title || 'AI 饮食助手')
const rounds = computed(() => messages.value.filter((m) => m.role === 'user').length)
const chatSub = computed(() =>
  rounds.value
    ? '共 ' + rounds.value + ' 轮对话 · 回答标注来源，可追溯'
    : '尚未开始对话 · 会结合你的健康档案与目标作答'
)

function stamp() {
  return store.now().slice(5)
}
function userChar() {
  return (store.displayName || '我').charAt(0)
}
function intentLabel(m) {
  return INTENTS[m.intent] || INTENTS.chat
}
function sourceLabel(m) {
  return SOURCES[m.source] || SOURCES.model
}

function pickConv(id) {
  currentId.value = id
  nextTick(scrollBottom)
}

async function removeConv(c) {
  const ok = await confirmDialog(
    '删除「' + (c.title || '这条会话') + '」后，对话记录将从本机移除，无法恢复。',
    { title: '删除会话', okText: '删除', danger: true }
  )
  if (!ok) return
  const wasCurrent = currentId.value === c.id
  store.removeConversation(c.id)
  if (wasCurrent) {
    currentId.value = store.convos.length ? store.convos[0].id : null
  }
  toast('会话已删除')
}

function newConv() {
  const conv = {
    id: 'c-' + Date.now(),
    title: '新的对话',
    summary: '尚未开始对话',
    time: stamp(),
    messages: []
  }
  store.saveConversation(conv)
  currentId.value = conv.id
  nextTick(() => inputEl.value?.focus())
  toast('已新建对话')
}

/* ---------------- 输入框 ---------------- */
const inputText = ref('')
const inputEl = ref(null)
const chatScrollEl = ref(null)

const charCount = computed(() => inputText.value.length)

function autoGrow() {
  const el = inputEl.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(120, el.scrollHeight) + 'px'
}

function scrollBottom() {
  const el = chatScrollEl.value
  if (el) el.scrollTop = el.scrollHeight
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
    e.preventDefault()
    send()
  }
}

/* ---------------- 发送与流式 ---------------- */
const sending = ref(false)
const streaming = ref(false)
const streamText = ref('')

async function send(prompt) {
  if (sending.value) {
    toast('正在生成回答，请稍候', 'error')
    return
  }
  const text = String(prompt == null ? inputText.value : prompt).trim()
  if (!text) {
    toast('请输入问题', 'error')
    inputEl.value?.focus()
    return
  }
  if (text.length > 1000) {
    toast('问题请控制在 1000 字以内', 'error')
    return
  }

  // 没有会话就先建一个
  let conv = currentConv.value
  if (!conv) {
    conv = {
      id: 'c-' + Date.now(),
      title: '新的对话',
      summary: '尚未开始对话',
      time: stamp(),
      messages: []
    }
    store.saveConversation(conv)
    currentId.value = conv.id
  }
  const targetId = conv.id

  // 落一条用户消息（第一句顺便当标题）
  const title = !conv.title || conv.title === '新的对话' ? text.slice(0, 18) : conv.title
  store.saveConversation({
    ...conv,
    title,
    messages: conv.messages.concat([{ role: 'user', text, time: store.nowTime() }])
  })

  inputText.value = ''
  autoGrow()

  sending.value = true
  streaming.value = true
  streamText.value = ''
  await nextTick()
  scrollBottom()

  try {
    await assistantApi.chatStream(text, {
      onChunk: (shown) => {
        streamText.value = shown
        scrollBottom()
      },
      onDone: (result) => {
        const aiMsg = result.blocked
          ? {
              role: 'ai',
              blocked: true,
              intent: result.intent,
              source: 'guardrail',
              text: result.text,
              time: store.nowTime()
            }
          : {
              role: 'ai',
              intent: result.intent,
              source: result.source,
              text: result.text,
              list: result.list,
              cards: result.cards,
              note: result.note,
              time: store.nowTime()
            }

        const fresh = store.conversation(targetId)
        if (fresh) {
          const plain = String(result.text || '')
          store.saveConversation({
            ...fresh,
            messages: fresh.messages.concat([aiMsg]),
            time: stamp(),
            title: fresh.title || text.slice(0, 18),
            summary: plain.slice(0, 26) + (plain.length > 26 ? '…' : '')
          })
        }
        streaming.value = false
        streamText.value = ''
      }
    })
  } catch (err) {
    toast('回答生成失败，请稍后重试', 'error')
    streaming.value = false
    streamText.value = ''
  } finally {
    sending.value = false
    await nextTick()
    scrollBottom()
    inputEl.value?.focus()
  }
}

/* 消息变化或流式刷新时自动滚到底 */
watch([() => messages.value.length, streamText], () => {
  nextTick(scrollBottom)
})

/* ---------------- 引导页的档案摘要 ---------------- */
const guideText = computed(() => {
  const h = store.healthInfo
  const chronic = h.chronic && h.chronic.length ? h.chronic.join('、') : '无慢病记录'
  return (
    '我会结合你的档案（' + chronic + ' · ' + store.goalInfo.goalType +
    '目标）与权威食养指南作答，并标注每段回答的意图与来源。'
  )
})
</script>

<template>
  <header class="page-head reveal">
    <div>
      <p class="eyebrow">AI Assistant</p>
      <h1 class="page-title">AI 饮食助手</h1>
      <p class="page-sub">结合你的档案与权威食养指南，回答带意图与来源标注</p>
    </div>
    <div class="page-actions">
      <button class="btn btn-primary" type="button" @click="newConv">
        <SvgIcon name="plus" />新对话
      </button>
    </div>
  </header>

  <section class="chat-layout asst-layout reveal d1">
    <!-- 会话列表 -->
    <aside class="card conv-panel">
      <div class="conv-head">
        <div class="row-between">
          <strong style="font-size: 13.5px">最近会话</strong>
          <span class="small muted num">{{ store.convos.length }}</span>
        </div>
      </div>
      <div class="conv-search">
        <div class="search-box">
          <SvgIcon name="search" />
          <input v-model="search" class="input" type="search" placeholder="搜索会话" aria-label="搜索会话" />
        </div>
      </div>
      <div class="conv-list">
        <div v-if="!filteredConvs.length" class="conv-empty">
          {{
            store.convos.length
              ? '没有匹配的会话，换个关键词试试。'
              : '还没有会话记录，点击右上角「新对话」开始提问。'
          }}
        </div>
        <div v-for="c in filteredConvs" :key="c.id" class="conv-row">
          <button
            class="conv-item"
            :class="{ on: c.id === currentId }"
            type="button"
            @click="pickConv(c.id)"
          >
            <strong>{{ c.title || '新的对话' }}</strong>
            <span>{{ c.time || '' }} · {{ convSummary(c) }}</span>
          </button>
          <button class="conv-del" type="button" title="删除会话" aria-label="删除会话" @click="removeConv(c)">
            <SvgIcon name="trash" />
          </button>
        </div>
      </div>
    </aside>

    <!-- 对话区 -->
    <section class="card chat-panel">
      <header class="chat-head">
        <div class="grow">
          <div class="row" style="gap: 9px">
            <span class="chat-title">{{ chatTitle }}</span>
            <span class="badge"><SvgIcon name="shield" />RAG · 权威源</span>
          </div>
          <p class="small muted" style="margin-top: 2px">{{ chatSub }}</p>
        </div>
      </header>

      <div ref="chatScrollEl" class="chat-scroll">
        <!-- 引导页：还没有任何消息 -->
        <div v-if="!messages.length && !streaming" class="chat-empty">
          <div class="guide-ico"><SvgIcon name="sparkles" /></div>
          <h3>你好，我是膳衡 AI 饮食助手</h3>
          <p class="small muted" style="line-height: 1.8">{{ guideText }}</p>
          <div class="guide-list">
            <button v-for="q in SUGGESTS" :key="q" class="suggest" type="button" @click="send(q)">
              {{ q }}
            </button>
          </div>
          <div class="alert-inline" style="text-align: left">
            <SvgIcon name="shield" />
            <span>涉及诊断、用药与处方的问题会被安全护栏拦截，请咨询医生或临床营养师。</span>
          </div>
        </div>

        <!-- 消息列表 -->
        <template v-else>
          <div
            v-for="(m, i) in messages"
            :key="i"
            class="msg"
            :class="{ user: m.role === 'user' }"
          >
            <div class="msg-avatar">{{ m.role === 'user' ? userChar() : '衡' }}</div>
            <div class="msg-body">
              <!-- 用户气泡 -->
              <template v-if="m.role === 'user'">
                <div class="msg-bubble"><p>{{ m.text }}</p></div>
                <div class="msg-meta">
                  <span style="margin-left: auto">{{ m.time }}</span>
                </div>
              </template>

              <!-- 被护栏拦截 -->
              <template v-else-if="m.blocked">
                <div class="blocked-note">
                  <SvgIcon name="alert" />
                  <div>
                    <strong class="blocked-title">安全护栏已拦截</strong>{{ m.text }}
                  </div>
                </div>
                <div class="msg-meta">
                  <span class="intent-chip">
                    <span class="dot gray" />意图：{{ intentLabel(m) }}
                  </span>
                  <span class="intent-chip">来源：{{ sourceLabel(m) }}</span>
                  <span style="margin-left: auto">{{ m.time }}</span>
                </div>
              </template>

              <!-- 正常回答 -->
              <template v-else>
                <div class="msg-bubble">
                  <p>{{ m.text }}</p>
                  <ul v-if="m.list && m.list.length">
                    <li v-for="(x, j) in m.list" :key="j">{{ x }}</li>
                  </ul>
                  <div v-if="m.cards && m.cards.length" class="msg-cards">
                    <a
                      v-for="(c, j) in m.cards"
                      :key="j"
                      class="msg-card"
                      :href="c.to || c.href"
                      @click.prevent="router.push(c.to || '/recipes/1')"
                    >
                      <img v-if="c.img" :src="c.img" :alt="c.title" />
                      <div>
                        <strong>{{ c.title }}</strong><span>{{ c.sub || '' }}</span>
                      </div>
                    </a>
                  </div>
                  <p v-if="m.note" class="small muted" style="margin-top: 8px">{{ m.note }}</p>
                </div>
                <div class="msg-meta">
                  <span class="intent-chip">
                    <span class="dot" :class="m.intent === 'recipe' ? ' amber' : ' gray'" />
                    意图：{{ intentLabel(m) }}
                  </span>
                  <span class="intent-chip">来源：{{ sourceLabel(m) }}</span>
                  <span style="margin-left: auto">{{ m.time }}</span>
                </div>
              </template>
            </div>
          </div>

          <!-- 流式占位气泡 -->
          <div v-if="streaming" class="msg">
            <div class="msg-avatar">衡</div>
            <div class="msg-body">
              <div class="msg-bubble">
                <span v-if="!streamText" class="typing"><i /><i /><i /></span>
                <p class="stream-text">{{ streamText }}</p>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- 有对话时才显示快捷提问条 -->
      <div v-if="messages.length || streaming" class="chat-suggests">
        <button v-for="q in SUGGESTS" :key="q" class="suggest" type="button" @click="send(q)">
          {{ q }}
        </button>
      </div>

      <div class="chat-input">
        <div class="chat-input-row">
          <textarea
            ref="inputEl"
            v-model="inputText"
            rows="1"
            placeholder="问点具体的，比如「晚饭吃什么」"
            aria-label="输入问题"
            :disabled="sending"
            @input="autoGrow"
            @keydown="onKeydown"
          />
          <button class="btn btn-primary btn-sm" type="button" :disabled="sending" @click="send()">
            <SvgIcon name="send" />发送
          </button>
        </div>
        <div class="chat-hint">
          <span class="row wrap" style="gap: 12px">
            <button class="link-btn" type="button" @click="send(GUARD_Q)">
              <SvgIcon name="alert" />试试医疗越界问题
            </button>
            <span>Enter 发送 · Shift + Enter 换行</span>
          </span>
          <span class="num" :style="charCount > 1000 ? 'color: var(--danger)' : ''">
            {{ charCount }} / 1000
          </span>
        </div>
      </div>
    </section>
  </section>

  <p class="small muted mt-24" style="text-align: center">
    AI 回答由本地规则桩生成并标注来源，仅作饮食参考，不构成医疗诊断或处方。
  </p>
</template>

<style scoped>
.conv-head {
  padding: 14px 16px 10px;
  flex: none;
}
.conv-search {
  padding: 0 12px 12px;
  border-bottom: 1px solid var(--border);
  flex: none;
}
.conv-search .input {
  height: 38px;
  font-size: 12.5px;
}
.conv-row {
  position: relative;
  display: flex;
  align-items: stretch;
}
.conv-row :deep(.conv-item) {
  padding-right: 40px;
}
.conv-del {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: 0;
  background: transparent;
  color: var(--text-3);
  display: grid;
  place-items: center;
  cursor: pointer;
  opacity: 0;
  pointer-events: none;
  transition: 0.15s;
}
.conv-row:hover .conv-del,
.conv-del:focus-visible {
  opacity: 1;
  pointer-events: auto;
  background: var(--surface);
  color: var(--danger);
}
.conv-del:hover {
  background: var(--danger-bg);
}
.conv-del .ic {
  width: 14px;
  height: 14px;
}
.conv-empty {
  padding: 30px 16px;
  text-align: center;
  font-size: 12px;
  color: var(--text-3);
  line-height: 1.8;
}
.chat-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--green-950);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.msg-body {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.stream-text {
  white-space: pre-wrap;
  margin: 0;
}
.chat-empty {
  margin: auto;
  max-width: 520px;
  width: 100%;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px;
}
.guide-ico {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  margin: 0 auto;
  display: grid;
  place-items: center;
  background: var(--green-050);
  border: 1px solid var(--green-100);
  color: var(--green-700);
}
.guide-ico .ic {
  width: 24px;
  height: 24px;
}
.chat-empty h3 {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 600;
  color: var(--green-950);
}
.guide-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  text-align: left;
}
.guide-list .suggest {
  border-radius: 10px;
  padding: 10px 12px;
  line-height: 1.5;
  font-size: 11.5px;
}
.blocked-title {
  display: block;
  font-weight: 600;
  margin-bottom: 2px;
}
.chat-hint .link-btn {
  color: var(--clay-600);
}
@media (max-width: 960px) {
  .asst-layout {
    grid-template-columns: minmax(0, 1fr);
    height: auto;
  }
  .asst-layout .conv-panel {
    max-height: 230px;
  }
  .asst-layout .chat-panel {
    height: min(72vh, 640px);
  }
}
</style>
