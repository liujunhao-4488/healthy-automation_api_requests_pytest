<template>
  <div class="assistant-page">
    <header class="assistant-header">
      <div class="brand">
        <div class="brand-icon" aria-hidden="true">
          <span class="icon-stem"></span>
          <span class="icon-fork"></span>
          <span class="icon-knife"></span>
        </div>
        <div>
          <h1>AI 智能饮食助手</h1>
          <p>结合你的健康档案和饮食目标，饮食搭配、食材替代、营养估算、慢病饮食都能问。</p>
        </div>
      </div>
    </header>

    <div class="assistant-body">
      <aside class="conversation-panel">
        <div class="conversation-panel__header">
          <div>
            <p class="panel-label">AI 会话</p>
            <h2>历史对话</h2>
          </div>
          <el-button size="small" type="primary" @click="handleCreateConversation">新建会话</el-button>
        </div>

        <div class="conversation-list">
          <div
            v-for="conversation in conversationList"
            :key="conversation.id"
            class="conversation-tile"
            :class="{ active: conversation.id === currentConversationId }"
            @click="handleSelectConversation(conversation)"
          >
            <div class="conversation-tile__body">
              <strong>{{ conversation.title || '新会话' }}</strong>
              <p class="conversation-preview">{{ conversation.summary || '暂无摘要，目前可直接发送问题' }}</p>
              <p class="conversation-meta">
                {{ conversation.messageCount ? `消息 ${conversation.messageCount} 条 · ` : '' }}
                {{ formatConversationTime(conversation.lastMessageAt) }}
              </p>
            </div>
            <el-button
              type="text"
              size="small"
              class="conversation-delete"
              @click.stop="handleDeleteConversation(conversation.id)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
          <div v-if="conversationLoading" class="conversation-empty">正在加载会话...</div>
          <div v-if="!conversationLoading && !conversationList.length" class="conversation-empty">
            暂无历史会话，点击「新建会话」立即开始。
          </div>
        </div>
      </aside>

      <section class="chat-column">
        <div class="chat-column__header">
          <div>
            <h2>{{ currentConversationTitle }}</h2>
            <p class="panel-label">
              {{ conversationList.length }} 个会话 · 当前 {{ currentConversationId ? '已选中' : '无会话' }}
            </p>
          </div>
        </div>

        <section ref="chatContainerRef" class="chat-panel">
          <div
            v-for="message in messages"
            :key="message.id"
            class="message-row"
            :class="message.role"
          >
            <div v-if="message.role === 'context'" class="context-strip">
              <div class="context-strip__title">发送给 AI 的上下文</div>
              <pre class="context-strip__text">{{ message.text }}</pre>
            </div>

            <div
              v-else
              class="bubble"
              :class="message.role === 'user' ? 'bubble-user' : 'bubble-assistant'"
            >
              <template v-if="message.role === 'assistant' && message.cards?.length">
                <div class="card-list">
                  <article
                    v-for="(item, index) in message.cards"
                    :key="`${message.id}-${item.name || index}`"
                    class="reply-card"
                  >
                    <div class="reply-card-head">
                      <strong>{{ item.name || '推荐方案' }}</strong>
                      <span>{{ item.similarity || '相似度未知' }}</span>
                    </div>
                    <p><b>营养差异：</b>{{ item.nutrition_difference || '无说明' }}</p>
                    <p><b>使用建议：</b>{{ item.usage_suggestion || '暂无建议' }}</p>
                  </article>
                </div>
              </template>
              <template v-else>
                <p v-for="(line, index) in toLines(message.text)" :key="`${message.id}-${index}`">
                  {{ line }}
                </p>
              </template>
            </div>
          </div>

          <div v-if="loading && !hasFirstChunk" class="chat-loading">
            <span>AI 正在思考...</span>
          </div>
        </section>

        <div class="composer-shell">
        <div class="quick-bar">
          <button
            v-for="item in quickPrompts"
            :key="item.label"
            type="button"
            class="quick-chip"
            :class="item.type"
            @click="sendPrompt(item.prompt)"
          >
            {{ item.label }}
          </button>
        </div>

        <section class="composer">
          <el-form ref="assistantFormRef" :model="assistantForm" :rules="rules" class="composer-form">
            <el-form-item prop="prompt" class="composer-item">
              <el-input
                v-model="assistantForm.prompt"
                type="textarea"
                resize="none"
                :rows="1"
                placeholder="输入你的问题，例如：减脂期间晚餐怎么吃？"
                @keydown.enter.exact.prevent="submitPrompt"
              />
            </el-form-item>
          </el-form>
          <div class="composer-actions">
            <el-button text @click="clearHistory">删除会话</el-button>
            <el-button
              type="success"
              circle
              class="send-btn"
              :loading="loading"
              @click="submitPrompt"
            >
              <el-icon><Promotion /></el-icon>
            </el-button>
          </div>
        </section>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue';
import { Promotion, Delete } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import assistantApi from '../api/assistant';
import healthInfoApi from '../api/healthInfo';
import dietGoalApi from '../api/dietGoal';
import { useUserStore } from '../stores/user';
import { checkAssistantInput } from '../utils/assistantSafety';

const userStore = useUserStore();
const assistantFormRef = ref(null);
const chatContainerRef = ref(null);
const loading = ref(false);
const conversationLoading = ref(false);
// 流式回答开始后，"AI 正在思考..."就不该再挂着了（字都已经在往外冒了）。
// 用它区分"等第一段"和"正在流"这两种都处于 loading 的状态。
const hasFirstChunk = ref(false);

const assistantForm = reactive({
  prompt: ''
});

const rules = {
  prompt: [{ required: true, message: '请输入你的问题', trigger: 'blur' }]
};

// 四个快捷问题刻意和移动端 app/pages/assistant/chat.vue 保持一致 ——
// 之前这里四个全是"替代"，把整个页面框死在食材替换上，
// 而后端早就被放宽成泛健康助手了，两边对不上。
const quickPrompts = [
  { label: '控糖早餐', prompt: '控糖早餐怎么搭配更稳？', type: 'green' },
  { label: '低钠晚餐', prompt: '低钠晚餐推荐吃什么？', type: 'orange' },
  { label: '食材替换', prompt: '鸡胸肉可以替换成什么？', type: 'blue' },
  { label: '蛋白质不足', prompt: '今天蛋白质不够怎么办？', type: 'purple' }
];

const messages = ref([]);
const conversationList = ref([]);
const currentConversationId = ref(null);

const currentConversationTitle = computed(() => {
  const current = conversationList.value.find((item) => item.id === currentConversationId.value);
  return current?.title || 'AI 饮食助手会话';
});

const toLines = (text) =>
  String(text || '')
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean);

const createTempMessage = (role, text, extra = {}) => ({
  id: `temp-${role}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
  role,
  text,
  ...extra
});

const formatConversationTime = (value) => {
  if (!value) {
    return '暂无更新';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '时间未知';
  }
  return date.toLocaleString('zh-CN', { hour12: false });
};

const scrollToBottom = async () => {
  await nextTick();
  if (chatContainerRef.value) {
    chatContainerRef.value.scrollTop = chatContainerRef.value.scrollHeight;
  }
};

const loadLatestContext = async () => {
  const [healthResponse, goalResponse] = await Promise.allSettled([
    healthInfoApi.getHealthInfo(),
    dietGoalApi.getDietGoal()
  ]);

  if (healthResponse.status === 'fulfilled' && healthResponse.value?.code === 200 && healthResponse.value?.data) {
    userStore.setHealthInfo(healthResponse.value.data);
    userStore.setHealthAnalysis(healthResponse.value.analysis || null);
  }

  if (goalResponse.status === 'fulfilled' && goalResponse.value?.code === 200 && goalResponse.value?.data) {
    userStore.setDietGoal(goalResponse.value.data);
  }
};

const refreshMessages = async (conversationIdParam = currentConversationId.value) => {
  if (!conversationIdParam) {
    messages.value = [];
    return;
  }
  try {
    const response = await assistantApi.getMessages(conversationIdParam);
    if (response.code === 200) {
      messages.value = Array.isArray(response.data) ? response.data : [];
      await scrollToBottom();
    } else {
      ElMessage.error(response.message || '获取消息失败');
    }
  } catch (error) {
    console.error('获取会话消息失败:', error);
    ElMessage.error('获取会话消息失败，请稍后重试');
  }
};

const loadConversations = async () => {
  conversationLoading.value = true;
  try {
    const response = await assistantApi.getConversations();
    if (response.code === 200) {
      const list = Array.isArray(response.data) ? response.data : [];
      conversationList.value = list;
      const hasCurrent = list.some((item) => item.id === currentConversationId.value);
      if (!hasCurrent) {
        currentConversationId.value = list[0]?.id || null;
      }
    } else {
      ElMessage.error(response.message || '获取会话列表失败');
    }
  } catch (error) {
    console.error('加载会话失败:', error);
    ElMessage.error('加载会话失败，请稍后重试');
  } finally {
    conversationLoading.value = false;
  }
};

const handleSelectConversation = async (conversation) => {
  if (!conversation?.id) {
    return;
  }
  if (conversation.id === currentConversationId.value) {
    return;
  }
  currentConversationId.value = conversation.id;
  await refreshMessages(conversation.id);
};

const handleCreateConversation = async () => {
  try {
    const response = await assistantApi.createConversation({ title: 'AI 饮食助手会话' });
    if (response.code === 200 && response.data) {
      currentConversationId.value = response.data.id;
      await loadConversations();
      await refreshMessages(currentConversationId.value);
    } else {
      ElMessage.error(response.message || '创建会话失败');
    }
  } catch (error) {
    console.error('创建会话失败:', error);
    ElMessage.error('创建会话失败，请稍后重试');
  }
};

const handleDeleteConversation = async (conversationId) => {
  if (!conversationId) {
    return;
  }
  const confirmed = window.confirm('确认删除该会话及所有消息吗？');
  if (!confirmed) {
    return;
  }
  try {
    const response = await assistantApi.deleteConversation(conversationId);
    if (response.code === 200) {
      ElMessage.success('会话已删除');
      if (currentConversationId.value === conversationId) {
        currentConversationId.value = null;
      }
      await loadConversations();
      if (currentConversationId.value) {
        await refreshMessages();
      } else {
        messages.value = [];
      }
    } else {
      ElMessage.error(response.message || '删除会话失败');
    }
  } catch (error) {
    console.error('删除会话失败:', error);
    ElMessage.error('删除会话失败，请稍后重试');
  }
};

const submitPrompt = async () => {
  if (!assistantFormRef.value || loading.value) {
    return;
  }

  const valid = await assistantFormRef.value.validate().catch(() => false);
  if (!valid) {
    return;
  }

  const rawPrompt = assistantForm.prompt.trim();
  if (!rawPrompt) {
    return;
  }

  // 前端本地预检（体验层）：只拦「超长 + 明摆着的脏话」，直接回固定提示、不发请求。
  // 高危医疗 / 无关领域 已交给后端判 —— 前端判会漂移（见 utils/assistantSafety.js 头注释）。
  // 它可被绕过，不是安全边界。
  const blocked = checkAssistantInput(rawPrompt);
  if (blocked) {
    assistantForm.prompt = '';
    messages.value = [
      ...messages.value,
      createTempMessage('user', rawPrompt),
      createTempMessage('assistant', blocked.reply),
    ];
    await scrollToBottom();
    return;
  }

  loading.value = true;
  hasFirstChunk.value = false;
  try {
    await loadLatestContext();

    if (!currentConversationId.value) {
      await handleCreateConversation();
    }
    if (!currentConversationId.value) {
      throw new Error('无法创建会话，暂时无法发送消息');
    }

    assistantForm.prompt = '';

    // 先摆两个临时气泡：用户那条立刻可见；助手那条**先空着**，等流一段段往里填。
    // 流跑完后助手那条会被后端落库的最终消息覆盖（含真正的 id / intent / source / blocked），
    // 所以这里不需要再调 refreshMessages 去整个重拉一遍。
    const userTemp = createTempMessage('user', rawPrompt);
    const assistantTemp = createTempMessage('assistant', '');
    messages.value = [...messages.value, userTemp, assistantTemp];
    await scrollToBottom();

    const findAssistantTemp = () => messages.value.find((item) => item.id === assistantTemp.id);

    // 只发 rawPrompt，不再拼一段 prompt 一起发。
    //
    // 为什么删掉？因为后端会把它整块当成"用户的问题"：
    //   AssistantChatServiceImpl:128  request.put("prompt", promptWithContext)
    //   RecipeServiceImpl:727         extractIngredientQuestion 优先返回 prompt
    // 于是拼进去的 "请优先给出替代食材…" 成了模型的指令，问「1+1=多少」也照套；
    // 而拼进去的健康档案，后端本来就会按 userId 再查一遍、作为 system 消息单独发 ——
    // 同一份档案发两遍，还可能互相矛盾。
    //
    // 副作用（想要的）：不再产生 role=context 的消息，聊天里那块
    // "发送给 AI 的上下文" 也就不再出现了。旧会话里已有的 context 消息仍会照旧显示。
    await assistantApi.chatStream(
      {
        conversationId: currentConversationId.value,
        rawPrompt,
        healthInfo: userStore.healthInfo,
        dietGoal: userStore.dietGoal
      },
      {
        // 后端建好会话、存好用户消息后**最先**推这个 ——
        // 新建会话时尤其关键：不用等模型答完，客户端就已经知道这轮属于哪个会话了。
        start: (data) => {
          if (data?.conversationId) {
            currentConversationId.value = data.conversationId;
          }
        },
        // 一段一段往里追加。这里**不能**每段都刷新消息列表 ——
        // 那样会把还在生成的临时气泡冲掉，看起来就像"闪一下又没了"。
        delta: (data) => {
          const target = findAssistantTemp();
          if (target && typeof data?.text === 'string') {
            target.text = `${target.text || ''}${data.text}`;
            if (!hasFirstChunk.value) {
              hasFirstChunk.value = true;
            }
            scrollToBottom();
          }
        },
        // 流结束：用后端落库的那条**权威消息**覆盖临时气泡，再刷新会话列表
        // （标题 / 摘要 / 消息数只有后端算得出来）。
        done: async (data) => {
          const target = findAssistantTemp();
          const finalMessage = data?.assistantMessage;
          if (target && finalMessage) {
            Object.assign(target, finalMessage);
          }
          await loadConversations();
          await scrollToBottom();
        },
        // 后端在流程里抛异常时会推这个事件；抛出去让下面统一的 catch 接住
        error: (data) => {
          throw new Error(data?.message || '生成回复失败');
        }
      }
    );
  } catch (error) {
    console.error('发送请求失败:', error);
    // 失败时补一条说明，别让用户对着一个空气泡猜
    const fallback = createTempMessage('assistant', error?.message || '发送请求失败，请稍后重试');
    messages.value = [...messages.value, fallback];
    await scrollToBottom();
    ElMessage.error(error?.message || '发送请求失败，请稍后重试');
  } finally {
    loading.value = false;
    hasFirstChunk.value = false;
  }
};

const sendPrompt = async (prompt) => {
  assistantForm.prompt = prompt;
  await submitPrompt();
};

const clearHistory = async () => {
  await handleDeleteConversation(currentConversationId.value);
};

onMounted(async () => {
  try {
    await loadLatestContext();
  } catch (error) {
    console.error('加载上下文失败:', error);
  }
  await loadConversations();
  if (currentConversationId.value) {
    await refreshMessages();
  }
});
</script>

<style scoped>
.assistant-page {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 0 6px 0;
  max-width: 100%;
  margin: -10px auto 0;
  box-sizing: border-box;
  overflow: hidden;
}

.assistant-body {
  display: grid;
  grid-template-columns: minmax(168px, 184px) minmax(0, 1fr);
  gap: 10px;
  align-items: start;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.assistant-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: #ffffff;
  border-radius: 14px;
  border: 1px solid #edf2ee;
  box-shadow: none;
  flex-shrink: 0;
  position: relative;
  z-index: 10;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #173a2e;
  letter-spacing: 0;
}

.brand p {
  margin: 2px 0 0;
  color: #5c6f63;
  font-size: 12px;
  line-height: 1.4;
}

.brand-icon {
  position: relative;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
}

.icon-stem,
.icon-fork,
.icon-knife {
  position: absolute;
  display: block;
  background: linear-gradient(180deg, #5fc36f, #2f9969);
  border-radius: 999px;
}

.icon-fork {
  left: 2px;
  top: 3px;
  width: 7px;
  height: 36px;
}

.icon-fork::before,
.icon-fork::after {
  content: '';
  position: absolute;
  top: -1px;
  width: 2px;
  height: 12px;
  background: inherit;
  border-radius: 999px;
}

.icon-fork::before {
  left: 1px;
}

.icon-fork::after {
  right: 1px;
}

.icon-knife {
  right: 2px;
  top: 3px;
  width: 7px;
  height: 36px;
}

.icon-stem {
  left: 18px;
  bottom: 2px;
  width: 6px;
  height: 34px;
}

.conversation-panel {
  background: #ffffff;
  border: 1px solid #edf2ee;
  border-radius: 16px;
  padding: 10px;
  position: sticky;
  top: 0;
  align-self: start;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-shadow: none;
  min-height: 0;
  height: 100%;
  max-height: none;
  overflow: hidden;
  transition: all 0.2s ease;
}

.conversation-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 0;
  flex-shrink: 0;
}

.panel-label {
  margin: 0;
  font-size: 10px;
  color: #6b7c70;
  font-weight: 500;
  letter-spacing: 0.2px;
}

.conversation-panel__header h2,
.chat-column__header h2 {
  margin: 0;
  font-size: 15px;
  line-height: 1.3;
  color: #173a2e;
}

.conversation-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding-right: 2px;
  overscroll-behavior: contain;
}

.conversation-list::-webkit-scrollbar {
  width: 6px;
}

.conversation-list::-webkit-scrollbar-thumb {
  background: rgba(92, 111, 99, 0.28);
  border-radius: 999px;
}

.conversation-tile {
  border: 1px solid #f1f4f1;
  padding: 8px 10px;
  border-radius: 12px;
  background: #fafcfb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  cursor: pointer;
  transition: all 0.18s ease;
}

.conversation-tile:hover {
  border-color: #d7e5da;
  background: #f5faf6;
  transform: none;
}

.conversation-tile.active {
  border-color: #c7dccd;
  background: #f3f8f4;
  box-shadow: none;
}

.conversation-tile__body strong {
  display: block;
  font-size: 12px;
  line-height: 1.35;
  color: #173a2e;
}

.conversation-preview {
  margin: 3px 0 0;
  font-size: 11px;
  color: #42594a;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.conversation-meta {
  margin: 3px 0 0;
  font-size: 10px;
  color: #8b9b8f;
}

.conversation-delete {
  min-width: 28px;
  padding: 0;
  color: #b34949;
  transition: all 0.2s;
}

.conversation-delete:hover {
  color: #d85a5a;
  transform: scale(1.08);
}

.conversation-empty {
  margin-top: 40px;
  color: #7a8c81;
  font-size: 14px;
  text-align: center;
}

.chat-column {
  display: flex;
  flex-direction: column;
  gap: 0;
  min-height: 0;
  overflow: hidden;
  height: 100%;
  background: #ffffff;
  border: 1px solid #edf2ee;
  border-radius: 16px;
  box-shadow: none;
}

.chat-column__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding: 8px 16px 7px;
  background: transparent;
  border-bottom: 1px solid #edf2ee;
  border-radius: 16px 16px 0 0;
  box-shadow: none;
  flex-shrink: 0;
}

.chat-panel {
  flex: 1;
  overflow-y: auto;
  padding: 18px 28px 20px;
  border-radius: 0 0 16px 16px;
  background: #ffffff;
  border: none;
  box-shadow: none;
  min-height: 0;
  transition: all 0.2s ease;
}

.message-row {
  display: flex;
  margin-bottom: 20px;
  animation: messageFadeIn 0.25s ease forwards;
}

@keyframes messageFadeIn {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: min(1020px, 94%);
  width: fit-content;
  padding: 16px 18px;
  border-radius: 18px;
  line-height: 1.75;
  font-size: 15px;
  white-space: pre-wrap;
  box-shadow: none;
  border: 1px solid transparent;
}

.bubble p {
  margin: 0 0 8px;
}

.bubble p:last-child {
  margin-bottom: 0;
}

.bubble-user {
  background: #f1f7f2;
  color: #173a2e;
  border-top-right-radius: 8px;
  border-color: #ddebe0;
}

.bubble-assistant {
  background: #f7f9fb;
  color: #173a2e;
  border-top-left-radius: 8px;
  border-color: #e5ebf1;
}

.context-strip {
  width: 100%;
  padding: 16px 18px;
  border-radius: 16px;
  background: #f6faf7;
  border: 1px solid #ddebe0;
  margin-bottom: 16px;
}

.context-strip__title {
  font-size: 14px;
  font-weight: 700;
  color: #2f8f4e;
  margin-bottom: 8px;
}

.context-strip__text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  line-height: 1.7;
  color: #42594a;
  font-family: inherit;
}

.composer-shell {
  position: sticky;
  bottom: 0;
  z-index: 8;
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex-shrink: 0;
  padding: 12px 24px 12px;
  background: #ffffff;
  border-top: 1px solid #edf2ee;
}

.quick-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  width: min(100%, 1080px);
  margin: 0 auto;
  padding: 0;
  justify-content: flex-start;
}

.quick-chip {
  border: 1px solid #e5ece7;
  border-radius: 999px;
  padding: 10px 16px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.18s ease;
  box-shadow: none;
}

.quick-chip:hover {
  transform: none;
  box-shadow: none;
}

.quick-chip.green {
  background: #f2f8f3;
  color: #3a7f52;
}

.quick-chip.blue {
  background: #f2f6fb;
  color: #4d7098;
}

.quick-chip.orange {
  background: #fcf6ee;
  color: #a86c28;
}

.quick-chip.purple {
  background: #f6f2fb;
  color: #7560a8;
}

.chat-loading {
  margin-top: 10px;
  padding: 12px 20px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.04);
  text-align: center;
  font-size: 14px;
  color: #42594a;
  width: fit-content;
  margin-left: auto;
  margin-right: auto;
}

.composer {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  padding: 10px 16px;
  width: min(100%, 1080px);
  margin: 0 auto;
  border-radius: 18px;
  background: #ffffff;
  border: 1px solid #e4ebe6;
  box-shadow: 0 8px 24px rgba(23, 58, 46, 0.06);
  backdrop-filter: blur(14px);
}

.composer-form {
  flex: 1;
}

.composer-item {
  margin-bottom: 0;
}

:deep(.composer-item .el-textarea__inner) {
  border: none;
  box-shadow: none;
  padding: 8px 4px;
  font-size: 15px;
  min-height: 44px !important;
  background: transparent;
}

.composer-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.send-btn {
  width: 54px;
  height: 54px;
  box-shadow: 0 4px 12px rgba(95, 195, 111, 0.2);
  transition: all 0.2s ease;
}

.send-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(95, 195, 111, 0.28);
}

.card-list {
  display: grid;
  gap: 16px;
}

.reply-card {
  padding: 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid #b9d7ee;
  box-shadow: 0 3px 10px rgba(120, 160, 190, 0.08);
  transition: all 0.2s ease;
}

.reply-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(120, 160, 190, 0.12);
}

.reply-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.reply-card-head strong {
  font-size: 18px;
  color: #173a2e;
}

.reply-card-head span {
  color: #5b7d8f;
  font-size: 14px;
  font-weight: 500;
}

.reply-card p {
  margin: 0 0 10px;
  line-height: 1.7;
}

.reply-card p:last-child {
  margin-bottom: 0;
}

@media (max-width: 1280px) {
  .assistant-body {
    grid-template-columns: 172px minmax(0, 1fr);
    gap: 8px;
  }

  .chat-panel {
    padding: 18px 24px 22px;
  }

  .quick-bar,
  .composer {
    width: min(100%, 960px);
  }
}

@media (max-width: 1024px) {
  .assistant-body {
    grid-template-columns: 1fr;
  }

  .conversation-panel {
    position: relative;
    top: 0;
    height: 250px;
    max-height: 320px;
  }

  .chat-column {
    height: auto;
  }

  .chat-panel {
    min-height: 320px;
    padding: 20px 18px 28px;
  }

  .composer-shell {
    padding: 16px;
  }
}

@media (max-width: 768px) {
  .assistant-page {
    height: 100%;
    min-height: 0;
    padding: 6px 8px 8px;
    gap: 8px;
    margin-top: -6px;
  }

  .assistant-header {
    padding: 8px 12px;
  }

  .brand h1 {
    font-size: 16px;
  }

  .brand p {
    font-size: 11px;
  }

  .chat-panel {
    padding: 14px 10px 20px;
  }

  .bubble {
    max-width: 96%;
  }

  .composer-shell {
    padding: 12px 8px 8px;
  }

  .quick-bar {
    width: 100%;
    justify-content: flex-start;
    flex-wrap: nowrap;
    overflow-x: auto;
    padding-bottom: 4px;
  }

  .composer {
    flex-direction: column;
    align-items: stretch;
    gap: 14px;
    width: 100%;
  }

  .composer-actions {
    justify-content: space-between;
  }
}

</style>
