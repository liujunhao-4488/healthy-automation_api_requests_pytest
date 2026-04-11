<template>
  <div class="goal-overview">
    <section class="hero-card">
      <div>
        <p class="eyebrow">Diet Goal</p>
        <h2>饮食目标档案</h2>
        <p class="hero-copy">
          查看当前目标类型、当前体重与目标体重、营养分配和提醒设置。健康信息中的体重变化后，可以在这里一键更新目标数据。
        </p>
      </div>
      <div class="hero-actions">
        <el-button class="edit-button" type="primary" @click="goToEdit">修改目标</el-button>
        <el-badge v-if="showWeightUpdateHint" value="体重已更新" class="update-badge">
          <el-button class="update-button" @click="refreshGoalByWeight" :loading="refreshingGoal">
            更新数据
          </el-button>
        </el-badge>
        <el-button v-else class="update-button" @click="refreshGoalByWeight" :loading="refreshingGoal">
          更新数据
        </el-button>
      </div>
    </section>

    <el-row :gutter="20" class="summary-grid">
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="summary-card accent-sand">
          <span>当前目标</span>
          <strong>{{ goalTypeLabel }}</strong>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="summary-card accent-green">
          <span>当前体重</span>
          <strong>{{ displayValue(currentWeight, 'kg') }}</strong>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="summary-card accent-cream">
          <span>目标体重</span>
          <strong>{{ displayValue(dietGoal.targetWeight, 'kg') }}</strong>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="summary-card accent-mint">
          <span>每日热量</span>
          <strong>{{ displayValue(dietGoal.targetCalories, 'kcal') }}</strong>
        </div>
      </el-col>
    </el-row>

    <el-alert
      v-if="showWeightUpdateHint"
      type="warning"
      :closable="false"
      class="hint-alert"
      title="检测到健康信息中的体重已更新"
      description="点击“更新数据”后，系统会按最新体重重新计算热量、三大营养素和饮水目标，并直接保存到当前饮食目标。"
    />

    <div class="content-grid">
      <el-card class="goal-card" shadow="never">
        <template #header>
          <div class="section-head">
            <span>目标概况</span>
          </div>
        </template>
        <div class="info-list">
          <div class="info-item">
            <label>目标类型</label>
            <span>{{ goalTypeLabel }}</span>
          </div>
          <div class="info-item">
            <label>当前体重</label>
            <span>{{ displayValue(currentWeight, 'kg') }}</span>
          </div>
          <div class="info-item">
            <label>目标体重</label>
            <span>{{ displayValue(dietGoal.targetWeight, 'kg') }}</span>
          </div>
          <div class="info-item">
            <label>体重差值</label>
            <span>{{ weightGapLabel }}</span>
          </div>
          <div class="info-item">
            <label>开始日期</label>
            <span>{{ displayValue(dietGoal.startDate) }}</span>
          </div>
          <div class="info-item">
            <label>结束日期</label>
            <span>{{ displayValue(dietGoal.endDate) }}</span>
          </div>
          <div class="info-item">
            <label>提醒状态</label>
            <span>{{ dietGoal.reminderEnabled === 1 ? '已开启' : '未开启' }}</span>
          </div>
          <div class="info-item">
            <label>提醒时间</label>
            <span>{{ displayValue(dietGoal.reminderTime) }}</span>
          </div>
        </div>
      </el-card>

      <el-card class="goal-card" shadow="never">
        <template #header>
          <div class="section-head">
            <span>营养分配</span>
          </div>
        </template>
        <div class="metric-strip">
          <div class="metric-box">
            <span>每日热量</span>
            <strong>{{ displayValue(dietGoal.targetCalories, 'kcal') }}</strong>
          </div>
          <div class="metric-box">
            <span>每日饮水</span>
            <strong>{{ displayValue(dietGoal.waterTarget, 'ml') }}</strong>
          </div>
        </div>
        <div class="macro-grid">
          <div class="macro-card protein">
            <span>蛋白质</span>
            <strong>{{ displayValue(dietGoal.proteinTarget, 'g') }}</strong>
            <small>{{ displayValue(dietGoal.proteinRatio, '%') }}</small>
          </div>
          <div class="macro-card carbs">
            <span>碳水</span>
            <strong>{{ displayValue(dietGoal.carbsTarget, 'g') }}</strong>
            <small>{{ displayValue(dietGoal.carbsRatio, '%') }}</small>
          </div>
          <div class="macro-card fat">
            <span>脂肪</span>
            <strong>{{ displayValue(dietGoal.fatTarget, 'g') }}</strong>
            <small>{{ displayValue(dietGoal.fatRatio, '%') }}</small>
          </div>
        </div>
      </el-card>
    </div>

    <el-card class="note-card" shadow="never">
      <div class="note-copy">
        <h3>目标建议</h3>
        <p>{{ goalDescription }}</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { CollectionTag, DataAnalysis, EditPen, Memo, Reading, RefreshRight, Timer, User } from '@element-plus/icons-vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { useUserStore } from '../stores/user';
import dietGoalApi from '../api/dietGoal';
import { computeDietGoalRecommendation, formatGoalDate, formatGoalTime } from '../utils/dietGoalRecommendation';

const router = useRouter();
const userStore = useUserStore();
const refreshingGoal = ref(false);

const goalOptions = {
  fat_loss: { label: '减肥减脂', description: '控制总热量并提高蛋白质占比，适合希望降低体脂的人群。' },
  muscle_toning: { label: '增肌塑形', description: '提升优质蛋白和训练支持，更适合力量训练与塑形恢复。' },
  weight_maintenance: { label: '维持体重', description: '保持热量收支稳定，让日常饮食结构更均衡可持续。' },
  healthy_weight_gain: { label: '健康增重', description: '在保证营养质量的前提下增加能量摄入，帮助稳步增重。' },
  blood_sugar_control: { label: '控糖饮食', description: '重点关注碳水来源和血糖波动，适合控糖需求。' },
  lipid_control: { label: '控脂降脂', description: '更关注脂肪质量与总量，帮助优化血脂相关饮食结构。' },
  low_sodium: { label: '控压低盐', description: '减少钠盐摄入，增加清淡搭配，更适合血压管理。' },
  pregnancy_nutrition: { label: '孕妇营养', description: '强化蛋白质、铁和钙的摄入，满足孕期的营养支持。' },
  child_growth: { label: '儿童成长', description: '兼顾成长发育所需能量与营养密度，帮助儿童健康成长。' },
  senior_wellness: { label: '老年养生', description: '更重视易消化、足蛋白和清淡饮食，适合老年日常养护。' }
};

const dietGoal = computed(() => userStore.dietGoal || {});
const currentWeight = computed(() => userStore.healthInfo?.weight ?? null);

const goalTypeLabel = computed(() => goalOptions[dietGoal.value.goalType]?.label || '--');

const goalDescription = computed(() => {
  return goalOptions[dietGoal.value.goalType]?.description || '先设置你的饮食目标，系统才能生成更合适的营养建议。';
});

const showWeightUpdateHint = computed(() => {
  const current = Number(currentWeight.value);
  const appliedWeight = Number(userStore.dietGoalMeta?.appliedWeight);

  if (!Number.isFinite(current) || !dietGoal.value.goalType) {
    return false;
  }

  if (Number.isFinite(appliedWeight)) {
    return Math.abs(current - appliedWeight) > 0.0001;
  }

  const healthUpdatedAt = userStore.healthInfo?.updateTime ? new Date(userStore.healthInfo.updateTime).getTime() : 0;
  const goalUpdatedAt = dietGoal.value.updateTime ? new Date(dietGoal.value.updateTime).getTime() : 0;
  return healthUpdatedAt > goalUpdatedAt;
});

const weightGapLabel = computed(() => {
  const current = Number(currentWeight.value);
  const target = Number(dietGoal.value.targetWeight);

  if (!Number.isFinite(current) || !Number.isFinite(target)) {
    return '--';
  }

  const gap = Number((target - current).toFixed(1));
  const prefix = gap > 0 ? '+' : '';
  return `${prefix}${gap} kg`;
});

const displayValue = (value, unit = '') => {
  if (value === null || value === undefined || value === '') {
    return '--';
  }

  const normalizedValue =
    typeof value === 'number'
      ? Number.isInteger(value)
        ? value
        : value.toFixed(1)
      : value;

  return `${normalizedValue}${unit ? ` ${unit}` : ''}`;
};

const persistGoalMeta = () => {
  if (Number.isFinite(Number(currentWeight.value))) {
    userStore.setDietGoalMeta({
      appliedWeight: Number(currentWeight.value),
      appliedAt: new Date().toISOString()
    });
  }
};

const goToEdit = () => {
  router.push('/dashboard/diet-goal/edit');
};

const loadDietGoal = async () => {
  try {
    const response = await dietGoalApi.getDietGoal();
    if (response.code === 200 && response.data) {
      userStore.setDietGoal(response.data);
      return;
    }
  } catch (error) {
    console.error('获取饮食目标失败:', error);
  }
};

const refreshGoalByWeight = async () => {
  const healthInfo = userStore.healthInfo;
  if (!healthInfo || !dietGoal.value.goalType) {
    ElMessage.warning('请先完善健康信息和饮食目标');
    return;
  }

  const recommendation = computeDietGoalRecommendation({
    healthInfo,
    goalForm: dietGoal.value
  });

  if (!recommendation) {
    ElMessage.warning('暂时无法根据当前信息生成目标推荐');
    return;
  }

  const payload = {
    ...dietGoal.value,
    ...recommendation.recommendedGoal,
    startDate: formatGoalDate(dietGoal.value.startDate),
    endDate: formatGoalDate(dietGoal.value.endDate),
    reminderTime: formatGoalTime(dietGoal.value.reminderTime)
  };

  refreshingGoal.value = true;
  try {
    const response = await dietGoalApi.updateDietGoal(payload);
    if (response.code === 200) {
      userStore.setDietGoal(response.data || payload);
      persistGoalMeta();
      ElMessage.success('饮食目标已按最新体重更新');
      return;
    }

    ElMessage.error(response.message || '更新失败');
  } catch (error) {
    ElMessage.error(error.message || '更新失败，请检查网络连接');
  } finally {
    refreshingGoal.value = false;
  }
};

onMounted(async () => {
  await loadDietGoal();
});
</script>

<style scoped>
.goal-overview {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.hero-card {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 20px;
  padding: 28px 30px;
  border-radius: 24px;
  background:
    radial-gradient(circle at top left, rgba(196, 226, 210, 0.35), transparent 42%),
    linear-gradient(135deg, #f9fffb 0%, #edf7ef 100%);
  border: 1px solid #dcecdf;
}

.eyebrow {
  margin: 0 0 10px;
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #6f8f72;
}

.hero-card h2 {
  margin: 0;
  font-family: 'Noto Serif SC', serif;
  font-size: 30px;
  color: #334235;
}

.hero-copy {
  max-width: 560px;
  margin: 12px 0 0;
  color: #68796b;
  line-height: 1.7;
}

.hero-actions {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  flex-wrap: wrap;
  margin-right: 10px;
}

.update-badge {
  margin-left: 4px;
}

.update-badge :deep(.el-badge__content) {
  right: 2px;
  top: -4px;
  transform: scale(0.78);
  transform-origin: top right;
  padding: 0 8px;
  height: 22px;
  line-height: 22px;
  font-size: 12px;
}

.update-button {
  min-width: 124px;
  height: 44px;
  border-color: #cfe0d2;
  color: #46614a;
  background: #f4fbf5;
}

.edit-button {
  min-width: 124px;
  height: 44px;
  border: none;
  background: linear-gradient(135deg, #6f8f72 0%, #8b7355 100%);
}

.summary-grid {
  margin: 0;
}

.summary-card {
  min-height: 126px;
  padding: 22px;
  border-radius: 22px;
  color: #334235;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 12px 28px rgba(59, 79, 63, 0.06);
}

.summary-meta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.summary-card span {
  color: #738075;
}

.summary-icon {
  font-size: 18px;
}

.summary-card strong {
  font-size: 28px;
  font-weight: 600;
}

.accent-sand {
  background: linear-gradient(180deg, #fffaf4 0%, #f1e5d7 100%);
}

.accent-green {
  background: linear-gradient(180deg, #f4fbf5 0%, #dcefdc 100%);
}

.accent-cream {
  background: linear-gradient(180deg, #fcfbf6 0%, #ece7d8 100%);
}

.accent-mint {
  background: linear-gradient(180deg, #f3fcf7 0%, #d8eee3 100%);
}

.hint-alert {
  border-radius: 18px;
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 22px;
}

.goal-card,
.note-card {
  border: 1px solid #e4ecdf;
  border-radius: 22px;
}

.section-head {
  font-weight: 600;
  color: #334235;
}

.section-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.section-title .el-icon {
  color: #6f8f72;
}

.info-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.info-item {
  padding: 16px 18px;
  border-radius: 16px;
  background: #f7faf6;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item label {
  font-size: 13px;
  color: #829084;
}

.info-item span {
  color: #334235;
  line-height: 1.6;
}

.metric-strip {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 14px;
}

.metric-box {
  padding: 16px 18px;
  border-radius: 16px;
  background: #f7faf6;
}

.metric-box span {
  display: block;
  margin-bottom: 8px;
  color: #718073;
}

.metric-box strong {
  color: #334235;
  font-size: 24px;
}

.macro-grid {
  display: grid;
  gap: 14px;
}

.macro-card {
  padding: 18px 20px;
  border-radius: 18px;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.macro-card span {
  color: #617165;
}

.macro-card strong {
  font-size: 24px;
  color: #334235;
}

.macro-card small {
  color: #7f8b81;
}

.protein {
  background: #f2f8ff;
}

.carbs {
  background: #fff8ee;
}

.fat {
  background: #f7f3ff;
}

.note-card {
  background: linear-gradient(135deg, #ffffff 0%, #f6fbf7 100%);
}

.note-copy h3 {
  margin: 0 0 10px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-family: 'Noto Serif SC', serif;
  color: #334235;
}

.note-copy p {
  margin: 0;
  color: #69766b;
  line-height: 1.8;
}

@media (max-width: 900px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .hero-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-actions {
    align-items: flex-start;
  }

  .info-list,
  .metric-strip {
    grid-template-columns: 1fr;
  }
}
</style>
