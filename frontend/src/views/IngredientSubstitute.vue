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
          <h1>AI 食材小助手</h1>
          <p>每次提问都会把你的健康档案和饮食目标一起发送给 AI，再结合问题给出更贴合当前状态的建议。</p>
        </div>
      </div>
    </header>

    <section ref="chatContainerRef" class="chat-panel">
      <div class="message-row assistant">
        <div class="bubble bubble-assistant intro-bubble">
          <p>你好，我是你的 AI 食材小助手。</p>
          <p>你可以直接问我这些和食材替代相关的问题：</p>
          <ul>
            <li>减脂期鸡胸肉可以替换成什么？</li>
            <li>我乳糖不耐受，牛奶可以换成什么？</li>
            <li>我对海鲜过敏，海虾可以用什么代替？</li>
            <li>家里只有鸡蛋、豆腐和西兰花，晚餐怎么搭配更合适？</li>
          </ul>
        </div>
      </div>

      <div
        v-for="message in messages"
        :key="message.id"
        class="message-row"
        :class="message.role"
      >
        <div v-if="message.role === 'context'" class="context-strip">
          <div class="context-strip__title">已发送给 AI</div>
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
                  <strong>{{ item.name || '建议方案' }}</strong>
                  <span>{{ item.similarity || '参考建议' }}</span>
                </div>
                <p><b>营养差异：</b>{{ item.nutrition_difference || '暂无说明' }}</p>
                <p><b>使用建议：</b>{{ item.usage_suggestion || '暂无建议' }}</p>
              </article>
            </div>
          </template>
          <template v-else>
            <p
              v-for="(line, index) in toLines(message.text)"
              :key="`${message.id}-${index}`"
            >
              {{ line }}
            </p>
          </template>
        </div>
      </div>
    </section>

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
            placeholder="请输入你的食材替代问题..."
            @keydown.enter.exact.prevent="submitPrompt"
          />
        </el-form-item>
      </el-form>

      <div class="composer-actions">
        <el-button text @click="clearHistory">清空记录</el-button>
        <el-button type="success" circle class="send-btn" :loading="loading" @click="submitPrompt">
          <el-icon><Promotion /></el-icon>
        </el-button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { nextTick, onMounted, reactive, ref } from 'vue';
import { Promotion } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import recipeApi from '../api/recipe';
import healthInfoApi from '../api/healthInfo';
import dietGoalApi from '../api/dietGoal';
import { useUserStore } from '../stores/user';

const userStore = useUserStore();
const assistantFormRef = ref(null);
const chatContainerRef = ref(null);
const loading = ref(false);
const seed = ref(0);

const assistantForm = reactive({
  prompt: ''
});

const rules = {
  prompt: [{ required: true, message: '请输入你的问题', trigger: 'blur' }]
};

const quickPrompts = [
  { label: '鸡胸肉替代', prompt: '减脂期鸡胸肉可以替换成什么？', type: 'green' },
  { label: '牛奶替代', prompt: '我乳糖不耐受，牛奶可以换成什么？', type: 'blue' },
  { label: '海鲜过敏替代', prompt: '我对海鲜过敏，海虾可以用什么代替？', type: 'orange' },
  { label: '现有食材搭配', prompt: '家里只有鸡蛋、豆腐和西兰花，晚餐怎么搭配更合适？', type: 'purple' }
];

const activityLevelLabelMap = {
  sedentary: '久坐少动',
  lightly_active: '轻度活动',
  moderately_active: '中度活动',
  very_active: '高度活动',
  extra_active: '高强度活动'
};

const goalTypeLabelMap = {
  fat_loss: '减肥减脂',
  muscle_toning: '增肌塑形',
  weight_maintenance: '维持体重',
  healthy_weight_gain: '健康增重',
  blood_sugar_control: '控糖饮食',
  lipid_control: '控脂降脂',
  low_sodium: '控压低盐',
  pregnancy_nutrition: '孕妇营养',
  child_growth: '儿童成长',
  senior_wellness: '老年养生'
};

const messages = ref(
  Array.isArray(userStore.ingredientAssistantHistory) ? [...userStore.ingredientAssistantHistory] : []
);

const createId = () => `${Date.now()}-${++seed.value}`;

const persistMessages = () => {
  userStore.setIngredientAssistantHistory(messages.value);
};

const toLines = (text) =>
  String(text || '')
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean);

const formatValue = (value, suffix = '') => {
  if (value === null || value === undefined || value === '') {
    return '--';
  }
  return `${value}${suffix}`;
};

const buildContextSummary = () => {
  const healthInfo = userStore.healthInfo || {};
  const dietGoal = userStore.dietGoal || {};

  const healthSummary = [
    '健康档案：',
    `年龄${formatValue(healthInfo.age)}`,
    `性别${formatValue(healthInfo.gender)}`,
    `身高${formatValue(healthInfo.height, 'cm')}`,
    `体重${formatValue(healthInfo.weight, 'kg')}`,
    `BMI${formatValue(healthInfo.bmi)}`,
    `活动水平${activityLevelLabelMap[healthInfo.activityLevel] || healthInfo.activityLevel || '--'}`,
    `过敏信息${healthInfo.allergies || '--'}`,
    `慢病情况${healthInfo.chronicDiseases || '--'}`
  ].join('，') + '。';

  const goalSummary = [
    '饮食目标：',
    `目标类型${goalTypeLabelMap[dietGoal.goalType] || dietGoal.goalType || '--'}`,
    `目标热量${formatValue(dietGoal.targetCalories, 'kcal')}`,
    `蛋白质目标${formatValue(dietGoal.proteinTarget, 'g')}`,
    `碳水目标${formatValue(dietGoal.carbsTarget, 'g')}`,
    `脂肪目标${formatValue(dietGoal.fatTarget, 'g')}`,
    `饮水目标${formatValue(dietGoal.waterTarget, 'ml')}`
  ].join('，') + '。';

  return `${healthSummary}\n${goalSummary}`;
};

const buildPromptWithContext = (question) => {
  return [
    '请结合以下用户信息回答食材替代问题。',
    buildContextSummary(),
    `用户核心问题：${question}`,
    '要求：先直接回答这个问题，再说明为什么这些替代方案适合该用户当前身体状况和饮食目标。'
  ].join('\n');
};

const scrollToBottom = async () => {
  await nextTick();
  if (chatContainerRef.value) {
    chatContainerRef.value.scrollTop = chatContainerRef.value.scrollHeight;
  }
};

const pushUserMessage = (text) => {
  messages.value.push({
    id: createId(),
    role: 'user',
    text
  });
  persistMessages();
};

const pushContextMessage = (text) => {
  messages.value.push({
    id: createId(),
    role: 'context',
    text
  });
  persistMessages();
};

const pushLoadingMessage = () => {
  const id = createId();
  messages.value.push({
    id,
    role: 'assistant',
    text: '食材小助手正在结合你的健康档案和饮食目标分析，请稍候...'
  });
  persistMessages();
  return id;
};

const replaceMessage = (id, payload) => {
  const index = messages.value.findIndex((item) => item.id === id);
  if (index !== -1) {
    messages.value[index] = payload;
    persistMessages();
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

const sendPrompt = async (prompt) => {
  assistantForm.prompt = prompt;
  await submitPrompt();
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

  loading.value = true;

  try {
    await loadLatestContext();
    const promptWithContext = buildPromptWithContext(rawPrompt);

    pushUserMessage(rawPrompt);
    pushContextMessage(promptWithContext);
    assistantForm.prompt = '';
    const loadingId = pushLoadingMessage();
    await scrollToBottom();

    const response = await recipeApi.getSubstitutes({
      prompt: promptWithContext,
      rawPrompt,
      healthInfo: userStore.healthInfo,
      dietGoal: userStore.dietGoal
    });

    if (response.code === 200) {
      const payload = response.data || {};
      const cards =
        payload.mode === 'cards'
          ? (Array.isArray(payload.cards) ? payload.cards : [])
          : (Array.isArray(payload) ? payload : []);
      const text =
        payload.mode === 'text'
          ? (payload.text || '暂时没有生成建议，请换个问法试试。')
          : (cards.length ? '' : '暂时没有生成替代建议，请换个问法试试。');

      replaceMessage(loadingId, {
        id: createId(),
        role: 'assistant',
        cards,
        text
      });
    } else {
      replaceMessage(loadingId, {
        id: createId(),
        role: 'assistant',
        text: response.message || '获取建议失败'
      });
      ElMessage.error(response.message || '获取建议失败');
    }
  } catch (error) {
    console.error('食材小助手请求失败:', error);
    ElMessage.error('获取建议失败，请稍后重试');
  } finally {
    loading.value = false;
    await scrollToBottom();
  }
};

const clearHistory = async () => {
  messages.value = [];
  userStore.clearIngredientAssistantHistory();
  await scrollToBottom();
};

onMounted(async () => {
  try {
    await loadLatestContext();
  } catch (error) {
    console.error('加载食材小助手上下文失败:', error);
  }
  await scrollToBottom();
});
</script>

<style scoped>
.assistant-page {
  min-height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.assistant-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand {
  display: flex;
  align-items: center;
  gap: 16px;
}

.brand h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 800;
  color: #173a2e;
}

.brand p {
  margin: 6px 0 0;
  color: #5c6f63;
  font-size: 14px;
}

.brand-icon {
  position: relative;
  width: 42px;
  height: 42px;
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

.chat-panel {
  min-height: 520px;
  max-height: 70vh;
  overflow-y: auto;
  padding: 18px;
  border-radius: 24px;
  background: #ffffff;
  border: 1px solid #d9e7d8;
  box-shadow: 0 16px 30px rgba(74, 111, 76, 0.08);
}

.message-row {
  display: flex;
  margin-bottom: 16px;
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: 78%;
  padding: 16px 18px;
  border-radius: 22px;
  line-height: 1.8;
  font-size: 15px;
  white-space: pre-wrap;
}

.bubble p {
  margin: 0 0 8px;
}

.bubble p:last-child {
  margin-bottom: 0;
}

.bubble-user {
  background: #eef7ef;
  color: #173a2e;
  border-top-right-radius: 8px;
}

.bubble-assistant {
  background: #dff0ff;
  color: #173a2e;
  border-top-left-radius: 8px;
}

.intro-bubble ul {
  margin: 8px 0 0;
  padding-left: 18px;
}

.context-strip {
  width: 100%;
  padding: 14px 16px;
  border-radius: 16px;
  background: #f2faf3;
  border: 1px solid #cfe5d1;
}

.context-strip__title {
  font-size: 14px;
  font-weight: 700;
  color: #2f8f4e;
  margin-bottom: 6px;
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

.quick-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.quick-chip {
  border: none;
  border-radius: 999px;
  padding: 10px 18px;
  font-size: 15px;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.quick-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 16px rgba(74, 111, 76, 0.12);
}

.quick-chip.green {
  background: #e7f6e8;
  color: #3aa154;
}

.quick-chip.blue {
  background: #e7f0ff;
  color: #4f80e1;
}

.quick-chip.orange {
  background: #fff1df;
  color: #f08c34;
}

.quick-chip.purple {
  background: #efe8ff;
  color: #8a69d6;
}

.composer {
  display: flex;
  gap: 16px;
  align-items: flex-end;
  padding: 14px 18px;
  border-radius: 24px;
  background: #ffffff;
  border: 1px solid #d9e7d8;
  box-shadow: 0 12px 24px rgba(74, 111, 76, 0.08);
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
  padding: 10px 0;
  font-size: 16px;
  min-height: 52px !important;
}

.composer-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.send-btn {
  width: 50px;
  height: 50px;
}

.card-list {
  display: grid;
  gap: 14px;
}

.reply-card {
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid #b9d7ee;
}

.reply-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.reply-card-head strong {
  font-size: 20px;
  color: #173a2e;
}

.reply-card-head span {
  color: #5b7d8f;
  font-size: 14px;
}

.reply-card p {
  margin: 0 0 8px;
}

.reply-card p:last-child {
  margin-bottom: 0;
}

@media (max-width: 768px) {
  .chat-panel {
    min-height: 420px;
    padding: 14px;
  }

  .bubble {
    max-width: 92%;
  }

  .composer {
    flex-direction: column;
    align-items: stretch;
  }

  .composer-actions {
    justify-content: space-between;
  }
}
</style>
