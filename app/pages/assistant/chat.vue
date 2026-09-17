<template>
  <view class="assistant-shell safe-bottom">
    <view class="chat-topbar">
      <view class="top-icon" @click="goBack">‹</view>
      <view class="top-title-wrap">
        <text class="top-title">饮食小助手</text>
        <text class="top-subtitle">{{ sending ? '正在思考...' : currentTitle }}</text>
      </view>
      <view class="top-actions">
        <view class="ghost-action" @click="openHistory">历史</view>
        <view class="new-chat" @click="startNewConversation">新对话</view>
      </view>
    </view>

    <scroll-view class="chat-scroll" scroll-y :scroll-top="scrollTop">
      <view v-if="!messages.length" class="welcome-panel">
        <view class="bot-orb">
          <text>AI</text>
        </view>
        <text class="welcome-title">今天想改善哪一餐？</text>
        <text class="welcome-desc">我可以帮你分析食谱、替换食材、解释控糖低钠建议，也能根据饮食记录给出调整方向。</text>

        <view class="prompt-grid">
          <view v-for="item in quickPrompts" :key="item.title" class="prompt-card" @click="useQuickPrompt(item.text)">
            <text class="prompt-title">{{ item.title }}</text>
            <text class="prompt-desc">{{ item.text }}</text>
          </view>
        </view>
      </view>

      <view v-else class="message-list">
        <view
          v-for="message in messages"
          :key="message.localId || message.id"
          class="message-row"
          :class="message.role === 'user' ? 'message-row-user' : 'message-row-assistant'"
        >
          <view v-if="message.role !== 'user'" class="assistant-avatar">AI</view>
          <view class="message-content">
            <view class="message-bubble">
              <text class="message-text">{{ message.text }}</text>
            </view>

            <view v-if="message.cards && message.cards.length" class="result-cards">
              <view v-for="(card, index) in message.cards" :key="index" class="result-card">
                <view class="result-head">
                  <text class="result-title">{{ card.name || card.title || card.ingredientName || '推荐内容' }}</text>
                  <text v-if="card.tag || card.category" class="result-tag">{{ card.tag || card.category }}</text>
                </view>
                <text v-if="card.reason || card.description" class="result-desc">
                  {{ card.reason || card.description }}
                </text>
                <view class="metric-pills">
                  <text v-if="card.calories">热量 {{ card.calories }} kcal</text>
                  <text v-if="card.protein">蛋白质 {{ card.protein }} g</text>
                  <text v-if="card.sodium">钠 {{ card.sodium }} mg</text>
                  <text v-if="card.gi">GI {{ card.gi }}</text>
                </view>
              </view>
            </view>
          </view>
        </view>

        <view v-if="sending" class="message-row message-row-assistant">
          <view class="assistant-avatar">AI</view>
          <view class="typing-bubble">
            <view class="typing-dot"></view>
            <view class="typing-dot"></view>
            <view class="typing-dot"></view>
          </view>
        </view>
      </view>
    </scroll-view>

    <view class="composer-wrap">
      <view class="composer">
        <textarea
          v-model="inputText"
          class="composer-input"
          auto-height
          maxlength="500"
          placeholder="问问饮食、食材、控糖或食谱搭配..."
          :disabled="sending"
          confirm-type="send"
        />
        <button class="send-button" :class="{ active: inputText.trim() }" :disabled="sending || !inputText.trim()" @click="sendMessage">
          ↑
        </button>
      </view>
      <text class="composer-tip">AI 建议不能替代医生诊断，慢病饮食请结合医嘱。</text>
    </view>

    <view v-if="showHistory" class="history-mask" @click="closeHistory">
      <view class="history-sheet" @click.stop>
        <view class="sheet-handle"></view>
        <view class="history-head">
          <view>
            <text class="history-title">历史对话</text>
            <text class="history-subtitle">{{ historyLoading ? '正在加载...' : `${conversations.length} 个会话` }}</text>
          </view>
          <text class="history-close" @click="closeHistory">关闭</text>
        </view>

        <view v-if="historyLoading" class="history-empty">
          <text>正在加载历史会话...</text>
        </view>

        <scroll-view v-else-if="conversations.length" class="history-list" scroll-y>
          <view
            v-for="item in conversations"
            :key="item.id"
            class="history-item"
            :class="{ active: Number(item.id) === Number(conversationId) }"
            @click="openConversation(item)"
          >
            <view class="history-item-main">
              <text class="history-item-title">{{ item.title || '未命名会话' }}</text>
              <text class="history-item-summary">{{ item.summary || '暂无摘要' }}</text>
              <view class="history-item-meta">
                <text>{{ item.messageCount || 0 }} 条消息</text>
                <text>{{ formatTime(item.lastMessageAt || item.updateTime || item.createTime) }}</text>
              </view>
            </view>
            <text class="history-delete" @click.stop="deleteConversation(item)">删除</text>
          </view>
        </scroll-view>

        <view v-else class="history-empty">
          <text>暂无历史对话</text>
          <button class="history-new-button" @click="startFromHistory">开始新对话</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import assistantApi from '@/api/assistant'
import { nextTick, ref } from 'vue'

const conversationId = ref(null)
const currentTitle = ref('在线 · 营养建议仅供参考')
const messages = ref([])
const inputText = ref('')
const sending = ref(false)
const scrollTop = ref(0)
const showHistory = ref(false)
const historyLoading = ref(false)
const conversations = ref([])

const quickPrompts = [
  { title: '控糖搭配', text: '控糖早餐怎么搭配更稳？' },
  { title: '低钠晚餐', text: '低钠晚餐推荐吃什么？' },
  { title: '食材替换', text: '鸡胸肉可以替换成什么？' },
  { title: '记录分析', text: '今天蛋白质不够怎么办？' }
]

const scrollToBottom = () => {
  nextTick(() => {
    scrollTop.value += 9999
  })
}

const normalizeMessage = (message, fallbackRole) => ({
  id: message?.id,
  localId: message?.localId || `${fallbackRole}-${Date.now()}-${Math.random()}`,
  role: message?.role || fallbackRole,
  text: message?.text || message?.content || '',
  cards: Array.isArray(message?.cards) ? message.cards : []
})

const appendMessage = (message, fallbackRole) => {
  messages.value.push(normalizeMessage(message, fallbackRole))
  scrollToBottom()
}

const goBack = () => {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/tabbar/mine' })
    }
  })
}

const resetConversationState = () => {
  conversationId.value = null
  currentTitle.value = '在线 · 营养建议仅供参考'
  messages.value = []
  inputText.value = ''
}

const startNewConversation = () => {
  resetConversationState()
}

const startFromHistory = () => {
  resetConversationState()
  closeHistory()
}

const useQuickPrompt = (text) => {
  inputText.value = text
}

const extractList = (response) => {
  const data = response?.data
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.list)) return data.list
  if (Array.isArray(data?.records)) return data.records
  return []
}

const loadConversations = async () => {
  historyLoading.value = true
  try {
    const response = await assistantApi.getConversations()
    conversations.value = response.code === 200 ? extractList(response) : []
  } catch (error) {
    conversations.value = []
    uni.showToast({ title: error?.message || '历史会话加载失败', icon: 'none' })
  } finally {
    historyLoading.value = false
  }
}

const openHistory = async () => {
  showHistory.value = true
  await loadConversations()
}

const closeHistory = () => {
  showHistory.value = false
}

const openConversation = async (conversation) => {
  if (!conversation?.id) return
  historyLoading.value = true
  try {
    const response = await assistantApi.getMessages(conversation.id)
    if (response.code !== 200) {
      throw new Error(response.message || '会话消息加载失败')
    }
    conversationId.value = conversation.id
    currentTitle.value = conversation.title || '历史对话'
    messages.value = extractList(response).map((item) => normalizeMessage(item, item.role || 'assistant'))
    closeHistory()
    scrollToBottom()
  } catch (error) {
    uni.showToast({ title: error?.message || '会话消息加载失败', icon: 'none' })
  } finally {
    historyLoading.value = false
  }
}

const deleteConversation = async (conversation) => {
  if (!conversation?.id) return
  try {
    const response = await assistantApi.deleteConversation(conversation.id)
    if (response.code !== 200) {
      throw new Error(response.message || '删除失败')
    }
    conversations.value = conversations.value.filter((item) => Number(item.id) !== Number(conversation.id))
    if (Number(conversationId.value) === Number(conversation.id)) {
      resetConversationState()
    }
    uni.showToast({ title: '已删除', icon: 'none' })
  } catch (error) {
    uni.showToast({ title: error?.message || '删除失败', icon: 'none' })
  }
}

const formatTime = (value) => {
  if (!value) return '暂无时间'
  const text = String(value).replace('T', ' ')
  return text.length > 16 ? text.slice(0, 16) : text
}

const sendMessage = async () => {
  const rawPrompt = inputText.value.trim()
  if (!rawPrompt || sending.value) return

  appendMessage({ text: rawPrompt, role: 'user' }, 'user')
  inputText.value = ''
  sending.value = true

  try {
    const response = await assistantApi.chat({
      conversationId: conversationId.value,
      rawPrompt,
      prompt: rawPrompt
    })

    if (response.code !== 200) {
      throw new Error(response.message || '发送失败')
    }

    conversationId.value = response.data?.conversationId || conversationId.value
    currentTitle.value = response.data?.conversation?.title || currentTitle.value
    appendMessage(response.data?.assistantMessage, 'assistant')
  } catch (error) {
    appendMessage({
      role: 'assistant',
      text: error?.message || '小助手暂时无法回复，请稍后再试。'
    }, 'assistant')
  } finally {
    sending.value = false
  }
}
</script>

<style scoped lang="scss">
.assistant-shell {
  min-height: 100vh;
  background:
    radial-gradient(circle at 18% 4%, rgba(111, 149, 128, 0.18), transparent 34%),
    linear-gradient(180deg, #f7f8f1 0%, #eef3e8 44%, #f8f7f0 100%);
  color: #20281f;
}

.chat-topbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: calc(var(--status-bar-height) + 18rpx) 24rpx 18rpx;
  background: rgba(247, 248, 241, 0.92);
  backdrop-filter: blur(18rpx);
  border-bottom: 1rpx solid rgba(76, 96, 72, 0.08);
}

.top-icon {
  width: 62rpx;
  height: 62rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.82);
  color: #263326;
  font-size: 52rpx;
  line-height: 1;
  box-shadow: 0 10rpx 28rpx rgba(65, 83, 62, 0.1);
}

.top-title-wrap {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.top-title {
  color: #1f2d1f;
  font-size: 32rpx;
  font-weight: 900;
}

.top-subtitle {
  margin-top: 4rpx;
  color: #6b7568;
  font-size: 22rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.top-actions {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.ghost-action,
.new-chat {
  padding: 14rpx 18rpx;
  border-radius: 999rpx;
  font-size: 23rpx;
  font-weight: 800;
}

.ghost-action {
  background: rgba(255, 255, 255, 0.82);
  color: #486646;
}

.new-chat {
  background: #243323;
  color: #ffffff;
}

.chat-scroll {
  height: calc(100vh - 220rpx);
  padding-top: calc(var(--status-bar-height) + 122rpx);
  box-sizing: border-box;
}

.welcome-panel {
  padding: 72rpx 32rpx 260rpx;
}

.bot-orb {
  width: 104rpx;
  height: 104rpx;
  border-radius: 32rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #273826, #6f9580);
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 900;
  box-shadow: 0 22rpx 48rpx rgba(72, 102, 70, 0.24);
}

.welcome-title {
  display: block;
  margin-top: 30rpx;
  color: #1f2d1f;
  font-size: 46rpx;
  font-weight: 950;
  letter-spacing: -1rpx;
}

.welcome-desc {
  display: block;
  max-width: 640rpx;
  margin-top: 18rpx;
  color: #64705f;
  font-size: 27rpx;
  line-height: 1.65;
}

.prompt-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
  margin-top: 40rpx;
}

.prompt-card {
  min-height: 142rpx;
  padding: 24rpx;
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 16rpx 36rpx rgba(65, 83, 62, 0.1);
  border: 1rpx solid rgba(111, 149, 128, 0.12);
}

.prompt-title {
  display: block;
  color: #263326;
  font-size: 27rpx;
  font-weight: 900;
}

.prompt-desc {
  display: block;
  margin-top: 12rpx;
  color: #697265;
  font-size: 23rpx;
  line-height: 1.45;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 30rpx;
  padding: 28rpx 28rpx 260rpx;
}

.message-row {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
}

.message-row-user {
  justify-content: flex-end;
}

.message-row-assistant {
  justify-content: flex-start;
}

.assistant-avatar {
  flex: 0 0 auto;
  width: 58rpx;
  height: 58rpx;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #243323, #73977e);
  color: #ffffff;
  font-size: 20rpx;
  font-weight: 900;
  box-shadow: 0 12rpx 26rpx rgba(72, 102, 70, 0.18);
}

.message-content {
  max-width: 82%;
}

.message-bubble {
  padding: 22rpx 26rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 14rpx 36rpx rgba(65, 83, 62, 0.1);
}

.message-row-user .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-row-user .message-bubble {
  color: #ffffff;
  background: linear-gradient(135deg, #263326, #486646);
  border-bottom-right-radius: 10rpx;
}

.message-row-assistant .message-bubble {
  border-bottom-left-radius: 10rpx;
}

.message-text {
  display: block;
  white-space: pre-wrap;
  font-size: 29rpx;
  line-height: 1.72;
}

.result-cards {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  margin-top: 16rpx;
}

.result-card {
  padding: 22rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.86);
  border: 1rpx solid rgba(111, 149, 128, 0.16);
  box-shadow: 0 12rpx 28rpx rgba(65, 83, 62, 0.08);
}

.result-head {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.result-title {
  flex: 1;
  color: #223021;
  font-size: 26rpx;
  font-weight: 900;
}

.result-tag {
  padding: 7rpx 12rpx;
  border-radius: 999rpx;
  background: #eef4e9;
  color: #486646;
  font-size: 20rpx;
  font-weight: 800;
}

.result-desc {
  display: block;
  margin-top: 12rpx;
  color: #657060;
  font-size: 23rpx;
  line-height: 1.55;
}

.metric-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 14rpx;
}

.metric-pills text {
  padding: 8rpx 12rpx;
  border-radius: 999rpx;
  background: #f2f6ee;
  color: #486646;
  font-size: 21rpx;
  font-weight: 700;
}

.typing-bubble {
  display: flex;
  gap: 8rpx;
  align-items: center;
  height: 56rpx;
  padding: 0 22rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 14rpx 36rpx rgba(65, 83, 62, 0.1);
}

.typing-dot {
  width: 10rpx;
  height: 10rpx;
  border-radius: 50%;
  background: #6f9580;
  animation: typingPulse 1s infinite ease-in-out;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.16s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.32s;
}

.composer-wrap {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 30;
  padding: 18rpx 22rpx calc(env(safe-area-inset-bottom) + 18rpx);
  background: linear-gradient(180deg, rgba(248, 247, 240, 0), rgba(248, 247, 240, 0.96) 24%, #f8f7f0 100%);
}

.composer {
  display: flex;
  align-items: flex-end;
  gap: 14rpx;
  padding: 14rpx;
  border-radius: 34rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 20rpx 54rpx rgba(65, 83, 62, 0.18);
  border: 1rpx solid rgba(111, 149, 128, 0.14);
}

.composer-input {
  flex: 1;
  min-height: 54rpx;
  max-height: 170rpx;
  padding: 17rpx 18rpx;
  color: #20281f;
  font-size: 28rpx;
  line-height: 1.5;
}

.send-button {
  width: 68rpx;
  height: 68rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  background: #d9e2d2;
  color: #ffffff;
  font-size: 38rpx;
  font-weight: 900;
  line-height: 1;
}

.send-button.active {
  background: #243323;
}

.send-button[disabled] {
  opacity: 0.65;
}

.composer-tip {
  display: block;
  margin-top: 10rpx;
  color: #858c80;
  text-align: center;
  font-size: 20rpx;
}

.history-mask {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: flex;
  align-items: flex-end;
  background: rgba(20, 28, 19, 0.42);
}

.history-sheet {
  width: 100%;
  max-height: 78vh;
  padding: 18rpx 24rpx calc(env(safe-area-inset-bottom) + 24rpx);
  border-radius: 36rpx 36rpx 0 0;
  background: #f8f7f0;
  box-shadow: 0 -24rpx 60rpx rgba(32, 40, 31, 0.22);
}

.sheet-handle {
  width: 78rpx;
  height: 8rpx;
  margin: 0 auto 22rpx;
  border-radius: 999rpx;
  background: #d4dccd;
}

.history-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18rpx;
}

.history-title {
  display: block;
  color: #1f2d1f;
  font-size: 34rpx;
  font-weight: 950;
}

.history-subtitle {
  display: block;
  margin-top: 6rpx;
  color: #7a8376;
  font-size: 23rpx;
}

.history-close {
  padding: 12rpx 18rpx;
  border-radius: 999rpx;
  background: #eef4e9;
  color: #486646;
  font-size: 23rpx;
  font-weight: 800;
}

.history-list {
  max-height: 58vh;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding: 22rpx;
  margin-bottom: 16rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.9);
  border: 1rpx solid rgba(111, 149, 128, 0.12);
}

.history-item.active {
  border-color: rgba(72, 102, 70, 0.45);
  background: #eef4e9;
}

.history-item-main {
  flex: 1;
  min-width: 0;
}

.history-item-title {
  display: block;
  color: #263326;
  font-size: 28rpx;
  font-weight: 900;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-item-summary {
  display: block;
  margin-top: 8rpx;
  color: #697265;
  font-size: 23rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-item-meta {
  display: flex;
  gap: 16rpx;
  margin-top: 10rpx;
  color: #92998d;
  font-size: 21rpx;
}

.history-delete {
  flex: 0 0 auto;
  padding: 12rpx 14rpx;
  border-radius: 999rpx;
  background: #fff1ed;
  color: #b15d43;
  font-size: 22rpx;
  font-weight: 800;
}

.history-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 320rpx;
  color: #717a6c;
  font-size: 26rpx;
}

.history-new-button {
  margin-top: 22rpx;
  padding: 0 32rpx;
  height: 72rpx;
  border-radius: 999rpx;
  background: #243323;
  color: #ffffff;
  font-size: 25rpx;
  font-weight: 900;
}

@keyframes typingPulse {
  0%, 80%, 100% {
    transform: translateY(0);
    opacity: 0.45;
  }
  40% {
    transform: translateY(-6rpx);
    opacity: 1;
  }
}
</style>
